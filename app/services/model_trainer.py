import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from app.db.models import MetricEnrollment, ModelMetadata, AuditLog
from app.core.tsdb_client import tsdb_client
from app.services.anomaly_stats import StatisticalModelBaseline

logger = logging.getLogger(__name__)


def hash_labels(labels: Dict[str, str]) -> str:
    """Create deterministic SHA-256 hash for metric labels."""
    sorted_labels = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return hashlib.sha256(sorted_labels.encode("utf-8")).hexdigest()[:16]


class ModelTrainingService:
    """Trains and manages statistical anomaly baselines."""

    async def train_model_for_enrollment(
        self,
        db: Session,
        enrollment_id: int,
        custom_samples: Optional[List[Tuple[int, float]]] = None
    ) -> ModelMetadata:
        """
        Retrieves history (2,000 or 4,000 observations) from TSDB or synthetic source,
        computes baseline, updates enrollment status, and saves ModelMetadata.
        """
        enrollment = db.query(MetricEnrollment).filter(MetricEnrollment.id == enrollment_id).first()
        if not enrollment:
            raise ValueError(f"Metric enrollment {enrollment_id} not found")

        labels = json.loads(enrollment.labels_json) if enrollment.labels_json else {}

        raw_points: List[Tuple[int, float]] = []

        if custom_samples:
            raw_points = custom_samples
        else:
            # Query VictoriaMetrics for historical range
            # Calculate time range based on history_size * 10s (standard interval)
            history_seconds = enrollment.history_size * 15
            end_s = int(datetime.now(timezone.utc).timestamp())
            start_s = end_s - history_seconds

            filter_parts = [f'{k}="{v}"' for k, v in labels.items()]
            filter_str = "{" + ",".join(filter_parts) + "}" if filter_parts else ""
            query = f"{enrollment.metric_name}{filter_str}"

            res = await tsdb_client.query_range(query=query, start=start_s, end=end_s, step="15s")
            result_list = res.get("data", {}).get("result", [])
            if result_list:
                for item in result_list:
                    values = item.get("values", [])
                    for pt in values:
                        try:
                            raw_points.append((int(pt[0]), float(pt[1])))
                        except (ValueError, TypeError):
                            continue

        # Clean, sort, deduplicate timestamps
        cleaned_values = StatisticalModelBaseline.clean_and_sort_samples(raw_points)

        try:
            fit_result = StatisticalModelBaseline.fit(
                values=cleaned_values,
                strategy=enrollment.model_strategy,
                multiplier=enrollment.bound_multiplier,
                min_samples=50
            )

            # Determine latest version
            last_model = db.query(ModelMetadata).filter(
                ModelMetadata.enrollment_id == enrollment.id
            ).order_by(ModelMetadata.version.desc()).first()
            next_version = (last_model.version + 1) if last_model else 1

            now = datetime.now(timezone.utc)
            metadata = ModelMetadata(
                enrollment_id=enrollment.id,
                version=next_version,
                strategy=enrollment.model_strategy,
                baseline_expected=fit_result["baseline_expected"],
                scale_factor=fit_result["scale_factor"],
                upper_bound=fit_result["upper_bound"],
                lower_bound=fit_result["lower_bound"],
                sample_count=fit_result["sample_count"],
                training_start=now - timedelta(seconds=len(cleaned_values) * 15),
                training_end=now
            )
            db.add(metadata)

            enrollment.model_status = "TRAINED"
            enrollment.status_message = fit_result["message"]
            enrollment.last_trained_at = now
            db.commit()
            db.refresh(metadata)

            # Audit record
            audit = AuditLog(
                entity_type="MODEL",
                entity_id=str(metadata.id),
                action="TRAIN",
                details_json=json.dumps({
                    "enrollment_id": enrollment.id,
                    "version": next_version,
                    "upper_bound": metadata.upper_bound,
                    "lower_bound": metadata.lower_bound,
                    "sample_count": metadata.sample_count
                })
            )
            db.add(audit)
            db.commit()

            return metadata

        except Exception as e:
            enrollment.model_status = "FAILED"
            enrollment.status_message = str(e)[:250]
            db.commit()
            raise e


model_trainer = ModelTrainingService()
