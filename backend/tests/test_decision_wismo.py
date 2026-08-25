from datetime import datetime, timezone

from app.domain.enums import Intent, RecommendedAction
from app.domain.models import Customer, EmailUnderstanding, Order, OrderItem
from app.services.decision import DecisionEngine
from app.services.reply import ReplyGenerator


def make_order(
    fulfillment_status="unfulfilled",
    tracking_number=None,
    tracking_url=None,
):
    return Order(
        id="gid://shopify/Order/1",
        order_number="#1001",
        customer=Customer(
            name="Customer",
            email="customer@example.com",
        ),
        financial_status="paid",
        fulfillment_status=fulfillment_status,
        placed_at=datetime.now(timezone.utc),
        tracking_number=tracking_number,
        tracking_url=tracking_url,
        items=[
            OrderItem(
                sku="SKU-1",
                title="Test Product",
                quantity=1,
            )
        ],
        total_amount=31.0,
        currency="USD",
    )


def make_analysis():
    return EmailUnderstanding(
        intent=Intent.WHERE_IS_MY_ORDER,
        order_number="#1001",
        confidence=0.9,
        facts=[],
    )


def test_unfulfilled_order_does_not_claim_tracking_exists():
    order = make_order(fulfillment_status="unfulfilled")
    decision = DecisionEngine().decide(make_analysis(), order)

    assert decision.recommended_action == RecommendedAction.ORDER_STATUS_UPDATE

    reply = ReplyGenerator().generate(order, decision)
    assert "has not shipped yet" in reply
    assert "tracking is not available" in reply


def test_tracking_update_only_when_tracking_exists():
    order = make_order(
        fulfillment_status="fulfilled",
        tracking_number="TRACK123",
        tracking_url="https://example.com/track/TRACK123",
    )
    decision = DecisionEngine().decide(make_analysis(), order)

    assert decision.recommended_action == RecommendedAction.SEND_TRACKING_UPDATE

    reply = ReplyGenerator().generate(order, decision)
    assert "TRACK123" in reply


def test_sender_email_mismatch_forces_manual_review_before_disclosure():
    order = make_order(fulfillment_status="fulfilled", tracking_number="TRACK123")
    analysis = make_analysis()
    analysis.customer_email = "different-customer@example.com"

    decision = DecisionEngine().decide(analysis, order)

    assert decision.recommended_action == RecommendedAction.MANUAL_REVIEW
    assert decision.requires_human_approval is True
    assert "does not match" in decision.reason

    reply = ReplyGenerator().generate(order, decision)
    assert "TRACK123" not in reply
    assert "team member" in reply.lower()


def test_missing_shopify_customer_email_forces_manual_review_before_disclosure():
    order = make_order(fulfillment_status="fulfilled", tracking_number="TRACK123")
    order.customer.email = ""
    analysis = make_analysis()
    analysis.customer_email = "customer@example.com"

    decision = DecisionEngine().decide(analysis, order)

    assert decision.recommended_action == RecommendedAction.MANUAL_REVIEW
    assert decision.requires_human_approval is True
    assert "does not provide a customer email" in decision.reason

    reply = ReplyGenerator().generate(order, decision)
    assert "TRACK123" not in reply
