from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import Incident, AuditLog
from app.core.monitor_schemas import IncidentResponse
from app.services.incident_mgr import incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    state: Optional[str] = Query(None, description="Filter by state: OPEN, ACKNOWLEDGED, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, CRITICAL"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List incidents with optional state and severity filtering."""
    query = db.query(Incident)
    if state:
        query = query.filter(Incident.state == state.upper())
    if severity:
        query = query.filter(Incident.severity == severity.upper())
    incidents = query.order_by(Incident.last_seen_at.desc()).limit(limit).all()
    return [IncidentResponse.from_orm_model(inc) for inc in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single incident."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.from_orm_model(inc)


@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(incident_id: int, db: Session = Depends(get_db)):
    """Acknowledge an active incident."""
    inc = incident_service.acknowledge_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found or already resolved")
    return IncidentResponse.from_orm_model(inc)


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(incident_id: int, db: Session = Depends(get_db)):
    """Manually resolve an active incident."""
    inc = incident_service.resolve_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found or already resolved")
    return IncidentResponse.from_orm_model(inc)


@router.get("/{incident_id}/audit")
def get_incident_audit(incident_id: int, db: Session = Depends(get_db)):
    """Retrieve audit trail for a specific incident."""
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "INCIDENT",
        AuditLog.entity_id == str(incident_id)
    ).order_by(AuditLog.timestamp.asc()).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "action": l.action,
            "details": l.details_json
        }
        for l in logs
    ]
