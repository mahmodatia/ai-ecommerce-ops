from __future__ import annotations

from time import perf_counter

from app.domain.models import CaseResult, DecisionTraceStep
from app.services.decision import DecisionEngine
from app.services.policy import get_policy
from app.services.reply import ReplyGenerator


class Orchestrator:
    def __init__(self, ai, shopify):
        self.ai = ai
        self.shopify = shopify
        self.decisions = DecisionEngine()
        self.replies = ReplyGenerator()

    def process(self, message, *, source: str = "unknown"):
        total_start = perf_counter()

        start = perf_counter()
        analysis = self.ai.analyze(message)
        understanding_ms = (perf_counter() - start) * 1000

        start = perf_counter()
        order = (
            self.shopify.find_by_order_number(analysis.order_number)
            if analysis.order_number
            else None
        )
        shopify_ms = (perf_counter() - start) * 1000

        sender_email = (analysis.customer_email or "").strip().casefold()
        order_email = ((order.customer.email if order else "") or "").strip().casefold()
        identity_missing = bool(order and sender_email and not order_email)
        identity_mismatch = bool(order and sender_email and order_email and sender_email != order_email)
        identity_issue = identity_missing or identity_mismatch

        start = perf_counter()
        policy = get_policy(analysis.intent)
        policy_ms = (perf_counter() - start) * 1000

        start = perf_counter()
        decision = self.decisions.decide(analysis, order)
        decision_ms = (perf_counter() - start) * 1000

        start = perf_counter()
        draft = self.replies.generate(order, decision)
        drafting_ms = (perf_counter() - start) * 1000

        total_ms = (perf_counter() - total_start) * 1000

        trace = [
            DecisionTraceStep(
                key="ai_understanding",
                label="AI Understanding",
                source="ai",
                value=analysis.intent.value,
                detail=f"Confidence {analysis.confidence:.0%}",
            ),
            DecisionTraceStep(
                key="order_extraction",
                label="Order Extraction",
                source="deterministic",
                status="complete" if analysis.order_number else "warning",
                value=analysis.order_number or "No order reference",
                detail="Order reference extracted from the customer request.",
            ),
            DecisionTraceStep(
                key="shopify_verification",
                label="Shopify Verification",
                source="shopify",
                status="warning" if identity_issue or not order else "complete",
                value=(
                    "Order found · identity verification required"
                    if identity_issue
                    else (
                        f"{order.fulfillment_status} · {order.financial_status}"
                        if order
                        else "No matching order"
                    )
                ),
                detail=(
                    (
                        "Order found, but Shopify has no customer email. Verify identity before disclosure."
                        if identity_missing
                        else "Order found, but the sender email does not match the Shopify customer email. Verify identity before disclosure."
                    )
                    if identity_issue
                    else (
                        "Verified from Shopify order data."
                        if order
                        else "No authoritative Shopify order facts were found."
                    )
                ),
            ),
            DecisionTraceStep(
                key="policy_applied",
                label="Policy Applied",
                source="policy",
                status="complete" if policy else "warning",
                value=analysis.intent.value,
                detail=policy or "No policy mapped to this request.",
            ),
            DecisionTraceStep(
                key="deterministic_rule",
                label="Deterministic Rule",
                source="rules",
                value=decision.recommended_action.value,
                detail=decision.reason,
            ),
            DecisionTraceStep(
                key="recommended_action",
                label="Recommended Action",
                source="recommendation",
                value=decision.recommended_action.value,
                detail=decision.reason,
            ),
            DecisionTraceStep(
                key="human_approval",
                label="Human Approval",
                source="human",
                status="pending",
                value=(
                    "Required"
                    if decision.requires_human_approval
                    else "Review available"
                ),
                detail=(
                    "A human must approve this recommendation before any "
                    "sensitive next step."
                    if decision.requires_human_approval
                    else "The recommendation is safe to review; no email is sent automatically."
                ),
            ),
        ]

        return CaseResult(
            message_id=message.id,
            analysis=analysis,
            order=order,
            policy_excerpt=policy,
            decision=decision,
            draft_reply=draft,
            status=(
                "awaiting_approval"
                if decision.requires_human_approval
                else "decision_ready"
            ),
            source=source,
            trace=trace,
            timings_ms={
                "understanding": round(understanding_ms, 2),
                "shopify": round(shopify_ms, 2),
                "policy": round(policy_ms, 2),
                "decision": round(decision_ms, 2),
                "drafting": round(drafting_ms, 2),
                "total": round(total_ms, 2),
            },
        )
