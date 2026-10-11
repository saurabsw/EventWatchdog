import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal, init_db
from app.db.models import MetricEnrollment, ModelMetadata, Incident
from app.services.model_trainer import model_trainer
from app.services.anomaly_evaluator import anomaly_evaluator


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    db = SessionLocal()
    db.query(Incident).delete()
    db.query(ModelMetadata).delete()
    db.query(MetricEnrollment).delete()
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_anomaly_detection_functional_journey():
    """
    Demonstrates end-to-end anomaly detection lifecycle:
    1. Enroll metric series for statistical anomaly detection (Robust MAD, 2000 history).
    2. Train baseline model with 2,000 synthetic observations.
    3. Evaluate normal observation -> No incident.
    4. Evaluate out-of-bounds observation -> Incident created (ANOMALY).
    5. Evaluate continuing out-of-bounds observation -> Incident deduplicated (count = 2).
    6. Acknowledge incident.
    7. Evaluate normal observations -> Incident auto-resolves.
    """
    transport = ASGITransport(app=app)
    db = SessionLocal()

    # Step 1: Enroll metric series
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        enroll_res = await client.post("/api/v1/models", json={
            "metric_name": "checkout_pipeline_latency_ms",
            "labels": {"service": "checkout-web"},
            "model_strategy": "robust_mad",
            "history_size": 2000,
            "bound_multiplier": 3.0,
            "enabled": True
        })
        assert enroll_res.status_code == 201
        enroll_id = enroll_res.json()["id"]

    enrollment = db.query(MetricEnrollment).filter(MetricEnrollment.id == enroll_id).first()
    assert enrollment is not None

    # Step 2: Seed 2,000 synthetic historical observations (normal distribution around 100.0)
    synthetic_samples = [(1700000000 + i * 15, 100.0 + (i % 10) * 0.5) for i in range(2000)]
    metadata = await model_trainer.train_model_for_enrollment(db, enroll_id, custom_samples=synthetic_samples)

    assert metadata.version == 1
    assert metadata.sample_count == 2000
    assert 99.0 <= metadata.baseline_expected <= 105.0
    assert metadata.upper_bound > metadata.baseline_expected

    # Step 3: Evaluate normal observation (102.0 is well within bounds)
    res_normal = await anomaly_evaluator.evaluate_enrollment(db, enrollment, latest_value_override=102.0)
    assert res_normal["status"] == "normal"
    assert db.query(Incident).count() == 0

    # Step 4: Evaluate known anomalous outlier (450.0 > upper_bound)
    res_anomaly1 = await anomaly_evaluator.evaluate_enrollment(db, enrollment, latest_value_override=450.0)
    assert res_anomaly1["status"] == "anomaly_detected"
    inc_id = res_anomaly1["incident_id"]

    inc = db.query(Incident).filter(Incident.id == inc_id).first()
    assert inc is not None
    assert inc.detection_type == "ANOMALY"
    assert inc.state == "OPEN"
    assert inc.occurrence_count == 1
    assert inc.latest_value == 450.0

    # Step 5: Continuing anomaly (500.0) -> Deduplication check
    res_anomaly2 = await anomaly_evaluator.evaluate_enrollment(db, enrollment, latest_value_override=500.0)
    assert res_anomaly2["status"] == "anomaly_detected"
    assert res_anomaly2["incident_id"] == inc_id  # Deduplicated

    db.refresh(inc)
    assert inc.occurrence_count == 2
    assert inc.latest_value == 500.0

    # Step 6: Acknowledge incident
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ack_res = await client.post(f"/api/v1/incidents/{inc_id}/acknowledge")
        assert ack_res.status_code == 200
        assert ack_res.json()["state"] == "ACKNOWLEDGED"

    # Step 7: Recovery with normal observations (requires 2 consecutive recoveries)
    await anomaly_evaluator.evaluate_enrollment(db, enrollment, latest_value_override=101.0)
    db.refresh(inc)
    assert inc.state == "ACKNOWLEDGED"
    assert inc.consecutive_normal_count == 1

    await anomaly_evaluator.evaluate_enrollment(db, enrollment, latest_value_override=101.5)
    db.refresh(inc)
    assert inc.state == "RESOLVED"
    assert inc.resolved_at is not None

    db.close()
