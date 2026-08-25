from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_case_detail_includes_trace_and_source():
    created = client.post("/api/v1/demo/process/msg_001")
    assert created.status_code == 200
    case_id = created.json()["case_id"]

    detail = client.get(f"/api/v1/cases/{case_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["source"] == "mock"
    assert payload["trace"]
    assert payload["timings_ms"]["total"] >= 0
    assert payload["request_body"]


def test_attention_queue_contains_reviewable_case():
    client.post("/api/v1/demo/process/msg_006")
    response = client.get("/api/v1/attention")
    assert response.status_code == 200
    assert response.json()
    assert "source" in response.json()[0]


def test_human_correction_is_audited():
    created = client.post("/api/v1/demo/process/msg_001").json()
    case_id = created["case_id"]

    corrected = client.post(
        f"/api/v1/cases/{case_id}/corrections",
        json={
            "intent": "return_refund",
            "order_number": "#8291",
            "recommended_action": "return_review",
            "notes": "Operator reviewed the customer request.",
        },
    )
    assert corrected.status_code == 200
    payload = corrected.json()
    assert payload["intent"] == "return_refund"
    assert payload["recommended_action"] == "return_review"
    assert payload["corrections"]
    assert any(
        action["action_type"] == "analysis_correction"
        for action in payload["actions"]
    )


def test_simulation_is_safe_and_persisted():
    response = client.post(
        "/api/v1/simulations",
        json={
            "scenario": "where_is_my_order",
            "order_number": "#8291",
            "provider": "rules",
            "message": "Where is my order #8291?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["safety"]["email_sent"] is False
    assert payload["safety"]["shopify_mutation_executed"] is False
    assert payload["result"]["trace"]

    recent = client.get("/api/v1/simulations")
    assert recent.status_code == 200
    assert len(recent.json()) == 1


def test_customer_signals_are_derived_from_cases():
    client.post("/api/v1/demo/process/msg_001")
    client.post("/api/v1/demo/process/msg_006")
    response = client.get("/api/v1/signals/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_size"] == 2
    assert sum(item["count"] for item in payload["contact_drivers"]) == 2


def test_policies_and_integrations_are_safe():
    policies = client.get("/api/v1/policies")
    assert policies.status_code == 200
    assert len(policies.json()) == 4

    integrations = client.get("/api/v1/integrations/status")
    assert integrations.status_code == 200
    safety = integrations.json()["safety"]
    assert safety["gmail_auto_send"] is False
    assert safety["shopify_mutations"] is False


def test_mock_shopify_orders_are_available_in_demo_mode():
    response = client.get("/api/v1/shopify/orders?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["source"] == "mock"


def test_global_audit_contains_case_creation():
    client.post("/api/v1/demo/process/msg_001")
    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    assert any(item["action"] == "case_created" for item in response.json())


def test_policy_payload_has_arabic_copy():
    response = client.get('/api/v1/policies/where_is_my_order')
    assert response.status_code == 200
    payload = response.json()
    assert payload['content_ar']
    assert payload['name_ar']


def test_environment_mode_distinguishes_mixed_integrations():
    from app.core.config import get_settings

    settings = get_settings()
    original_gmail = settings.gmail_mode
    original_shopify = settings.shopify_mode
    try:
        settings.gmail_mode = 'live'
        settings.shopify_mode = 'mock'
        assert settings.environment_mode == 'mixed'

        settings.gmail_mode = 'mock'
        settings.shopify_mode = 'mock'
        assert settings.environment_mode == 'demo'

        settings.gmail_mode = 'live'
        settings.shopify_mode = 'live'
        assert settings.environment_mode == 'live'
    finally:
        settings.gmail_mode = original_gmail
        settings.shopify_mode = original_shopify


def test_human_override_cannot_bypass_sender_order_identity_guard():
    created = client.post("/api/v1/demo/process/msg_001").json()
    case_id = created["case_id"]

    response = client.post(
        f"/api/v1/cases/{case_id}/corrections",
        json={
            "order_number": "#8292",
            "recommended_action": "send_tracking_update",
            "notes": "Attempted override without identity verification.",
        },
    )

    assert response.status_code == 409
    assert "cannot be verified" in response.json()["detail"]
