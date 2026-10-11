import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal, init_db
from app.db.models import MonitorRule, Incident


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    db = SessionLocal()
    db.query(Incident).delete()
    db.query(MonitorRule).delete()
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_monitors_and_incidents_api_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a monitor rule
        rule_payload = {
            "name": "Integration Test High Error Rule",
            "metric_name": "app_log_errors_total",
            "label_filters": {"service": "checkout"},
            "evaluation_window_seconds": 60,
            "aggregation_func": "sum",
            "comparison_operator": ">",
            "threshold": 5.0,
            "severity": "CRITICAL",
            "consecutive_breaches": 1,
            "consecutive_recoveries": 2,
            "enabled": True
        }
        create_res = await client.post("/api/v1/monitors", json=rule_payload)
        assert create_res.status_code == 201
        rule = create_res.json()
        rule_id = rule["id"]
        assert rule["name"] == rule_payload["name"]

        # 2. List monitors
        list_res = await client.get("/api/v1/monitors")
        assert list_res.status_code == 200
        monitors = list_res.json()
        assert any(m["id"] == rule_id for m in monitors)

        # 3. Patch monitor rule
        patch_res = await client.patch(f"/api/v1/monitors/{rule_id}", json={"threshold": 10.0})
        assert patch_res.status_code == 200
        assert patch_res.json()["threshold"] == 10.0

        # 4. List incidents
        inc_res = await client.get("/api/v1/incidents")
        assert inc_res.status_code == 200
        assert isinstance(inc_res.json(), list)

        # 5. UI endpoint smoke check
        ui_res = await client.get("/ui/")
        assert ui_res.status_code == 200
        assert "EventWatchdog Console" in ui_res.text
