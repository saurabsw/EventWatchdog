import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import MetricEnrollment, ModelMetadata, AuditLog
from app.core.anomaly_schemas import (
    ModelEnrollmentCreate, ModelEnrollmentUpdate, ModelEnrollmentResponse,
    ModelMetadataResponse, TrainModelRequest
)
from app.services.model_trainer import model_trainer, hash_labels

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=List[ModelEnrollmentResponse])
def list_enrollments(enabled_only: bool = False, db: Session = Depends(get_db)):
    """List metric series enrolled for anomaly detection."""
    query = db.query(MetricEnrollment)
    if enabled_only:
        query = query.filter(MetricEnrollment.enabled.is_(True))
    enrollments = query.all()

    responses = []
    for e in enrollments:
        active_model = db.query(ModelMetadata).filter(
            ModelMetadata.enrollment_id == e.id
        ).order_by(ModelMetadata.version.desc()).first()
        responses.append(ModelEnrollmentResponse.from_orm(e, active_model))
    return responses


@router.post("", response_model=ModelEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_metric_series(payload: ModelEnrollmentCreate, db: Session = Depends(get_db)):
    """Enroll a metric series for statistical anomaly detection."""
    lbl_hash = hash_labels(payload.labels)
    existing = db.query(MetricEnrollment).filter(
        MetricEnrollment.metric_name == payload.metric_name,
        MetricEnrollment.labels_hash == lbl_hash
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This metric series and label combination is already enrolled"
        )

    enrollment = MetricEnrollment(
        metric_name=payload.metric_name,
        labels_hash=lbl_hash,
        labels_json=json.dumps(payload.labels, sort_keys=True),
        model_strategy=payload.model_strategy,
        history_size=payload.history_size,
        bound_multiplier=payload.bound_multiplier,
        enabled=payload.enabled,
        model_status="PENDING",
        status_message="Enrolled. Awaiting initial training run."
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    audit = AuditLog(
        entity_type="MODEL_ENROLLMENT",
        entity_id=str(enrollment.id),
        action="ENROLL",
        details_json=json.dumps(payload.model_dump())
    )
    db.add(audit)
    db.commit()

    return ModelEnrollmentResponse.from_orm(enrollment)


@router.get("/{enrollment_id}", response_model=ModelEnrollmentResponse)
def get_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    """Get enrollment status and current active model."""
    enrollment = db.query(MetricEnrollment).filter(MetricEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    active_model = db.query(ModelMetadata).filter(
        ModelMetadata.enrollment_id == enrollment.id
    ).order_by(ModelMetadata.version.desc()).first()

    return ModelEnrollmentResponse.from_orm(enrollment, active_model)


@router.patch("/{enrollment_id}", response_model=ModelEnrollmentResponse)
def update_enrollment(enrollment_id: int, payload: ModelEnrollmentUpdate, db: Session = Depends(get_db)):
    """Update enrollment configuration (strategy, history size, multiplier, or enabled)."""
    enrollment = db.query(MetricEnrollment).filter(MetricEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(enrollment, k, v)

    db.commit()
    db.refresh(enrollment)

    active_model = db.query(ModelMetadata).filter(
        ModelMetadata.enrollment_id == enrollment.id
    ).order_by(ModelMetadata.version.desc()).first()

    return ModelEnrollmentResponse.from_orm(enrollment, active_model)


@router.post("/train", response_model=ModelMetadataResponse)
async def train_model(payload: TrainModelRequest, db: Session = Depends(get_db)):
    """Trigger training for an enrolled series over configured history (2000 or 4000)."""
    try:
        metadata = await model_trainer.train_model_for_enrollment(db, payload.enrollment_id)
        return ModelMetadataResponse(
            id=metadata.id,
            enrollment_id=metadata.enrollment_id,
            version=metadata.version,
            strategy=metadata.strategy,
            baseline_expected=metadata.baseline_expected,
            scale_factor=metadata.scale_factor,
            upper_bound=metadata.upper_bound,
            lower_bound=metadata.lower_bound,
            sample_count=metadata.sample_count,
            training_start=metadata.training_start,
            training_end=metadata.training_end,
            created_at=metadata.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Training error: {e}")
