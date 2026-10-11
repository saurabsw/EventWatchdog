import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal, init_db
from app.db.models import MetricEnrollment, ModelMetadata


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    db = SessionLocal()
    db.query(ModelMetadata).delete()
    db.query(MetricEnrollment).delete()
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_models_api_enrollment_and_listing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Enroll metric series
        payload = {
            "metric_name": "payment_gateway_response_ms",
            "labels": {"gateway": "stripe"},
            "model_strategy": "robust_mad",
            "history_size": 2000,
            "bound_multiplier": 3.0,
            "enabled": True
        }
        res = await client.post("/api/v1/models", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["metric_name"] == "payment_gateway_response_ms"
        assert data["model_status"] == "PENDING"
        enrollment_id = data["id"]

        # 2. Duplicate enrollment returns 409
        dup_res = await client.post("/api/v1/models", json=payload)
        assert dup_res.status_code == 409

        # 3. List enrollments
        list_res = await client.get("/api/v1/models")
        assert list_res.status_code == 200
        enrollments = list_res.json()
        assert any(e["id"] == enrollment_id for e in enrollments)

        # 4. Patch enrollment
        patch_res = await client.patch(f"/api/v1/models/{enrollment_id}", json={"bound_multiplier": 3.5})
        assert patch_res.status_code == 200
        assert patch_res.json()["bound_multiplier"] == 3.5
