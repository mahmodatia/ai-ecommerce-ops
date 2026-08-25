from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.request_user import request_actor
from app.db.repository import CaseRepository, case_source
from app.domain.enums import CaseStatus
from app.services.correction import CaseCorrectionService

router = APIRouter()


class DraftUpdate(BaseModel):
    draft_reply: str = Field(min_length=1, max_length=12000)


class CorrectionRequest(BaseModel):
    intent: str | None = None
    order_number: str | None = Field(default=None, max_length=64)
    recommended_action: str | None = None
    notes: str | None = Field(default=None, max_length=2000)


def serialize(record, *, include_result: bool = False):
    result = record.result_json or {}
    payload = {
        "id": record.id,
        "message_id": record.message_id,
        "sender_email": record.sender_email,
        "subject": record.subject,
        "intent": record.intent,
        "order_number": record.order_number,
        "confidence": record.confidence,
        "recommended_action": record.recommended_action,
        "requires_human_approval": record.requires_human_approval,
        "draft_reply": record.draft_reply,
        "status": record.status,
        "source": case_source(record),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "timings_ms": result.get("timings_ms", {}),
    }
    if include_result:
        payload.update(
            {
                "analysis": result.get("analysis"),
                "order": result.get("order"),
                "policy_excerpt": result.get("policy_excerpt"),
                "decision": result.get("decision"),
                "trace": result.get("trace", []),
                "request_body": result.get("request_body"),
                "request_subject": result.get("request_subject"),
                "request_sender": result.get("request_sender"),
            }
        )
    return payload


@router.get("/stats")
def case_stats(db: Session = Depends(get_db)):
    return CaseRepository(db).stats()


@router.get("")
def list_cases(
    limit: int = 200,
    db: Session = Depends(get_db),
):
    return [serialize(record) for record in CaseRepository(db).list(limit=limit)]


@router.get("/{case_id}")
def case_detail(case_id: str, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    record = repo.get(case_id)
    if not record:
        raise HTTPException(404, "Case not found")

    payload = serialize(record, include_result=True)
    payload["actions"] = [
        {
            "id": action.id,
            "action_type": action.action_type,
            "status": action.status,
            "details": action.details,
            "created_at": action.created_at,
        }
        for action in repo.list_actions(case_id)
    ]
    payload["corrections"] = [
        {
            "id": correction.id,
            "notes": correction.notes,
            "actor": correction.actor,
            "before": correction.before_json,
            "after": correction.after_json,
            "created_at": correction.created_at,
        }
        for correction in repo.list_corrections(case_id)
    ]
    return payload


@router.get("/{case_id}/actions")
def case_actions(case_id: str, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    record = repo.get(case_id)
    if not record:
        raise HTTPException(404, "Case not found")

    return [
        {
            "id": action.id,
            "action_type": action.action_type,
            "status": action.status,
            "details": action.details,
            "created_at": action.created_at,
        }
        for action in repo.list_actions(case_id)
    ]


@router.patch("/{case_id}/draft")
def update_draft(
    case_id: str,
    payload: DraftUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = CaseRepository(db)
    try:
        record = repo.update_draft(case_id, payload.draft_reply)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    if not record:
        raise HTTPException(404, "Case not found")

    repo.add_action(
        case_id,
        "draft_reply",
        "edited",
        {"edited_by": request_actor(request)},
    )
    return serialize(record, include_result=True)


@router.post("/{case_id}/corrections")
def correct_analysis(
    case_id: str,
    payload: CorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        record = CaseCorrectionService(db).apply(
            case_id,
            intent=payload.intent,
            order_number=payload.order_number,
            recommended_action=payload.recommended_action,
            notes=payload.notes,
            actor=request_actor(request),
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(409, str(exc)) from exc

    return case_detail(case_id, db)


@router.post("/{case_id}/approve")
def approve(case_id: str, request: Request, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    try:
        record, changed = repo.transition(case_id, CaseStatus.APPROVED.value)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    if not record:
        raise HTTPException(404, "Case not found")

    if changed:
        repo.add_action(
            case_id,
            record.recommended_action,
            "approved",
            {"approved_by": request_actor(request)},
        )
    return serialize(record, include_result=True)


@router.post("/{case_id}/reject")
def reject(case_id: str, request: Request, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    try:
        record, changed = repo.transition(case_id, CaseStatus.REJECTED.value)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    if not record:
        raise HTTPException(404, "Case not found")

    if changed:
        repo.add_action(
            case_id,
            record.recommended_action,
            "rejected",
            {"rejected_by": request_actor(request)},
        )
    return serialize(record, include_result=True)
