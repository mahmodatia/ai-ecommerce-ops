from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from app.core.config import get_settings
from app.domain.models import CustomerMessage
from app.services.ai.factory import build_ai
from app.services.factory import build_shopify
from app.services.orchestrator import Orchestrator


SCENARIO_PRESETS = {
    "where_is_my_order": {
        "label": "Where is my order?",
        "message": "Hi, where is my order {order_number}? I have not received tracking yet.",
    },
    "return_refund": {
        "label": "Return / Refund",
        "message": "Hi, I want to return order {order_number} and request a refund review.",
    },
    "missing_wrong_item": {
        "label": "Missing / Wrong Item",
        "message": "Hi, an item is missing or incorrect in order {order_number}. Please review it.",
    },
    "cancel_modify": {
        "label": "Cancel / Modify",
        "message": "Hi, please review a cancellation or modification for order {order_number} before it ships.",
    },
}


class SimulationService:
    def __init__(self, db):
        from app.db.repository import CaseRepository

        self.db = db
        self.repo = CaseRepository(db)

    def run(
        self,
        *,
        scenario: str,
        message: str | None,
        order_number: str | None,
        provider: str,
    ):
        if scenario not in SCENARIO_PRESETS:
            raise ValueError("Unsupported simulation scenario")

        settings = get_settings()
        provider_name = settings.ai_provider if provider == "current" else provider
        if provider_name not in {"rules", "openai"}:
            raise ValueError("Provider must be current, rules, or openai")

        ai_settings = settings.model_copy(update={"ai_provider": provider_name})
        ai = build_ai(ai_settings)
        shopify = build_shopify()

        default_order = order_number
        if not default_order:
            try:
                recent = shopify.list_recent_orders(limit=1)
                if recent:
                    default_order = recent[0].get("name") or recent[0].get("order_number")
            except Exception:
                default_order = None
        default_order = default_order or "#0000"
        text = (message or "").strip() or SCENARIO_PRESETS[scenario]["message"].format(
            order_number=default_order
        )

        customer_message = CustomerMessage(
            id=f"simulation_{uuid4().hex}",
            sender_email="simulation@example.com",
            subject=SCENARIO_PRESETS[scenario]["label"],
            body=text,
        )

        total_start = perf_counter()
        result = Orchestrator(ai, shopify).process(customer_message, source="simulation")

        if order_number and result.analysis.order_number != order_number:
            # Explicit simulation context is authoritative, then rerun the facts/decision path.
            result.analysis.order_number = order_number
            result = Orchestrator(ai, shopify).process(
                CustomerMessage(
                    id=customer_message.id,
                    sender_email=customer_message.sender_email,
                    subject=customer_message.subject,
                    body=f"{text}\nOrder reference: {order_number}",
                ),
                source="simulation",
            )
            result.analysis.order_number = order_number

        elapsed_ms = (perf_counter() - total_start) * 1000
        result.timings_ms["total"] = round(elapsed_ms, 2)

        if result.analysis.intent.value == "unknown" or result.order is None:
            status = "needs_review"
        elif result.decision.recommended_action.value == "manual_review":
            status = "needs_review"
        elif result.analysis.confidence < settings.low_confidence_threshold:
            status = "needs_review"
        else:
            status = "pass"

        record = self.repo.add_simulation(
            scenario=scenario,
            provider=provider_name,
            order_number=result.analysis.order_number,
            status=status,
            duration_ms=elapsed_ms,
            input_json={
                "message": text,
                "order_number": order_number,
                "scenario": scenario,
                "provider": provider_name,
            },
            result_json=result.model_dump(mode="json"),
        )

        return {
            "id": record.id,
            "scenario": scenario,
            "provider": provider_name,
            "status": status,
            "duration_ms": round(elapsed_ms, 2),
            "created_at": record.created_at,
            "result": result.model_dump(mode="json"),
            "safety": {
                "email_sent": False,
                "shopify_mutation_executed": False,
            },
        }
