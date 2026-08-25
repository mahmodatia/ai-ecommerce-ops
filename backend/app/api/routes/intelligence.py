from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import public_error_detail
from app.db.models import ActionRecord, CaseCorrectionRecord, CaseRecord
from app.db.repository import CaseRepository
from app.services.policy import get_policy_definition, list_policies
from app.services.simulation import SCENARIO_PRESETS, SimulationService

router = APIRouter()


class SimulationRequest(BaseModel):
    scenario: str
    message: str | None = Field(default=None, max_length=6000)
    order_number: str | None = Field(default=None, max_length=100)
    provider: str = "current"


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("/simulations/presets")
def simulation_presets():
    return [
        {"value": key, **value}
        for key, value in SCENARIO_PRESETS.items()
    ]


@router.post("/simulations")
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    try:
        return SimulationService(db).run(
            scenario=payload.scenario,
            message=payload.message,
            order_number=payload.order_number,
            provider=payload.provider,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, public_error_detail("Simulation failed safely", exc)) from exc


@router.get("/simulations")
def recent_simulations(limit: int = 20, db: Session = Depends(get_db)):
    return [
        {
            "id": record.id,
            "scenario": record.scenario,
            "provider": record.provider,
            "order_number": record.order_number,
            "status": record.status,
            "duration_ms": round(record.duration_ms, 2),
            "created_at": record.created_at,
            "result": record.result_json,
        }
        for record in CaseRepository(db).list_simulations(limit=limit)
    ]


@router.get("/simulations/{simulation_id}")
def simulation_detail(simulation_id: str, db: Session = Depends(get_db)):
    record = CaseRepository(db).get_simulation(simulation_id)
    if not record:
        raise HTTPException(404, "Simulation not found")
    return {
        "id": record.id,
        "scenario": record.scenario,
        "provider": record.provider,
        "order_number": record.order_number,
        "status": record.status,
        "duration_ms": round(record.duration_ms, 2),
        "input": record.input_json,
        "result": record.result_json,
        "created_at": record.created_at,
    }


@router.get("/signals/overview")
def customer_signals(db: Session = Depends(get_db)):
    cases = list(db.scalars(select(CaseRecord)))
    total = len(cases)
    counts = Counter(record.intent for record in cases)

    drivers = []
    for intent in [
        "where_is_my_order",
        "return_refund",
        "missing_wrong_item",
        "cancel_modify",
        "unknown",
    ]:
        count = counts.get(intent, 0)
        drivers.append(
            {
                "intent": intent,
                "count": count,
                "percentage": round((count / total * 100) if total else 0, 1),
            }
        )

    approved_states = {"approved", "gmail_draft_created"}
    completed = [
        record for record in cases if record.status in approved_states | {"rejected"}
    ]
    accepted = [record for record in completed if record.status in approved_states]
    acceptance_rate = (len(accepted) / len(completed) * 100) if completed else 0

    correction_case_ids = set(
        db.scalars(select(CaseCorrectionRecord.case_id))
    )
    correction_rate = (len(correction_case_ids) / total * 100) if total else 0

    edited_case_ids = set(
        db.scalars(
            select(ActionRecord.case_id).where(
                ActionRecord.action_type == "draft_reply",
                ActionRecord.status == "edited",
            )
        )
    )
    draft_edit_rate = (len(edited_case_ids) / total * 100) if total else 0

    review_seconds = []
    actions = list(
        db.scalars(
            select(ActionRecord).where(
                ActionRecord.status.in_(["approved", "rejected"])
            )
        )
    )
    case_map = {record.id: record for record in cases}
    seen = set()
    for action in sorted(actions, key=lambda item: item.created_at):
        if action.case_id in seen or action.case_id not in case_map:
            continue
        case = case_map[action.case_id]
        delta = (_aware(action.created_at) - _aware(case.created_at)).total_seconds()
        if delta >= 0:
            review_seconds.append(delta)
            seen.add(action.case_id)

    avg_review_seconds = (
        sum(review_seconds) / len(review_seconds) if review_seconds else 0
    )

    now = datetime.now(timezone.utc)
    current_start = now - timedelta(hours=24)
    previous_start = now - timedelta(hours=48)

    current_counts = Counter(
        record.intent for record in cases if _aware(record.created_at) >= current_start
    )
    previous_counts = Counter(
        record.intent
        for record in cases
        if previous_start <= _aware(record.created_at) < current_start
    )

    critical = []
    for intent in ["missing_wrong_item", "where_is_my_order"]:
        current = current_counts.get(intent, 0)
        previous = previous_counts.get(intent, 0)
        if current >= 3 and current > max(previous * 1.5, previous + 1):
            critical.append(
                {
                    "type": "contact_driver_spike",
                    "intent": intent,
                    "current_24h": current,
                    "previous_24h": previous,
                    "message": (
                        f"{intent} increased from {previous} to {current} cases "
                        "in the latest 24-hour window."
                    ),
                }
            )

    return {
        "data_current_as_of": now,
        "sample_size": total,
        "contact_drivers": drivers,
        "metrics": {
            "recommendation_acceptance_rate": round(acceptance_rate, 1),
            "human_correction_rate": round(correction_rate, 1),
            "draft_edit_rate": round(draft_edit_rate, 1),
            "average_review_seconds": round(avg_review_seconds, 1),
        },
        "critical_signals": critical,
        "trend_window": "24h_vs_previous_24h",
    }


@router.get("/policies")
def policies():
    return list_policies()


@router.get("/policies/{intent}")
def policy_detail(intent: str):
    from app.domain.enums import Intent

    try:
        policy = get_policy_definition(Intent(intent))
    except ValueError as exc:
        raise HTTPException(404, "Policy not found") from exc
    if not policy:
        raise HTTPException(404, "Policy not found")
    return policy
