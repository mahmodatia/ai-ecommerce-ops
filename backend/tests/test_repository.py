from app.core.database import SessionLocal
from app.db.repository import CaseRepository
from app.domain.enums import CaseStatus


def test_stats_count_cases():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    client.post("/api/v1/demo/process/msg_001")
    client.post("/api/v1/demo/process/msg_006")

    stats = client.get("/api/v1/cases/stats")
    assert stats.status_code == 200
    assert stats.json()["total"] == 2


def test_action_audit_created_on_approval():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    processed = client.post("/api/v1/demo/process/msg_001").json()
    case_id = processed["case_id"]

    client.post(f"/api/v1/cases/{case_id}/approve")

    actions = client.get(f"/api/v1/cases/{case_id}/actions")
    assert actions.status_code == 200
    assert any(
        item["status"] == "approved"
        for item in actions.json()
    )
