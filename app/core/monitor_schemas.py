import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class MonitorCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = Field(None, max_length=256)
    metric_name: str = Field(..., max_length=128)
    label_filters: Dict[str, str] = Field(default_factory=dict)
    evaluation_window_seconds: int = Field(60, ge=15, le=86400)
    aggregation_func: str = Field("avg", description="avg, min, max, count, sum")
    comparison_operator: str = Field(..., description=">, >=, <, <=, ==, !=")
    threshold: float
    severity: str = Field("WARNING", description="INFO, WARNING, CRITICAL")
    consecutive_breaches: int = Field(1, ge=1)
    consecutive_recoveries: int = Field(2, ge=1)
    enabled: bool = True

    @field_validator("comparison_operator")
    def validate_op(cls, v: str) -> str:
        if v not in (">", ">=", "<", "<=", "==", "!="):
            raise ValueError(f"Unsupported comparison operator '{v}'")
        return v

    @field_validator("aggregation_func")
    def validate_agg(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in ("avg", "min", "max", "count", "sum"):
            raise ValueError(f"Unsupported aggregation function '{v}'")
        return v_lower


class MonitorUpdate(BaseModel):
    description: Optional[str] = None
    threshold: Optional[float] = None
    comparison_operator: Optional[str] = None
    evaluation_window_seconds: Optional[int] = None
    consecutive_breaches: Optional[int] = None
    consecutive_recoveries: Optional[int] = None
    enabled: Optional[bool] = None


class MonitorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    metric_name: str
    label_filters: Dict[str, str]
    evaluation_window_seconds: int
    aggregation_func: str
    comparison_operator: str
    threshold: float
    severity: str
    consecutive_breaches: int
    consecutive_recoveries: int
    enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_orm_model(cls, m: Any) -> "MonitorResponse":
        labels = {}
        if m.label_filters_json:
            try:
                labels = json.loads(m.label_filters_json)
            except Exception:
                pass
        return cls(
            id=m.id,
            name=m.name,
            description=m.description,
            metric_name=m.metric_name,
            label_filters=labels,
            evaluation_window_seconds=m.evaluation_window_seconds,
            aggregation_func=m.aggregation_func,
            comparison_operator=m.comparison_operator,
            threshold=m.threshold,
            severity=m.severity,
            consecutive_breaches=m.consecutive_breaches,
            consecutive_recoveries=m.consecutive_recoveries,
            enabled=m.enabled,
            created_at=m.created_at,
            updated_at=m.updated_at
        )


class IncidentResponse(BaseModel):
    id: int
    fingerprint: str
    detection_type: str
    source_id: Optional[int]
    metric_name: str
    labels: Dict[str, str]
    severity: str
    state: str
    summary: str
    latest_value: Optional[float]
    expected_value: Optional[float]
    occurrence_count: int
    consecutive_normal_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    @classmethod
    def from_orm_model(cls, m: Any) -> "IncidentResponse":
        labels = {}
        if m.labels_json:
            try:
                labels = json.loads(m.labels_json)
            except Exception:
                pass
        return cls(
            id=m.id,
            fingerprint=m.fingerprint,
            detection_type=m.detection_type,
            source_id=m.source_id,
            metric_name=m.metric_name,
            labels=labels,
            severity=m.severity,
            state=m.state,
            summary=m.summary,
            latest_value=m.latest_value,
            expected_value=m.expected_value,
            occurrence_count=m.occurrence_count,
            consecutive_normal_count=m.consecutive_normal_count,
            first_seen_at=m.first_seen_at,
            last_seen_at=m.last_seen_at,
            acknowledged_at=m.acknowledged_at,
            resolved_at=m.resolved_at
        )
