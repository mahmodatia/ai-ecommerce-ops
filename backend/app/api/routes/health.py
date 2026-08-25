from sqlalchemy import text
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    s = get_settings()
    return {
        "status": "ok",
        "version": s.app_version,
        "environment": s.environment_mode,
        "ai_provider": s.ai_provider,
        "shopify_mode": s.shopify_mode,
        "gmail_mode": s.gmail_mode,
        "gmail_manual_send_enabled": s.gmail_manual_send_enabled,
        "tasks_mode": s.tasks_mode,
        "database": (
            "sqlite" if s.database_url.startswith("sqlite") else "postgresql"
        ),
        "auth_mode": s.auth_mode,
        "live_mutations_enabled": s.allow_live_actions,
    }


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
