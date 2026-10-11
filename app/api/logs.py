import logging
from typing import List, Any
from fastapi import APIRouter, HTTPException, status
from app.core.schemas import LogBatchPayload, LogParseSummary
from app.services.log_parser import log_parser
from app.core.tsdb_client import tsdb_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=LogParseSummary, status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(payload: LogBatchPayload):
    """
    Ingest a batch of application logs (JSON array or raw multiline text).
    Parses recognized log lines into standardized time-series metrics.
    Malformed records are observed and counted under 'app_log_parse_errors_total'.
    """
    raw_items: List[Any] = []
    if payload.entries:
        raw_items.extend(payload.entries)
    if payload.raw_lines:
        lines = [line.strip() for line in payload.raw_lines.splitlines() if line.strip()]
        raw_items.extend(lines)

    if not raw_items:
        return LogParseSummary(
            total_received=0,
            parsed_metrics=0,
            parse_errors=0,
            metrics_generated=[]
        )

    # Parse and normalize into MetricSamples
    metrics, parse_errors, reasons = log_parser.process_batch(raw_items)

    # Persist generated metrics (including parse error counter metrics) to VictoriaMetrics
    if metrics:
        vm_success = await tsdb_client.write_metrics(metrics)
        if not vm_success:
            logger.warning("Failed to store %d parsed log metrics in VictoriaMetrics", len(metrics))

    unique_metric_names = sorted(list({m.metric for m in metrics}))

    return LogParseSummary(
        total_received=len(raw_items),
        parsed_metrics=len(metrics),
        parse_errors=parse_errors,
        metrics_generated=unique_metric_names,
        error_reasons=reasons
    )
