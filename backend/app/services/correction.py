from __future__ import annotations

from copy import deepcopy

from app.db.repository import CaseRepository, case_source
from app.domain.enums import CaseStatus, Intent, RecommendedAction
from app.domain.models import CaseResult, DecisionResult, DecisionTraceStep
from app.services.decision import DecisionEngine
from app.services.factory import build_shopify
from app.services.policy import get_policy
from app.services.reply import ReplyGenerator


EDITABLE_STATUSES = {
    CaseStatus.AWAITING_APPROVAL.value,
    CaseStatus.DECISION_READY.value,
}


class CaseCorrectionService:
    def __init__(self, db):
        self.db = db
        self.repo = CaseRepository(db)
        self.decisions = DecisionEngine()
        self.replies = ReplyGenerator()

    def apply(
        self,
        case_id: str,
        *,
        intent: str | None = None,
        order_number: str | None = None,
        recommended_action: str | None = None,
        notes: str | None = None,
        actor: str = "operator",
    ):
        record = self.repo.get(case_id)
        if not record:
            raise LookupError("Case not found")
        if record.status not in EDITABLE_STATUSES:
            raise ValueError(
                "Analysis can only be corrected before approval or rejection."
            )

        result = CaseResult.model_validate(record.result_json)
        before = deepcopy(result.model_dump(mode="json"))

        if intent is not None:
            result.analysis.intent = Intent(intent)
            result.analysis.requires_policy_lookup = result.analysis.intent in {
                Intent.RETURN_REFUND,
                Intent.MISSING_WRONG_ITEM,
                Intent.CANCEL_MODIFY,
            }

        if order_number is not None:
            clean = order_number.strip()
            result.analysis.order_number = clean or None

        shopify = build_shopify()
        result.order = (
            shopify.find_by_order_number(result.analysis.order_number)
            if result.analysis.order_number
            else None
        )
        result.policy_excerpt = get_policy(result.analysis.intent)

        deterministic = self.decisions.decide(result.analysis, result.order)

        sender_email = (result.analysis.customer_email or "").strip().casefold()
        order_email = ((result.order.customer.email if result.order else "") or "").strip().casefold()
        identity_missing = bool(result.order and sender_email and not order_email)
        identity_mismatch = bool(
            result.order and sender_email and order_email and sender_email != order_email
        )
        identity_issue = identity_missing or identity_mismatch

        if recommended_action and identity_issue:
            raise ValueError(
                "Order ownership cannot be verified from Shopify customer email. "
                "Resolve identity before overriding the manual-review recommendation."
            )

        if recommended_action:
            action = RecommendedAction(recommended_action)
            result.decision = DecisionResult(
                recommended_action=action,
                requires_human_approval=True,
                reason=(
                    f"Human correction override. {notes.strip()}"
                    if notes and notes.strip()
                    else "Human correction override recorded for review."
                ),
            )
        else:
            result.decision = deterministic

        result.draft_reply = self.replies.generate(result.order, result.decision)
        result.status = record.status
        result.case_id = record.id
        result.source = case_source(record)
        result.trace = [
            DecisionTraceStep(
                key="human_correction",
                label="Human Correction",
                source="human",
                value=result.analysis.intent.value,
                detail=notes or "Operator corrected the effective analysis.",
            ),
            DecisionTraceStep(
                key="order_extraction",
                label="Order Extraction",
                source="deterministic",
                status="complete" if result.analysis.order_number else "warning",
                value=result.analysis.order_number or "No order reference",
                detail="Effective order reference after human review.",
            ),
            DecisionTraceStep(
                key="shopify_verification",
                label="Shopify Verification",
                source="shopify",
                status="warning" if identity_issue or not result.order else "complete",
                value=(
                    "Order found · identity verification required"
                    if identity_issue
                    else (
                        f"{result.order.fulfillment_status} · {result.order.financial_status}"
                        if result.order
                        else "No matching order"
                    )
                ),
                detail=(
                    (
                        "Shopify has no customer email for this order. Verify identity before disclosure."
                        if identity_missing
                        else "Sender email does not match the Shopify customer email. Verify identity before disclosure."
                    )
                    if identity_issue
                    else (
                        "Verified from current Shopify facts."
                        if result.order
                        else "No authoritative Shopify order facts found."
                    )
                ),
            ),
            DecisionTraceStep(
                key="policy_applied",
                label="Policy Applied",
                source="policy",
                value=result.analysis.intent.value,
                detail=result.policy_excerpt or "No mapped policy.",
            ),
            DecisionTraceStep(
                key="deterministic_rule",
                label="Deterministic Rule",
                source="rules",
                value=deterministic.recommended_action.value,
                detail=deterministic.reason,
            ),
            DecisionTraceStep(
                key="recommended_action",
                label="Recommended Action",
                source="recommendation",
                value=result.decision.recommended_action.value,
                detail=result.decision.reason,
            ),
            DecisionTraceStep(
                key="human_approval",
                label="Human Approval",
                source="human",
                status="pending",
                value="Required" if result.decision.requires_human_approval else "Review available",
                detail="No email is sent and no Shopify mutation is executed automatically.",
            ),
        ]

        self.repo.replace_case_result(record, result)
        after = result.model_dump(mode="json")
        correction = self.repo.add_correction(
            case_id,
            before,
            after,
            notes,
            actor=actor,
        )
        self.repo.add_action(
            case_id,
            "analysis_correction",
            "corrected",
            {
                "correction_id": correction.id,
                "actor": actor,
                "intent": result.analysis.intent.value,
                "order_number": result.analysis.order_number,
                "recommended_action": result.decision.recommended_action.value,
                "notes": notes,
            },
        )
        return record
