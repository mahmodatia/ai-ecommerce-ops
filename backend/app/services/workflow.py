from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.repository import CaseRepository
from app.domain.models import CaseResult, CustomerMessage
from app.services.factory import build_ai_engine, build_shopify
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


def persisted_result(record) -> CaseResult:
    result = CaseResult.model_validate(record.result_json)
    result.case_id = record.id
    result.status = record.status
    result.draft_reply = record.draft_reply
    return result


class CaseWorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CaseRepository(db)

    def process(
        self,
        message: CustomerMessage,
        *,
        shopify=None,
        source: str = "unknown",
    ) -> tuple[CaseResult, bool]:
        existing = self.repo.get_by_message_id(message.id)
        if existing:
            logger.info(
                "idempotent_case_hit message_id=%s case_id=%s",
                message.id,
                existing.id,
            )
            return persisted_result(existing), False

        orchestrator = Orchestrator(
            build_ai_engine(),
            shopify or build_shopify(),
        )
        result = orchestrator.process(message, source=source)
        result.request_body = message.body
        result.request_subject = message.subject
        result.request_sender = message.sender_email

        record, created = self.repo.create_or_get(message, result)
        if not created:
            return persisted_result(record), False

        result.case_id = record.id
        result.status = record.status
        record.result_json = result.model_dump(mode="json")
        self.db.commit()

        logger.info(
            "case_created message_id=%s case_id=%s intent=%s order=%s source=%s",
            message.id,
            record.id,
            record.intent,
            record.order_number,
            source,
        )
        return result, True
