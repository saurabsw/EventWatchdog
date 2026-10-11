import math
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


METRIC_NAME_REGEX = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
LABEL_NAME_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Deny high-cardinality label keys to protect TSDB index performance
FORBIDDEN_LABEL_KEYS = {
    "trace_id", "span_id", "request_id", "req_id", "session_id", "user_id",
    "ip", "client_ip", "remote_addr", "stack_trace", "stacktrace", "message",
    "msg", "error_details", "payload", "query_string", "url", "path", "raw"
}


def normalize_to_utc(dt: Any) -> datetime:
    """Ensure timestamp is a timezone-aware UTC datetime."""
    if isinstance(dt, (int, float)):
        # Support epoch seconds or milliseconds
        if dt > 1e11:  # milliseconds
            dt = dt / 1000.0
        return datetime.fromtimestamp(dt, tz=timezone.utc)
    if isinstance(dt, str):
        # Strip trailing Z for fromisoformat compatibility in Python versions
        cleaned_str = dt.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned_str)
        except ValueError:
            raise ValueError(f"Invalid timestamp format '{dt}'. Expected ISO-8601 string.")
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise ValueError(f"Unsupported timestamp type: {type(dt)}")


class MetricSample(BaseModel):
    metric: str = Field(..., description="Canonical metric name matching ^[a-zA-Z_:][a-zA-Z0-9_:]*$")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    value: float = Field(..., description="Finite numeric measurement")
    labels: Dict[str, str] = Field(default_factory=dict, description="Bounded key-value string labels")

    @field_validator("metric")
    def validate_metric_name(cls, v: str) -> str:
        if not METRIC_NAME_REGEX.match(v):
            raise ValueError(f"Invalid metric name '{v}'. Must match regex {METRIC_NAME_REGEX.pattern}")
        return v

    @field_validator("value")
    def validate_finite_value(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Metric value must be a finite number (NaN and Infinity are not permitted)")
        return float(v)

    @field_validator("timestamp", mode="before")
    def validate_timestamp(cls, v: Any) -> datetime:
        return normalize_to_utc(v)

    @field_validator("labels")
    def validate_and_sanitize_labels(cls, v: Dict[str, Any]) -> Dict[str, str]:
        cleaned = {}
        for key, val in v.items():
            if not isinstance(key, str):
                continue
            k_clean = key.strip().lower()
            if not LABEL_NAME_REGEX.match(k_clean):
                continue
            if k_clean in FORBIDDEN_LABEL_KEYS:
                continue
            # Bounded length values only
            val_str = str(val).strip()
            if len(val_str) > 128:
                val_str = val_str[:128]
            cleaned[k_clean] = val_str
        return cleaned


class MetricBatch(BaseModel):
    metrics: List[MetricSample] = Field(..., max_length=10000, description="Batch of metric samples (up to 10,000)")


class MetricIngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: List[str] = Field(default_factory=list)


class RawLogRecord(BaseModel):
    timestamp: Optional[Any] = None
    level: Optional[str] = None
    service: Optional[str] = None
    message: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class LogBatchPayload(BaseModel):
    entries: Optional[List[Any]] = Field(default=None, description="Batch of JSON objects or log string lines")
    raw_lines: Optional[str] = Field(default=None, description="Multiline text of log entries")

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if not self.entries and not self.raw_lines:
            raise ValueError("Either 'entries' or 'raw_lines' must be provided")
        return self


class LogParseSummary(BaseModel):
    total_received: int
    parsed_metrics: int
    parse_errors: int
    metrics_generated: List[str]
    error_reasons: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, Any]
