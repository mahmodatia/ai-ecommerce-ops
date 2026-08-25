from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    ActionRecord,
    CaseCorrectionRecord,
    CaseRecord,
    SimulationRecord,
)
from app.domain.enums import CaseStatus
from app.domain.models import CaseResult, CustomerMessage


ALLOWED_TRANSITIONS = {
    CaseStatus.AWAITING_APPROVAL.value: {
        CaseStatus.APPROVED.value,
        CaseStatus.REJECTED.value,
    },
    CaseStatus.DECISION_READY.value: {
        CaseStatus.APPROVED.value,
        CaseStatus.REJECTED.value,
    },
    CaseStatus.APPROVED.value: {
        CaseStatus.GMAIL_DRAFT_CREATED.value,
    },
    CaseStatus.REJECTED.value: set(),
    CaseStatus.GMAIL_DRAFT_CREATED.value: {CaseStatus.GMAIL_SENT.value},
    CaseStatus.GMAIL_SENT.value: set(),
}


def case_source(record: CaseRecord) -> str:
    source = (record.result_json or {}).get("source")
    if source and source != "unknown":
        return source
    if record.message_id.startswith("msg_"):
        return "mock"
    if record.message_id.startswith("shopify_test_"):
        return "shopify_test"
    return "live_gmail"


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, message: CustomerMessage, result: CaseResult) -> CaseRecord:
        record = CaseRecord(
            message_id=message.id,
            sender_email=message.sender_email,
            subject=message.subject,
            intent=result.analysis.intent.value,
            order_number=result.analysis.order_number,
            confidence=result.analysis.confidence,
            recommended_action=result.decision.recommended_action.value,
            requires_human_approval=result.decision.requires_human_approval,
            draft_reply=result.draft_reply,
            status=(
                CaseStatus.AWAITING_APPROVAL.value
                if result.decision.requires_human_approval
                else CaseStatus.DECISION_READY.value
            ),
            result_json=result.model_dump(mode="json"),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self.add_action(
            record.id,
            "case_created",
            "created",
            {
                "source": result.source,
                "intent": record.intent,
                "order_number": record.order_number,
            },
        )
        return record

    def get_by_message_id(self, message_id: str) -> CaseRecord | None:
        return self.db.scalar(
            select(CaseRecord).where(CaseRecord.message_id == message_id)
        )

    def create_or_get(
        self,
        message: CustomerMessage,
        result: CaseResult,
    ) -> tuple[CaseRecord, bool]:
        existing = self.get_by_message_id(message.id)
        if existing:
            return existing, False
        try:
            return self.create(message, result), True
        except IntegrityError:
            # Another worker may have created the same Gmail case concurrently.
            self.db.rollback()
            existing = self.get_by_message_id(message.id)
            if existing:
                return existing, False
            raise

    def list(self, limit: int = 200) -> list[CaseRecord]:
        stmt = (
            select(CaseRecord)
            .order_by(CaseRecord.created_at.desc())
            .limit(max(1, min(limit, 500)))
        )
        return list(self.db.scalars(stmt))

    def get(self, case_id: str) -> CaseRecord | None:
        return self.db.get(CaseRecord, case_id)

    def transition(
        self,
        case_id: str,
        new_status: str,
    ) -> tuple[CaseRecord | None, bool]:
        record = self.get(case_id)
        if not record:
            return None, False

        if record.status == new_status:
            return record, False

        allowed = ALLOWED_TRANSITIONS.get(record.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid case transition: {record.status} -> {new_status}"
            )

        record.status = new_status
        result_json = dict(record.result_json or {})
        result_json["status"] = new_status
        record.result_json = result_json
        self.db.commit()
        self.db.refresh(record)
        return record, True

    def set_status(self, case_id: str, status: str) -> CaseRecord | None:
        record = self.get(case_id)
        if not record:
            return None
        record.status = status
        result_json = dict(record.result_json or {})
        result_json["status"] = status
        record.result_json = result_json
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_draft(self, case_id: str, draft_reply: str) -> CaseRecord | None:
        record = self.get(case_id)
        if not record:
            return None

        if record.status not in {
            CaseStatus.AWAITING_APPROVAL.value,
            CaseStatus.DECISION_READY.value,
        }:
            raise ValueError(
                "Draft can only be edited before approval or rejection. "
                "Re-review the case before changing approved customer-facing content."
            )

        clean = draft_reply.strip()
        if not clean:
            raise ValueError("Draft reply cannot be empty.")
        if len(clean) > 12000:
            raise ValueError("Draft reply is too long.")

        record.draft_reply = clean
        result_json = dict(record.result_json or {})
        result_json["draft_reply"] = clean
        result_json["status"] = record.status
        record.result_json = result_json
        self.db.commit()
        self.db.refresh(record)
        return record

    def replace_case_result(self, record: CaseRecord, result: CaseResult) -> CaseRecord:
        record.intent = result.analysis.intent.value
        record.order_number = result.analysis.order_number
        record.confidence = result.analysis.confidence
        record.recommended_action = result.decision.recommended_action.value
        record.requires_human_approval = result.decision.requires_human_approval
        record.draft_reply = result.draft_reply
        record.result_json = result.model_dump(mode="json")
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_action(
        self,
        case_id: str,
        action_type: str,
        status: str,
        details: dict,
    ) -> ActionRecord:
        action = ActionRecord(
            case_id=case_id,
            action_type=action_type,
            status=status,
            details=details,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def list_actions(self, case_id: str) -> list[ActionRecord]:
        stmt = (
            select(ActionRecord)
            .where(ActionRecord.case_id == case_id)
            .order_by(ActionRecord.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def list_global_actions(self, limit: int = 100) -> list[ActionRecord]:
        stmt = (
            select(ActionRecord)
            .order_by(ActionRecord.created_at.desc())
            .limit(max(1, min(limit, 500)))
        )
        return list(self.db.scalars(stmt))

    def latest_action(
        self,
        case_id: str,
        action_type: str,
        status: str | None = None,
    ) -> ActionRecord | None:
        stmt = (
            select(ActionRecord)
            .where(
                ActionRecord.case_id == case_id,
                ActionRecord.action_type == action_type,
            )
            .order_by(ActionRecord.created_at.desc())
            .limit(1)
        )
        if status is not None:
            stmt = stmt.where(ActionRecord.status == status)
        return self.db.scalar(stmt)

    def add_correction(
        self,
        case_id: str,
        before_json: dict,
        after_json: dict,
        notes: str | None,
        actor: str = "operator",
    ) -> CaseCorrectionRecord:
        correction = CaseCorrectionRecord(
            case_id=case_id,
            before_json=before_json,
            after_json=after_json,
            notes=notes,
            actor=actor,
        )
        self.db.add(correction)
        self.db.commit()
        self.db.refresh(correction)
        return correction

    def list_corrections(self, case_id: str) -> list[CaseCorrectionRecord]:
        stmt = (
            select(CaseCorrectionRecord)
            .where(CaseCorrectionRecord.case_id == case_id)
            .order_by(CaseCorrectionRecord.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def add_simulation(
        self,
        *,
        scenario: str,
        provider: str,
        order_number: str | None,
        status: str,
        duration_ms: float,
        input_json: dict,
        result_json: dict,
    ) -> SimulationRecord:
        record = SimulationRecord(
            scenario=scenario,
            provider=provider,
            order_number=order_number,
            status=status,
            duration_ms=duration_ms,
            input_json=input_json,
            result_json=result_json,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_simulations(self, limit: int = 20) -> list[SimulationRecord]:
        stmt = (
            select(SimulationRecord)
            .order_by(SimulationRecord.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        return list(self.db.scalars(stmt))

    def get_simulation(self, simulation_id: str) -> SimulationRecord | None:
        return self.db.get(SimulationRecord, simulation_id)

    def stats(self) -> dict:
        total = self.db.scalar(select(func.count(CaseRecord.id))) or 0
        rows = self.db.execute(
            select(CaseRecord.status, func.count(CaseRecord.id)).group_by(
                CaseRecord.status
            )
        ).all()
        by_status = {status: count for status, count in rows}
        intent_rows = self.db.execute(
            select(CaseRecord.intent, func.count(CaseRecord.id)).group_by(
                CaseRecord.intent
            )
        ).all()
        return {
            "total": total,
            "by_status": by_status,
            "by_intent": {intent: count for intent, count in intent_rows},
        }

    def cleanup_older_than(self, days: int) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
        old_case_ids = list(
            self.db.scalars(
                select(CaseRecord.id).where(CaseRecord.created_at < cutoff)
            )
        )

        deleted_actions = deleted_corrections = deleted_cases = 0
        if old_case_ids:
            actions_result = self.db.execute(
                delete(ActionRecord).where(ActionRecord.case_id.in_(old_case_ids))
            )
            correction_result = self.db.execute(
                delete(CaseCorrectionRecord).where(
                    CaseCorrectionRecord.case_id.in_(old_case_ids)
                )
            )
            cases_result = self.db.execute(
                delete(CaseRecord).where(CaseRecord.id.in_(old_case_ids))
            )
            deleted_actions = actions_result.rowcount or 0
            deleted_corrections = correction_result.rowcount or 0
            deleted_cases = cases_result.rowcount or 0

        simulation_result = self.db.execute(
            delete(SimulationRecord).where(SimulationRecord.created_at < cutoff)
        )
        self.db.commit()

        return {
            "deleted_cases": deleted_cases,
            "deleted_actions": deleted_actions,
            "deleted_corrections": deleted_corrections,
            "deleted_simulations": simulation_result.rowcount or 0,
        }
