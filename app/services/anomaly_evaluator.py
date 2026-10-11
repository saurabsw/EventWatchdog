import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import MetricEnrollment, ModelMetadata
from app.core.tsdb_client import tsdb_client
from app.services.incident_mgr import incident_service

logger = logging.getLogger(__name__)


class AnomalyEvaluationService:
    """Evaluates live time-series observations against enrolled active models."""

    async def evaluate_enrollment(
        self,
        db: Session,
        enrollment: MetricEnrollment,
        latest_value_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compares latest observation for the enrolled series against its active model bounds.
        Submits qualifying outliers to the incident manager.
        """
        if not enrollment.enabled or enrollment.model_status != "TRAINED":
            return {"enrollment_id": enrollment.id, "status": "skipped"}

        # Fetch latest active model metadata
        active_model = db.query(ModelMetadata).filter(
            ModelMetadata.enrollment_id == enrollment.id
        ).order_by(ModelMetadata.version.desc()).first()

        if not active_model:
            return {"enrollment_id": enrollment.id, "status": "no_active_model"}

        labels = json.loads(enrollment.labels_json) if enrollment.labels_json else {}

        val = latest_value_override

        if val is None:
            # Query instant observation from VictoriaMetrics
            filter_parts = [f'{k}="{v}"' for k, v in labels.items()]
            filter_str = "{" + ",".join(filter_parts) + "}" if filter_parts else ""
            query = f"{enrollment.metric_name}{filter_str}"

            res = await tsdb_client.query_instant(query)
            result_list = res.get("data", {}).get("result", [])
            if not result_list:
                return {"enrollment_id": enrollment.id, "status": "no_data"}

            try:
                val = float(result_list[0].get("value", [0, "0"])[1])
            except (ValueError, TypeError, IndexError):
                return {"enrollment_id": enrollment.id, "status": "invalid_value"}

        # Compare observation against bounds
        is_anomaly = (val > active_model.upper_bound) or (val < active_model.lower_bound)

        if is_anomaly:
            summary = (
                f"Statistical Anomaly on {enrollment.metric_name}: observed {val:.2f} "
                f"outside prediction bounds [{active_model.lower_bound:.2f}, {active_model.upper_bound:.2f}] "
                f"(expected: {active_model.baseline_expected:.2f}, model v{active_model.version})"
            )
            inc = incident_service.process_breach(
                db=db,
                detection_type="ANOMALY",
                source_id=enrollment.id,
                metric_name=enrollment.metric_name,
                labels=labels,
                severity="WARNING" if val <= (active_model.upper_bound * 1.5) else "CRITICAL",
                summary=summary,
                observed_value=val,
                expected_value=active_model.baseline_expected
            )
            return {
                "enrollment_id": enrollment.id,
                "status": "anomaly_detected",
                "incident_id": inc.id,
                "observed_value": val,
                "upper_bound": active_model.upper_bound,
                "lower_bound": active_model.lower_bound
            }
        else:
            inc = incident_service.process_normal(
                db=db,
                detection_type="ANOMALY",
                source_id=enrollment.id,
                metric_name=enrollment.metric_name,
                labels=labels,
                required_recoveries=2
            )
            return {
                "enrollment_id": enrollment.id,
                "status": "normal",
                "incident_resolved": inc.state == "RESOLVED" if inc else False,
                "observed_value": val
            }

    async def evaluate_all_enrollments(self, db: Session) -> List[Dict[str, Any]]:
        """Evaluate all trained and enabled metric enrollments."""
        enrollments = db.query(MetricEnrollment).filter(
            MetricEnrollment.enabled.is_(True),
            MetricEnrollment.model_status == "TRAINED"
        ).all()
        results = []
        for e in enrollments:
            res = await self.evaluate_enrollment(db, e)
            results.append(res)
        return results


anomaly_evaluator = AnomalyEvaluationService()
