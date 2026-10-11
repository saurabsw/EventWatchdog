import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.config import settings
from app.core.schemas import MetricSample

logger = logging.getLogger(__name__)


class VictoriaMetricsClient:
    """Client for VictoriaMetrics Prometheus-compatible API and metric import."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.VICTORIAMETRICS_URL).rstrip("/")
        self.timeout = timeout or settings.VICTORIAMETRICS_TIMEOUT_SECONDS

    def format_prometheus_line(self, sample: MetricSample) -> str:
        """Format a MetricSample into Prometheus text line format."""
        labels_str = ""
        if sample.labels:
            pairs = [f'{k}="{v}"' for k, v in sorted(sample.labels.items())]
            labels_str = "{" + ",".join(pairs) + "}"
        ts_ms = int(sample.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000)
        return f"{sample.metric}{labels_str} {sample.value} {ts_ms}"

    async def write_metrics(self, samples: List[MetricSample]) -> bool:
        """Write metric samples to VictoriaMetrics via /api/v1/import/prometheus."""
        if not samples:
            return True
        lines = [self.format_prometheus_line(s) for s in samples]
        payload = "\n".join(lines) + "\n"
        url = f"{self.base_url}/api/v1/import/prometheus"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, content=payload.encode("utf-8"), headers={"Content-Type": "text/plain"})
                if res.status_code in (200, 204):
                    return True
                logger.warning("VictoriaMetrics import returned %s: %s", res.status_code, res.text)
                return False
        except Exception as e:
            logger.debug("Failed to write to VictoriaMetrics (%s): %s", url, e)
            return False

    async def query_instant(self, query: str) -> Dict[str, Any]:
        """Query instant PromQL from VictoriaMetrics."""
        url = f"{self.base_url}/api/v1/query"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"query": query})
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug("VictoriaMetrics query error: %s", e)
        return {"status": "error", "data": {"result": []}}

    async def query_range(self, query: str, start: int, end: int, step: str = "15s") -> Dict[str, Any]:
        """Query range PromQL from VictoriaMetrics."""
        url = f"{self.base_url}/api/v1/query_range"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params={"query": query, "start": start, "end": end, "step": step})
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug("VictoriaMetrics query_range error: %s", e)
        return {"status": "error", "data": {"result": []}}

    async def check_health(self) -> bool:
        """Check VictoriaMetrics /health endpoint."""
        url = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False


tsdb_client = VictoriaMetricsClient()
