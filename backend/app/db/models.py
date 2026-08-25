from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid4())


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    message_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    sender_email: Mapped[str] = mapped_column(String, index=True)
    subject: Mapped[str] = mapped_column(String)
    intent: Mapped[str] = mapped_column(String, index=True)
    order_number: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    recommended_action: Mapped[str] = mapped_column(String)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    draft_reply: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="awaiting_approval", index=True)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class ActionRecord(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(String, index=True)
    action_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="proposed", index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CaseCorrectionRecord(Base):
    __tablename__ = "case_corrections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(String, index=True)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SimulationRecord(Base):
    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scenario: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String)
    order_number: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
