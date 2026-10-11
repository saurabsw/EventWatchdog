import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.core.database import get_db
from app.core.tsdb_client import tsdb_client
from app.db.models import MonitorRule, MetricEnrollment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metadata"])


@router.get("/metrics/discovered", summary="List known metric series and their labels")
async def list_discovered_metrics(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns discovered metric series from VictoriaMetrics active series,
    augmented with locally configured monitors and model enrollments.
    """
    metrics_map: Dict[str, Dict[str, Any]] = {}

    # 1. Query VictoriaMetrics for active metric labels
    try:
        url = f"{tsdb_client.base_url}/api/v1/label/__name__/values"
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                names = res.json().get("data", [])
                for name in names:
                    if name and not name.startswith("vm_"):
                        metrics_map[name] = {
                            "metric_name": name,
                            "source": "tsdb_active",
                            "has_rule": False,
                            "has_anomaly_model": False
                        }
    except Exception as e:
        logger.debug("TSDB metric discovery query skipped: %s", e)

    # 2. Add local defaults and monitored metrics
    default_known = [
        "cpu_usage_idle",
        "mem_used_percent",
        "disk_used_percent",
        "app_log_events_total",
        "app_log_errors_total",
        "app_request_duration_ms",
        "app_http_errors_total",
        "app_log_parse_errors_total",
        "payment_processing_latency_ms"
    ]
    for name in default_known:
        if name not in metrics_map:
            metrics_map[name] = {
                "metric_name": name,
                "source": "standard_schema",
                "has_rule": False,
                "has_anomaly_model": False
            }

    # 3. Check configured rules
    rule_metrics = {r[0] for r in db.query(MonitorRule.metric_name).distinct().all()}
    for rm in rule_metrics:
        if rm in metrics_map:
            metrics_map[rm]["has_rule"] = True
        else:
            metrics_map[rm] = {
                "metric_name": rm,
                "source": "monitor_rule",
                "has_rule": True,
                "has_anomaly_model": False
            }

    # 4. Check enrolled models
    enrolled_metrics = {e[0] for e in db.query(MetricEnrollment.metric_name).distinct().all()}
    for em in enrolled_metrics:
        if em in metrics_map:
            metrics_map[em]["has_anomaly_model"] = True
        else:
            metrics_map[em] = {
                "metric_name": em,
                "source": "anomaly_enrollment",
                "has_rule": False,
                "has_anomaly_model": True
            }

    return sorted(list(metrics_map.values()), key=lambda x: x["metric_name"])


@router.get("/detections", summary="List recent detection events from audit log")
def list_recent_detections(limit: int = 50, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List recent detection breach events from SQLite audit log."""
    from app.db.models import AuditLog
    logs = db.query(AuditLog).filter(
        AuditLog.action.in_(["CREATE", "BREACH_RECURRENCE", "RESOLVE"])
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "action": l.action,
            "details": l.details_json
        }
        for l in logs
    ]
