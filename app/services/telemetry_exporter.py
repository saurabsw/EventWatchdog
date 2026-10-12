import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import MetricEnrollment, ModelMetadata, Incident, AuditLog
from app.core.schemas import MetricSample
from app.core.tsdb_client import tsdb_client

logger = logging.getLogger(__name__)


class TelemetryExporterService:
    """
    Exports internal Watchdog operational telemetry to VictoriaMetrics.
    Populates time-series metrics so Grafana dashboards render real-time
    baselines, prediction bounds, active/resolved incidents, and incident registers.
    """

    async def export_telemetry(self, db: Session):
        samples: List[MetricSample] = []
        now = datetime.now(timezone.utc)

        # 1. Export statistical models and prediction bounds
        enrollments = db.query(MetricEnrollment).filter(
            MetricEnrollment.enabled.is_(True),
            MetricEnrollment.model_status == "TRAINED"
        ).all()

        for e in enrollments:
            active_model = db.query(ModelMetadata).filter(
                ModelMetadata.enrollment_id == e.id
            ).order_by(ModelMetadata.version.desc()).first()

            if not active_model:
                continue

            labels = json.loads(e.labels_json) if e.labels_json else {}
            base_tags = {"metric_name": e.metric_name, "strategy": e.model_strategy, **labels}

            # Export Baseline & Bounds
            samples.append(MetricSample(
                metric="watchdog_model_baseline",
                timestamp=now,
                value=float(active_model.baseline_expected),
                labels=base_tags
            ))
            samples.append(MetricSample(
                metric="watchdog_model_upper_bound",
                timestamp=now,
                value=float(active_model.upper_bound),
                labels=base_tags
            ))
            samples.append(MetricSample(
                metric="watchdog_model_lower_bound",
                timestamp=now,
                value=float(active_model.lower_bound),
                labels=base_tags
            ))

            # Query instant observation from TSDB
            filter_parts = [f'{k}="{v}"' for k, v in labels.items()]
            filter_str = "{" + ",".join(filter_parts) + "}" if filter_parts else ""
            query = f"{e.metric_name}{filter_str}"

            try:
                res = await tsdb_client.query_instant(query)
                result_list = res.get("data", {}).get("result", [])
                if result_list:
                    val = float(result_list[0].get("value", [0, "0"])[1])
                    samples.append(MetricSample(
                        metric="watchdog_metric_value",
                        timestamp=now,
                        value=val,
                        labels=base_tags
                    ))
                    # Out-of-bounds breach indicator
                    is_anomaly = 1.0 if (val > active_model.upper_bound or val < active_model.lower_bound) else 0.0
                    samples.append(MetricSample(
                        metric="watchdog_anomaly_breach_indicator",
                        timestamp=now,
                        value=is_anomaly,
                        labels=base_tags
                    ))
            except Exception as ex:
                logger.debug("Failed querying instant sample for %s: %s", e.metric_name, ex)

        # 2. Export Incident Summary Metrics (Active, Acknowledged, Resolved)
        counts = db.query(
            Incident.state,
            Incident.severity,
            func.count(Incident.id)
        ).group_by(Incident.state, Incident.severity).all()

        seen_states = set()
        for state, severity, count in counts:
            seen_states.add(state)
            samples.append(MetricSample(
                metric="watchdog_incidents_active",
                timestamp=now,
                value=float(count),
                labels={"state": state, "severity": severity}
            ))

        # Ensure default zero metrics exist for Grafana stat panels
        for default_state in ["OPEN", "ACKNOWLEDGED", "RESOLVED"]:
            if default_state not in seen_states:
                samples.append(MetricSample(
                    metric="watchdog_incidents_active",
                    timestamp=now,
                    value=0.0,
                    labels={"state": default_state, "severity": "NONE"}
                ))

        # 3. Export Cumulative Detection Breach Counters
        detection_counts = db.query(
            Incident.detection_type,
            func.sum(Incident.occurrence_count)
        ).group_by(Incident.detection_type).all()

        for det_type, total_occ in detection_counts:
            samples.append(MetricSample(
                metric="watchdog_detections_total",
                timestamp=now,
                value=float(total_occ or 0),
                labels={"detection_type": det_type}
            ))

        # 4. Export Incident Register for the Grafana Alert Table Panel
        recent_incidents = db.query(Incident).order_by(Incident.last_seen_at.desc()).limit(50).all()
        for inc in recent_incidents:
            clean_summary = (inc.summary or "")[:120].replace('"', "'")
            samples.append(MetricSample(
                metric="watchdog_incident_info",
                timestamp=now,
                value=float(inc.latest_value if inc.latest_value is not None else 1.0),
                labels={
                    "id": str(inc.id),
                    "metric_name": inc.metric_name,
                    "severity": inc.severity,
                    "state": inc.state,
                    "detection_type": inc.detection_type,
                    "summary": clean_summary
                }
            ))

        if samples:
            await tsdb_client.write_metrics(samples)


telemetry_exporter_service = TelemetryExporterService()
