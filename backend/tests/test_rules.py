import json
from pathlib import Path
from app.domain.models import CustomerMessage
from app.services.ai.rules import RulesEngine

def test_rules_dataset():
    items=json.loads(Path("data/mock_customer_emails.json").read_text(encoding="utf-8"))
    engine=RulesEngine()
    for item in items:
        r=engine.analyze(CustomerMessage.model_validate(item))
        assert r.intent.value == item["expected_intent"]
        assert r.order_number == item["expected_order_number"]
