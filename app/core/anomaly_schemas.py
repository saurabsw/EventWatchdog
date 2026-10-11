import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ModelEnrollmentCreate(BaseModel):
    metric_name: str = Field(..., max_length=128)
    labels: Dict[str, str] = Field(default_factory=dict)
    model_strategy: str = Field("robust_mad", description="robust_mad or rolling_zscore")
    history_size: int = Field(2000, description="2000 or 4000 observations")
    bound_multiplier: float = Field(3.0, ge=1.0, le=10.0)
    enabled: bool = True

    @field_validator("model_strategy")
    def validate_strategy(cls, v: str) -> str:
        if v not in ("robust_mad", "rolling_zscore"):
            raise ValueError("Supported strategies: 'robust_mad' or 'rolling_zscore'")
        return v

    @field_validator("history_size")
    def validate_history(cls, v: int) -> int:
        if v not in (2000, 4000):
            raise ValueError("Supported history sizes are exactly 2000 or 4000 observations")
        return v


class ModelEnrollmentUpdate(BaseModel):
    model_strategy: Optional[str] = None
    history_size: Optional[int] = None
    bound_multiplier: Optional[float] = None
    enabled: Optional[bool] = None


class ModelMetadataResponse(BaseModel):
    id: int
    enrollment_id: int
    version: int
    strategy: str
    baseline_expected: float
    scale_factor: float
    upper_bound: float
    lower_bound: float
    sample_count: int
    training_start: datetime
    training_end: datetime
    created_at: datetime


class ModelEnrollmentResponse(BaseModel):
    id: int
    metric_name: str
    labels: Dict[str, str]
    model_strategy: str
    history_size: int
    bound_multiplier: float
    enabled: bool
    last_trained_at: Optional[datetime]
    model_status: str
    status_message: Optional[str]
    active_model: Optional[ModelMetadataResponse] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, e: Any, active_model: Optional[Any] = None) -> "ModelEnrollmentResponse":
        labels = {}
        if e.labels_json:
            try:
                labels = json.loads(e.labels_json)
            except Exception:
                pass

        model_resp = None
        if active_model:
            model_resp = ModelMetadataResponse(
                id=active_model.id,
                enrollment_id=active_model.enrollment_id,
                version=active_model.version,
                strategy=active_model.strategy,
                baseline_expected=active_model.baseline_expected,
                scale_factor=active_model.scale_factor,
                upper_bound=active_model.upper_bound,
                lower_bound=active_model.lower_bound,
                sample_count=active_model.sample_count,
                training_start=active_model.training_start,
                training_end=active_model.training_end,
                created_at=active_model.created_at
            )

        return cls(
            id=e.id,
            metric_name=e.metric_name,
            labels=labels,
            model_strategy=e.model_strategy,
            history_size=e.history_size,
            bound_multiplier=e.bound_multiplier,
            enabled=e.enabled,
            last_trained_at=e.last_trained_at,
            model_status=e.model_status,
            status_message=e.status_message,
            active_model=model_resp,
            created_at=e.created_at,
            updated_at=e.updated_at
        )


class TrainModelRequest(BaseModel):
    enrollment_id: int
