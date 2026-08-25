from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.db.repository import CaseRepository, case_source

router = APIRouter()


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("/attention")
def attention_queue(limit: int = 50, db: Session = Depends(get_db)):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    output = []

    for record in CaseRepository(db).list(limit=500):
        reasons = []
        if record.status in {"awaiting_approval", "decision_ready"}:
            reasons.append(record.status)
        if record.confidence < settings.low_confidence_threshold:
            reasons.append("low_confidence")
        if record.recommended_action == "manual_review":
            reasons.append("manual_review")

        if not reasons:
            continue

        wait_seconds = max(0, int((now - _aware(record.created_at)).total_seconds()))
        if "manual_review" in reasons or record.confidence < 0.5:
            priority = "high"
        elif record.status == "awaiting_approval":
            priority = "medium"
        else:
            priority = "normal"

        output.append(
            {
                "case_id": record.id,
                "subject": record.subject,
                "customer": record.sender_email,
                "intent": record.intent,
                "order_number": record.order_number,
                "confidence": record.confidence,
                "status": record.status,
                "recommended_action": record.recommended_action,
                "source": case_source(record),
                "wait_seconds": wait_seconds,
                "priority": priority,
                "reasons": reasons,
            }
        )

    output.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "normal": 2}[item["priority"]],
            -item["wait_seconds"],
        )
    )
    return output[: max(1, min(limit, 200))]
