from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def test_health_and_ready():
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["version"] == "3.0.0"

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_process_is_idempotent():
    first = client.post("/api/v1/demo/process/msg_001")
    second = client.post("/api/v1/demo/process/msg_001")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["case_id"] == second.json()["case_id"]

    cases = client.get("/api/v1/cases").json()
    assert len(cases) == 1


def test_approve_is_idempotent_and_reject_after_approve_conflicts():
    processed = client.post("/api/v1/demo/process/msg_001")
    case_id = processed.json()["case_id"]

    first = client.post(f"/api/v1/cases/{case_id}/approve")
    second = client.post(f"/api/v1/cases/{case_id}/approve")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "approved"

    rejected = client.post(f"/api/v1/cases/{case_id}/reject")
    assert rejected.status_code == 409


def test_edit_draft_before_gmail_draft():
    processed = client.post("/api/v1/demo/process/msg_001")
    case_id = processed.json()["case_id"]

    edited = client.patch(
        f"/api/v1/cases/{case_id}/draft",
        json={"draft_reply": "Updated human-reviewed reply."},
    )

    assert edited.status_code == 200
    assert edited.json()["draft_reply"] == "Updated human-reviewed reply."


def test_shopify_workflow_requires_live_mode():
    settings = get_settings()
    original = settings.shopify_mode
    settings.shopify_mode = "mock"

    try:
        response = client.post(
            "/api/v1/demo/shopify-workflow",
            json={
                "order_number": "#1001",
                "scenario": "where_is_my_order",
            },
        )
        assert response.status_code == 400
    finally:
        settings.shopify_mode = original


def test_gmail_messages_requires_live_mode():
    settings = get_settings()
    original = settings.gmail_mode
    settings.gmail_mode = "mock"

    try:
        response = client.get("/api/v1/gmail/messages")
        assert response.status_code == 400
    finally:
        settings.gmail_mode = original


def test_background_route_requires_celery_mode():
    settings = get_settings()
    original = settings.tasks_mode
    settings.tasks_mode = "sync"

    try:
        response = client.post("/api/v1/gmail/process/abc/async")
        assert response.status_code == 400
    finally:
        settings.tasks_mode = original


def test_draft_is_locked_after_approval():
    processed = client.post("/api/v1/demo/process/msg_001")
    case_id = processed.json()["case_id"]
    assert client.post(f"/api/v1/cases/{case_id}/approve").status_code == 200

    edited = client.patch(
        f"/api/v1/cases/{case_id}/draft",
        json={"draft_reply": "Changed after approval"},
    )
    assert edited.status_code == 409


def test_manual_gmail_send_requires_explicit_opt_in():
    settings = get_settings()
    original_mode = settings.gmail_mode
    original_send = settings.gmail_manual_send_enabled
    try:
        settings.gmail_mode = "live"
        settings.gmail_manual_send_enabled = False
        response = client.post("/api/v1/gmail/cases/not-a-real-case/send")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()
    finally:
        settings.gmail_mode = original_mode
        settings.gmail_manual_send_enabled = original_send


def test_production_manual_gmail_send_requires_auth():
    settings = get_settings()
    original_env = settings.app_env
    original_auth = settings.auth_mode
    original_mode = settings.gmail_mode
    original_send = settings.gmail_manual_send_enabled
    try:
        settings.app_env = "production"
        settings.auth_mode = "off"
        settings.gmail_mode = "live"
        settings.gmail_manual_send_enabled = True
        response = client.post("/api/v1/gmail/cases/not-a-real-case/send")
        assert response.status_code == 403
        assert "requires auth_mode=password" in response.json()["detail"].lower()
    finally:
        settings.app_env = original_env
        settings.auth_mode = original_auth
        settings.gmail_mode = original_mode
        settings.gmail_manual_send_enabled = original_send
