from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import public_error_detail
from app.core.request_user import request_actor
from app.db.repository import CaseRepository
from app.domain.enums import CaseStatus
from app.services.factory import build_gmail
from app.services.workflow import CaseWorkflowService

router = APIRouter()


@router.get("/status")
def gmail_status():
    settings = get_settings()

    return {
        "mode": settings.gmail_mode,
        "query": settings.gmail_query,
        "support_only": settings.gmail_support_only,
        "auto_send": False,
        "manual_send_enabled": settings.gmail_manual_send_enabled,
    }


@router.get("/messages")
def gmail_messages(
    limit: int = 10,
    support_only: bool | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if settings.gmail_mode != "live":
        raise HTTPException(
            status_code=400,
            detail="Set GMAIL_MODE=live to read the real Gmail inbox.",
        )

    try:
        gmail = build_gmail()
        messages = gmail.list_messages(
            limit=max(1, min(limit, 25)),
            support_only=support_only,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Gmail inbox failed", exc),
        ) from exc

    repo = CaseRepository(db)
    output = []

    for message in messages:
        existing = repo.get_by_message_id(message.id)
        row = message.model_dump(mode="json")
        row["processed"] = existing is not None
        row["case_id"] = existing.id if existing else None
        row["case_status"] = existing.status if existing else None
        output.append(row)

    return output


@router.post("/process/{message_id}")
def process_gmail_message(
    message_id: str,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if settings.gmail_mode != "live":
        raise HTTPException(
            status_code=400,
            detail="Set GMAIL_MODE=live first.",
        )

    repo = CaseRepository(db)
    existing = repo.get_by_message_id(message_id)
    if existing:
        from app.services.workflow import persisted_result
        return persisted_result(existing)

    try:
        gmail = build_gmail()
        message = gmail.get_message(message_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Gmail message read failed", exc),
        ) from exc

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Gmail message not found.",
        )

    try:
        result, _ = CaseWorkflowService(db).process(message, source="live_gmail")
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Workflow processing failed", exc),
        ) from exc


@router.post("/process/{message_id}/async")
def process_gmail_message_async(message_id: str):
    settings = get_settings()

    if settings.tasks_mode != "celery":
        raise HTTPException(
            status_code=400,
            detail="Set TASKS_MODE=celery to use background jobs.",
        )

    from app.tasks.jobs import process_gmail_message_task

    task = process_gmail_message_task.delay(message_id)
    return {
        "task_id": task.id,
        "status": "queued",
    }


@router.post("/sync")
def sync_gmail_inbox():
    settings = get_settings()

    if settings.tasks_mode != "celery":
        raise HTTPException(
            status_code=400,
            detail="Set TASKS_MODE=celery to run inbox sync in background.",
        )

    from app.tasks.jobs import sync_gmail_inbox_task

    task = sync_gmail_inbox_task.delay()
    return {
        "task_id": task.id,
        "status": "queued",
    }


@router.post("/cases/{case_id}/draft")
def create_gmail_draft(
    case_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if settings.gmail_mode != "live":
        raise HTTPException(
            status_code=400,
            detail="Set GMAIL_MODE=live first.",
        )

    repo = CaseRepository(db)
    record = repo.get(case_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Case not found.",
        )

    existing_action = repo.latest_action(
        case_id,
        "gmail_draft",
        status="created",
    )
    if existing_action:
        return {
            "status": CaseStatus.GMAIL_DRAFT_CREATED.value,
            "draft_id": existing_action.details.get("gmail_draft_id"),
            "case_id": case_id,
            "idempotent": True,
        }

    if record.status != CaseStatus.APPROVED.value:
        raise HTTPException(
            status_code=409,
            detail="Approve the case before creating a Gmail draft.",
        )

    if (
        record.message_id.startswith("msg_")
        or record.message_id.startswith("shopify_test_")
    ):
        raise HTTPException(
            status_code=409,
            detail="This case did not originate from real Gmail.",
        )

    try:
        draft = build_gmail().create_reply_draft(
            original_message_id=record.message_id,
            to_email=record.sender_email,
            subject=record.subject,
            body=record.draft_reply,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=public_error_detail("Gmail draft creation failed", exc),
        ) from exc

    repo.add_action(
        case_id=case_id,
        action_type="gmail_draft",
        status="created",
        details={
            "gmail_draft_id": draft.get("id"),
            "gmail_message_id": record.message_id,
            "created_by": request_actor(request),
        },
    )

    try:
        repo.transition(
            case_id,
            CaseStatus.GMAIL_DRAFT_CREATED.value,
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    return {
        "status": CaseStatus.GMAIL_DRAFT_CREATED.value,
        "draft_id": draft.get("id"),
        "case_id": case_id,
        "idempotent": False,
    }


@router.post("/cases/{case_id}/send")
def send_gmail_message(
    case_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if not settings.gmail_manual_send_enabled:
        raise HTTPException(
            status_code=403,
            detail="Manual Gmail sending is disabled. Set GMAIL_MANUAL_SEND_ENABLED=true explicitly to enable it.",
        )

    if settings.app_env.lower() in {"production", "prod"} and settings.auth_mode != "password":
        raise HTTPException(
            status_code=403,
            detail="Production manual sending requires AUTH_MODE=password.",
        )

    if settings.gmail_mode != "live":
        raise HTTPException(status_code=400, detail="Set GMAIL_MODE=live first.")

    repo = CaseRepository(db)
    record = repo.get(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found.")

    existing_action = repo.latest_action(case_id, "gmail_send", status="sent")
    if existing_action:
        return {
            "status": CaseStatus.GMAIL_SENT.value,
            "message_id": existing_action.details.get("gmail_message_id"),
            "case_id": case_id,
            "idempotent": True,
        }

    if record.status != CaseStatus.GMAIL_DRAFT_CREATED.value:
        raise HTTPException(
            status_code=409,
            detail="Create a Gmail draft after approval before sending.",
        )

    if record.message_id.startswith("msg_") or record.message_id.startswith("shopify_test_"):
        raise HTTPException(status_code=409, detail="This case did not originate from real Gmail.")

    draft_action = repo.latest_action(case_id, "gmail_draft", status="created")
    draft_id = draft_action.details.get("gmail_draft_id") if draft_action else None
    if not draft_id:
        raise HTTPException(status_code=409, detail="No Gmail draft exists for this case.")

    try:
        sent = build_gmail().send_draft(draft_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=public_error_detail("Gmail send failed", exc)) from exc

    repo.add_action(
        case_id=case_id,
        action_type="gmail_send",
        status="sent",
        details={
            "gmail_draft_id": draft_id,
            "gmail_message_id": sent.get("id"),
            "sent_by": request_actor(request),
        },
    )
    try:
        repo.transition(case_id, CaseStatus.GMAIL_SENT.value)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "status": CaseStatus.GMAIL_SENT.value,
        "message_id": sent.get("id"),
        "case_id": case_id,
        "idempotent": False,
    }
