import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from app.core.schemas import MetricBatch, MetricIngestResponse, MetricSample
from app.core.tsdb_client import tsdb_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("", response_model=MetricIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(batch: MetricBatch):
    """
    Ingest a batch of standardized time-series metric samples into VictoriaMetrics.
    Validates metric names, finite values, and bounded labels.
    """
    if not batch.metrics:
        return MetricIngestResponse(accepted=0, rejected=0)

    success = await tsdb_client.write_metrics(batch.metrics)
    if not success:
        logger.error("Failed to write %d metrics to VictoriaMetrics", len(batch.metrics))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to persist metrics to time-series storage"
        )

    return MetricIngestResponse(
        accepted=len(batch.metrics),
        rejected=0
    )


@router.get("", summary="Query metrics range")
async def query_metrics(
    query: str = Query(..., description="PromQL query expression, e.g. 'cpu_usage_idle'"),
    start: int = Query(..., description="Start timestamp (Unix epoch seconds)"),
    end: int = Query(..., description="End timestamp (Unix epoch seconds)"),
    step: str = Query("15s", description="Query resolution step (e.g. '15s', '1m')")
):
    """
    Query metric samples from VictoriaMetrics using PromQL expressions.
    """
    data = await tsdb_client.query_range(query=query, start=start, end=end, step=step)
    return data
