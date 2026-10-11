import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app
from app.core.schemas import MetricSample


@pytest.mark.asyncio
async def test_metric_ingest_and_query_endpoints():
    transport = ASGITransport(app=app)

    # Mock VictoriaMetricsClient write_metrics and query_range
    with patch("app.core.tsdb_client.tsdb_client.write_metrics", new_callable=AsyncMock) as mock_write, \
         patch("app.core.tsdb_client.tsdb_client.query_range", new_callable=AsyncMock) as mock_query:

        mock_write.return_value = True
        mock_query.return_value = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "cpu_usage_idle"},
                        "values": [[1700000000, "95.5"], [1700000015, "94.2"]]
                    }
                ]
            }
        }

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Ingest metric batch
            payload = {
                "metrics": [
                    {
                        "metric": "cpu_usage_idle",
                        "value": 95.5,
                        "labels": {"host": "node-01"}
                    }
                ]
            }
            res = await client.post("/api/v1/metrics", json=payload)
            assert res.status_code == 202
            data = res.json()
            assert data["accepted"] == 1
            assert data["rejected"] == 0
            assert mock_write.called

            # 2. Query metric range
            query_res = await client.get("/api/v1/metrics?query=cpu_usage_idle&start=1700000000&end=1700000030")
            assert query_res.status_code == 200
            q_data = query_res.json()
            assert q_data["status"] == "success"
            assert len(q_data["data"]["result"]) == 1


@pytest.mark.asyncio
async def test_log_ingest_endpoint():
    transport = ASGITransport(app=app)

    with patch("app.core.tsdb_client.tsdb_client.write_metrics", new_callable=AsyncMock) as mock_write:
        mock_write.return_value = True

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "entries": [
                    {
                        "timestamp": "2026-10-11T12:00:00Z",
                        "level": "ERROR",
                        "service": "orders",
                        "message": "Out of memory error in worker",
                        "duration_ms": 500.0,
                        "status_code": 500
                    },
                    "Malformed text line here"
                ]
            }
            res = await client.post("/api/v1/logs", json=payload)
            assert res.status_code == 202
            data = res.json()
            assert data["total_received"] == 2
            assert data["parse_errors"] == 1
            assert "app_log_errors_total" in data["metrics_generated"]
            assert "app_log_parse_errors_total" in data["metrics_generated"]
