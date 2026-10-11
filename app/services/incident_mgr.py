import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Incident, AuditLog

logger = logging.getLogger(__name__)


def generate_fingerprint(
    detection_type: str,
    source_id: Optional[int],
    metric_name: str,
    labels: Dict[str, str]
) -> str:
    """
    Generate a stable, deterministic fingerprint hash for incident deduplication.
    SHA-256(detection_type:source_id:metric_name:sorted_labels)
    """
    sorted_labels = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    raw_key = f"{detection_type}:{source_id or 0}:{metric_name}:{sorted_labels}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class NotificationAdapter:
    """
    Simulated webhook and logging notification adapter.
    Dispatches alerts without requiring an external messaging provider.
    """

    def send_notification(self, event_type: str, incident: Incident):
        logger.info(
            "[NOTIFICATION %s] Incident ID=%s Fingerprint=%s Metric=%s Severity=%s State=%s Summary=%s",
            event_type, incident.id, incident.fingerprint[:12],
            incident.metric_name, incident.severity, incident.state, incident.summary
        )


notification_adapter = NotificationAdapter()


class IncidentService:
    """Manages the full lifecycle of monitoring incidents with deduplication and auto-recovery."""

    def process_breach(
        self,
        db: Session,
        detection_type: str,
        source_id: Optional[int],
        metric_name: str,
        labels: Dict[str, str],
        severity: str,
        summary: str,
        observed_value: float,
        expected_value: Optional[float] = None
    ) -> Incident:
        """
        Record a breach detection.
        If an open or acknowledged incident with the same fingerprint exists, update it.
        Otherwise, create a new incident.
        """
        fingerprint = generate_fingerprint(detection_type, source_id, metric_name, labels)
        now = datetime.now(timezone.utc)

        incident = db.query(Incident).filter(
            Incident.fingerprint == fingerprint,
            Incident.state.in_(["OPEN", "ACKNOWLEDGED"])
        ).first()

        if incident:
            # Deduplicate continuing breach: increment count and update last_seen
            incident.occurrence_count += 1
            incident.last_seen_at = now
            incident.latest_value = observed_value
            incident.consecutive_normal_count = 0  # reset recovery counter
            db.commit()
            db.refresh(incident)

            # Audit log for repeated occurrence
            self._audit(
                db, "INCIDENT", str(incident.id), "BREACH_RECURRENCE",
                {"occurrence_count": incident.occurrence_count, "value": observed_value}
            )
            return incident

        # Create new incident
        new_incident = Incident(
            fingerprint=fingerprint,
            detection_type=detection_type,
            source_id=source_id,
            metric_name=metric_name,
            labels_json=json.dumps(labels, sort_keys=True),
            severity=severity,
            state="OPEN",
            summary=summary,
            latest_value=observed_value,
            expected_value=expected_value,
            occurrence_count=1,
            consecutive_normal_count=0,
            first_seen_at=now,
            last_seen_at=now
        )
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)

        self._audit(
            db, "INCIDENT", str(new_incident.id), "CREATE",
            {"summary": summary, "severity": severity, "value": observed_value}
        )
        notification_adapter.send_notification("OPENED", new_incident)
        return new_incident

    def acknowledge_incident(self, db: Session, incident_id: int) -> Optional[Incident]:
        """Acknowledge an open incident."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident or incident.state == "RESOLVED":
            return None

        incident.state = "ACKNOWLEDGED"
        incident.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(incident)

        self._audit(db, "INCIDENT", str(incident.id), "ACKNOWLEDGE", {"state": incident.state})
        notification_adapter.send_notification("ACKNOWLEDGED", incident)
        return incident

    def process_normal(
        self,
        db: Session,
        detection_type: str,
        source_id: Optional[int],
        metric_name: str,
        labels: Dict[str, str],
        required_recoveries: int = 2
    ) -> Optional[Incident]:
        """
        Record a healthy/normal evaluation.
        Increments normal count and auto-resolves if normal count >= required_recoveries.
        """
        fingerprint = generate_fingerprint(detection_type, source_id, metric_name, labels)
        incident = db.query(Incident).filter(
            Incident.fingerprint == fingerprint,
            Incident.state.in_(["OPEN", "ACKNOWLEDGED"])
        ).first()

        if not incident:
            return None

        incident.consecutive_normal_count += 1
        if incident.consecutive_normal_count >= required_recoveries:
            incident.state = "RESOLVED"
            incident.resolved_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(incident)

            self._audit(
                db, "INCIDENT", str(incident.id), "RESOLVE",
                {"consecutive_normal": incident.consecutive_normal_count}
            )
            notification_adapter.send_notification("RESOLVED", incident)
            return incident

        db.commit()
        db.refresh(incident)
        return incident

    def _audit(self, db: Session, entity_type: str, entity_id: str, action: str, details: Dict[str, Any]):
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details_json=json.dumps(details)
        )
        db.add(log)
        db.commit()


incident_service = IncidentService()
