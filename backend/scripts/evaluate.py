import _bootstrap  # noqa: F401
import json
from collections import Counter
from pathlib import Path

from app.domain.models import CustomerMessage
from app.services.ai.rules import RulesEngine

path = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "mock_customer_emails.json"
)

items = json.loads(
    path.read_text(encoding="utf-8")
)
engine = RulesEngine()

intent_ok = 0
order_ok = 0
by_intent = Counter()
by_intent_ok = Counter()

for item in items:
    result = engine.analyze(
        CustomerMessage.model_validate(item)
    )

    expected_intent = item["expected_intent"]
    by_intent[expected_intent] += 1

    if result.intent.value == expected_intent:
        intent_ok += 1
        by_intent_ok[expected_intent] += 1

    if result.order_number == item["expected_order_number"]:
        order_ok += 1

n = len(items)

print(
    f"Intent accuracy: {intent_ok}/{n} = "
    f"{intent_ok/n:.1%}"
)
print(
    f"Order extraction accuracy: {order_ok}/{n} = "
    f"{order_ok/n:.1%}"
)
print("Per intent:")

for intent in sorted(by_intent):
    total = by_intent[intent]
    correct = by_intent_ok[intent]
    print(
        f"  {intent}: {correct}/{total} = "
        f"{correct/total:.1%}"
    )

print(
    "\nNote: this is a deliberately simple mock regression set, "
    "not a production accuracy claim."
)
