from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import public_error_detail
from app.domain.models import CustomerMessage
from app.integrations.gmail.mock import MockGmail
from app.services.factory import build_shopify
from app.services.workflow import CaseWorkflowService

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class ShopifyWorkflowRequest(BaseModel):
    order_number: str
    scenario: str


SCENARIOS = {
    "where_is_my_order": {
        "subject": "Where is my order?",
        "body": (
            "Hi, where is my order {order_number}? "
            "Please send me the latest tracking status."
        ),
    },
    "return_refund": {
        "subject": "Return and refund request",
        "body": (
            "I want to return order {order_number} and get a refund."
        ),
    },
    "missing_wrong_item": {
        "subject": "Wrong item received",
        "body": (
            "I received the wrong item in order {order_number}. "
            "Please help."
        ),
    },
    "cancel_modify": {
        "subject": "Cancel my order",
        "body": (
            "Please cancel order {order_number} before it ships."
        ),
    },
}


def mock_gmail():
    return MockGmail(
        DATA_DIR / "mock_customer_emails.json"
    )


@router.get("/messages")
def messages():
    return mock_gmail().list_messages()


@router.post("/process/{message_id}")
def process(
    message_id: str,
    db: Session = Depends(get_db),
):
    message = mock_gmail().get_message(message_id)
    if not message:
        raise HTTPException(404, "Message not found")

    result, _ = CaseWorkflowService(db).process(message, source="mock")
    return result


@router.post("/shopify-workflow")
def shopify_workflow(
    payload: ShopifyWorkflowRequest,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if settings.shopify_mode != "live":
        raise HTTPException(
            status_code=400,
            detail="SHOPIFY_MODE must be live for this workflow test.",
        )

    scenario = SCENARIOS.get(payload.scenario)
    if not scenario:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unknown scenario. Choose one of: "
                + ", ".join(SCENARIOS)
            ),
        )

    shopify = build_shopify()

    try:
        real_order = shopify.find_by_order_number(
            payload.order_number
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Shopify lookup failed", exc),
        ) from exc

    if not real_order:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Order {payload.order_number} "
                "was not found in Shopify."
            ),
        )

    message = CustomerMessage(
        id=f"shopify_test_{uuid4().hex[:12]}",
        sender_email=(
            real_order.customer.email
            or "shopify-test@example.com"
        ),
        subject=scenario["subject"],
        body=scenario["body"].format(
            order_number=real_order.order_number
        ),
    )

    try:
        result, _ = CaseWorkflowService(db).process(
            message,
            shopify=shopify,
            source="shopify_test",
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Workflow processing failed", exc),
        ) from exc
