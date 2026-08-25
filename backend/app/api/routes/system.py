from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.db.repository import CaseRepository

router = APIRouter()


@router.get("/integrations/status")
def integrations_status():
    settings = get_settings()
    database_kind = (
        "sqlite" if settings.database_url.startswith("sqlite") else "postgresql"
    )

    return {
        "environment": settings.environment_mode,
        "version": settings.app_version,
        "gmail": {
            "mode": settings.gmail_mode,
            "connected": (
                settings.gmail_mode == "live"
                and Path(settings.gmail_token_file).exists()
            ),
            "capabilities": ["read_support_inbox", "create_drafts"],
            "auto_send": False,
            "manual_send_enabled": settings.gmail_manual_send_enabled,
        },
        "shopify": {
            "mode": settings.shopify_mode,
            "connected": bool(
                settings.shopify_mode == "live"
                and settings.shopify_shop
                and settings.shopify_client_id
                and settings.shopify_client_secret
            ),
            "shop": settings.shopify_shop,
            "capabilities": ["read_orders", "read_order_facts"],
            "mutations": False,
        },
        "ai": {
            "provider": settings.ai_provider,
            "fallback_to_rules": settings.ai_fallback_to_rules,
            "prompt_version": settings.prompt_version,
        },
        "database": {"kind": database_kind, "configured": True},
        "jobs": {
            "mode": settings.tasks_mode,
            "auto_poll": settings.gmail_auto_poll,
        },
        "policy": {"engine": "deterministic", "version": settings.policy_version},
        "auth": {"mode": settings.auth_mode},
        "safety": {
            "gmail_auto_send": False,
            "gmail_manual_send_enabled": settings.gmail_manual_send_enabled,
            "shopify_mutations": False,
            "allow_live_actions": settings.allow_live_actions,
        },
    }


@router.get("/audit")
def audit_log(limit: int = 100, db: Session = Depends(get_db)):
    repo = CaseRepository(db)
    output = []
    for action in repo.list_global_actions(limit=limit):
        case = repo.get(action.case_id)
        output.append(
            {
                "id": action.id,
                "timestamp": action.created_at,
                "actor": (
                    action.details.get("approved_by")
                    or action.details.get("rejected_by")
                    or action.details.get("edited_by")
                    or action.details.get("created_by")
                    or action.details.get("actor")
                    or "system"
                ),
                "action": action.action_type,
                "status": action.status,
                "case_id": action.case_id,
                "order_number": case.order_number if case else None,
                "details": action.details,
            }
        )
    return output
