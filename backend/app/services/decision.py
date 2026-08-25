from datetime import datetime, timezone

from app.domain.enums import Intent, RecommendedAction
from app.domain.models import DecisionResult


class DecisionEngine:
    def decide(self, analysis, order):
        if not order:
            return DecisionResult(
                recommended_action=RecommendedAction.MANUAL_REVIEW,
                requires_human_approval=True,
                reason="No matching order found.",
            )

        sender_email = (analysis.customer_email or "").strip().casefold()
        order_email = (order.customer.email or "").strip().casefold()
        if sender_email and not order_email:
            return DecisionResult(
                recommended_action=RecommendedAction.MANUAL_REVIEW,
                requires_human_approval=True,
                reason=(
                    "Shopify does not provide a customer email for this order. "
                    "Verify identity before disclosing order details."
                ),
            )
        if sender_email and order_email and sender_email != order_email:
            return DecisionResult(
                recommended_action=RecommendedAction.MANUAL_REVIEW,
                requires_human_approval=True,
                reason=(
                    "Sender email does not match the Shopify order customer email. "
                    "Verify identity before disclosing order details."
                ),
            )

        if analysis.intent == Intent.WHERE_IS_MY_ORDER:
            # Important: an unfulfilled Shopify order has not been shipped yet,
            # so there is no tracking update to send.
            if order.fulfillment_status == "unfulfilled":
                return DecisionResult(
                    recommended_action=RecommendedAction.ORDER_STATUS_UPDATE,
                    requires_human_approval=False,
                    reason=(
                        "Order has not been fulfilled/shipped yet, "
                        "so tracking is not available yet."
                    ),
                )

            if (
                order.tracking_status == "no_movement"
                and order.tracking_last_update
            ):
                age = (
                    datetime.now(timezone.utc)
                    - order.tracking_last_update
                ).days
                if age >= 5:
                    return DecisionResult(
                        recommended_action=RecommendedAction.CARRIER_INVESTIGATION,
                        requires_human_approval=False,
                        reason=f"Tracking has not moved for {age} days.",
                    )

            if order.tracking_number or order.tracking_url:
                return DecisionResult(
                    recommended_action=RecommendedAction.SEND_TRACKING_UPDATE,
                    requires_human_approval=False,
                    reason="Tracking information is available and can be shared.",
                )

            return DecisionResult(
                recommended_action=RecommendedAction.ORDER_STATUS_UPDATE,
                requires_human_approval=False,
                reason=(
                    "Order status can be shared, but Shopify has "
                    "no tracking information for this order yet."
                ),
            )

        if analysis.intent == Intent.RETURN_REFUND:
            return DecisionResult(
                recommended_action=RecommendedAction.RETURN_REVIEW,
                requires_human_approval=True,
                reason=(
                    "Return/refund eligibility must be verified "
                    "against delivery date and policy."
                ),
            )

        if analysis.intent == Intent.MISSING_WRONG_ITEM:
            return DecisionResult(
                recommended_action=RecommendedAction.REPLACEMENT_REVIEW,
                requires_human_approval=True,
                reason=(
                    "Missing/wrong-item claims require "
                    "line-item verification."
                ),
            )

        if analysis.intent == Intent.CANCEL_MODIFY:
            cancel_requested = any(
                "cancellation" in fact.lower()
                for fact in analysis.facts
            )

            if order.fulfillment_status == "unfulfilled":
                return DecisionResult(
                    recommended_action=(
                        RecommendedAction.CANCEL_REVIEW
                        if cancel_requested
                        else RecommendedAction.MODIFY_REVIEW
                    ),
                    requires_human_approval=True,
                    reason="Order has not started fulfillment.",
                )

            return DecisionResult(
                recommended_action=RecommendedAction.CANNOT_MODIFY,
                requires_human_approval=True,
                reason="Fulfillment has already started.",
            )

        return DecisionResult(
            recommended_action=RecommendedAction.MANUAL_REVIEW,
            requires_human_approval=True,
            reason="Unsupported or ambiguous intent.",
        )
