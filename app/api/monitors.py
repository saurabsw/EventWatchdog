import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import MonitorRule, AuditLog
from app.core.monitor_schemas import MonitorCreate, MonitorUpdate, MonitorResponse

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get("", response_model=List[MonitorResponse])
def list_monitors(enabled_only: bool = False, db: Session = Depends(get_db)):
    """List static threshold rules."""
    query = db.query(MonitorRule)
    if enabled_only:
        query = query.filter(MonitorRule.enabled.is_(True))
    monitors = query.all()
    return [MonitorResponse.from_orm_model(m) for m in monitors]


@router.post("", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
def create_monitor(payload: MonitorCreate, db: Session = Depends(get_db)):
    """Create a new static threshold rule."""
    existing = db.query(MonitorRule).filter(MonitorRule.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Monitor rule with name '{payload.name}' already exists"
        )

    rule = MonitorRule(
        name=payload.name,
        description=payload.description,
        metric_name=payload.metric_name,
        label_filters_json=json.dumps(payload.label_filters),
        evaluation_window_seconds=payload.evaluation_window_seconds,
        aggregation_func=payload.aggregation_func,
        comparison_operator=payload.comparison_operator,
        threshold=payload.threshold,
        severity=payload.severity,
        consecutive_breaches=payload.consecutive_breaches,
        consecutive_recoveries=payload.consecutive_recoveries,
        enabled=payload.enabled
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Audit log
    audit = AuditLog(
        entity_type="MONITOR",
        entity_id=str(rule.id),
        action="CREATE",
        details_json=json.dumps(payload.model_dump())
    )
    db.add(audit)
    db.commit()

    return MonitorResponse.from_orm_model(rule)


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db)):
    """Retrieve a monitor rule by ID."""
    rule = db.query(MonitorRule).filter(MonitorRule.id == monitor_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Monitor rule not found")
    return MonitorResponse.from_orm_model(rule)


@router.patch("/{monitor_id}", response_model=MonitorResponse)
def update_monitor(monitor_id: int, payload: MonitorUpdate, db: Session = Depends(get_db)):
    """Update fields of an existing monitor rule."""
    rule = db.query(MonitorRule).filter(MonitorRule.id == monitor_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Monitor rule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(rule, k, v)

    db.commit()
    db.refresh(rule)

    audit = AuditLog(
        entity_type="MONITOR",
        entity_id=str(rule.id),
        action="UPDATE",
        details_json=json.dumps(update_data)
    )
    db.add(audit)
    db.commit()

    return MonitorResponse.from_orm_model(rule)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    """Delete a monitor rule."""
    rule = db.query(MonitorRule).filter(MonitorRule.id == monitor_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Monitor rule not found")

    db.delete(rule)
    db.commit()

    audit = AuditLog(
        entity_type="MONITOR",
        entity_id=str(monitor_id),
        action="DELETE",
        details_json="{}"
    )
    db.add(audit)
    db.commit()
    return None
