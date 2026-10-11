import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app
from app.core.database import SessionLocal, init_db
from app.db.models import MonitorRule, Incident
from app.services.rule_engine import rule_engine_service


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    db = SessionLocal()
    db.query(Incident).delete()
    db.query(MonitorRule).delete()
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_full_workflow_journey():
    """
    Demonstrates the end-to-end incident lifecycle journey:
    1. Create static threshold rule
    2. Metric ingestion & breach detection -> Incident OPEN
    3. Repeated breach -> Incident deduplicated (occurrence_count incremented)
    4. Acknowledge incident -> Incident ACKNOWLEDGED
    5. Normal metric evaluation 1 -> Consecutive normal = 1 (remains ACKNOWLEDGED)
    6. Normal metric evaluation 2 -> Incident RESOLVED
    """
    transport = ASGITransport(app=app)
    db = SessionLocal()

    # Step 1: Create rule
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rule_res = await client.post("/api/v1/monitors", json={
            "name": "E2E High Latency Monitor",
            "metric_name": "api_latency_ms",
            "comparison_operator": ">",
            "threshold": 100.0,
            "severity": "CRITICAL",
            "evaluation_window_seconds": 60,
            "consecutive_breaches": 1,
            "consecutive_recoveries": 2
        })
        assert rule_res.status_code == 201
        rule = db.query(MonitorRule).filter(MonitorRule.name == "E2E High Latency Monitor").first()
        assert rule is not None

    # Step 2: Simulate breach (value = 150.0 > threshold 100.0)
    with patch("app.core.tsdb_client.tsdb_client.query_instant", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {
            "status": "success",
            "data": {
                "result": [{
                    "metric": {"service": "checkout"},
                    "value": [1700000000, "150.0"]
                }]
            }
        }
        res1 = await rule_engine_service.evaluate_rule(db, rule)
        assert res1["status"] == "evaluated"
        assert res1["results"][0]["status"] == "breached"
        inc_id = res1["results"][0]["incident_id"]

        inc = db.query(Incident).filter(Incident.id == inc_id).first()
        assert inc.state == "OPEN"
        assert inc.occurrence_count == 1
        assert inc.latest_value == 150.0

        # Step 3: Repeated breach (value = 180.0) -> Deduplication check
        mock_query.return_value = {
            "status": "success",
            "data": {
                "result": [{
                    "metric": {"service": "checkout"},
                    "value": [1700000015, "180.0"]
                }]
            }
        }
        res2 = await rule_engine_service.evaluate_rule(db, rule)
        assert res2["results"][0]["status"] == "breached"
        assert res2["results"][0]["incident_id"] == inc_id  # Deduplicated!

        db.refresh(inc)
        assert inc.occurrence_count == 2
        assert inc.latest_value == 180.0
        assert inc.state == "OPEN"

    # Step 4: Acknowledge incident via API
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ack_res = await client.post(f"/api/v1/incidents/{inc_id}/acknowledge")
        assert ack_res.status_code == 200
        assert ack_res.json()["state"] == "ACKNOWLEDGED"

    db.refresh(inc)
    assert inc.state == "ACKNOWLEDGED"

    # Step 5: Normal metric evaluation (value = 45.0 <= threshold 100.0)
    with patch("app.core.tsdb_client.tsdb_client.query_instant", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {
            "status": "success",
            "data": {
                "result": [{
                    "metric": {"service": "checkout"},
                    "value": [1700000030, "45.0"]
                }]
            }
        }
        # Run normal 1
        await rule_engine_service.evaluate_rule(db, rule)
        db.refresh(inc)
        assert inc.state == "ACKNOWLEDGED"
        assert inc.consecutive_normal_count == 1

        # Run normal 2 -> Trigger resolution (requires 2 consecutive recoveries)
        await rule_engine_service.evaluate_rule(db, rule)
        db.refresh(inc)
        assert inc.state == "RESOLVED"
        assert inc.resolved_at is not None

    db.close()
