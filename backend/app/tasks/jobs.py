from __future__ import annotations

import logging

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.factory import build_gmail
from app.services.workflow import CaseWorkflowService
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def process_gmail_message_task(self, message_id: str):
    settings = get_settings()
    if settings.gmail_mode != "live":
        return {
            "status": "skipped",
            "reason": "gmail_not_live",
        }

    gmail = build_gmail()
    message = gmail.get_message(message_id)

    if not message:
        return {
            "status": "not_found",
            "message_id": message_id,
        }

    with SessionLocal() as db:
        result, created = CaseWorkflowService(db).process(message, source="live_gmail")
        return {
            "status": "created" if created else "already_processed",
            "case_id": result.case_id,
            "message_id": message_id,
            "intent": result.analysis.intent.value,
        }


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def sync_gmail_inbox_task(self):
    settings = get_settings()

    if settings.gmail_mode != "live":
        return {
            "status": "skipped",
            "reason": "gmail_not_live",
        }

    gmail = build_gmail()
    messages = gmail.list_messages(limit=25)

    created = 0
    existing = 0
    failures = []

    with SessionLocal() as db:
        workflow = CaseWorkflowService(db)

        for message in messages:
            try:
                _, was_created = workflow.process(message, source="live_gmail")
                if was_created:
                    created += 1
                else:
                    existing += 1
            except Exception as exc:
                logger.exception(
                    "gmail_sync_message_failed message_id=%s",
                    message.id,
                )
                failures.append(
                    {
                        "message_id": message.id,
                        "error": type(exc).__name__,
                    }
                )

    return {
        "status": "complete",
        "created": created,
        "already_processed": existing,
        "failures": failures,
    }
