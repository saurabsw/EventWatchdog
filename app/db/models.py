import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, Index
)
from app.core.database import Base


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class MonitorRule(Base):
    __tablename__ = "monitor_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(256), nullable=True)
    metric_name = Column(String(128), nullable=False, index=True)
    label_filters_json = Column(Text, nullable=True, default="{}")
    evaluation_window_seconds = Column(Integer, nullable=False, default=60)
    aggregation_func = Column(String(32), nullable=False, default="avg")  # avg, min, max, count, sum
    comparison_operator = Column(String(8), nullable=False)  # >, >=, <, <=, ==, !=
    threshold = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False, default="WARNING")  # INFO, WARNING, CRITICAL
    consecutive_breaches = Column(Integer, nullable=False, default=1)
    consecutive_recoveries = Column(Integer, nullable=False, default=2)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MetricEnrollment(Base):
    __tablename__ = "metric_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(128), nullable=False, index=True)
    labels_hash = Column(String(64), nullable=False, index=True)
    labels_json = Column(Text, nullable=False, default="{}")
    model_strategy = Column(String(32), nullable=False, default="robust_mad")  # rolling_zscore, robust_mad
    history_size = Column(Integer, nullable=False, default=2000)  # 2000 or 4000
    bound_multiplier = Column(Float, nullable=False, default=3.0)
    enabled = Column(Boolean, nullable=False, default=True)
    last_trained_at = Column(DateTime(timezone=True), nullable=True)
    model_status = Column(String(32), nullable=False, default="PENDING")  # PENDING, TRAINED, FAILED
    status_message = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    strategy = Column(String(32), nullable=False)
    baseline_expected = Column(Float, nullable=False)
    scale_factor = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False)
    training_start = Column(DateTime(timezone=True), nullable=False)
    training_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)
    detection_type = Column(String(32), nullable=False)  # STATIC, ANOMALY
    source_id = Column(Integer, nullable=True)  # rule_id or enrollment_id
    metric_name = Column(String(128), nullable=False, index=True)
    labels_json = Column(Text, nullable=False, default="{}")
    severity = Column(String(32), nullable=False, default="WARNING")
    state = Column(String(32), nullable=False, default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    summary = Column(String(512), nullable=False)
    latest_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    occurrence_count = Column(Integer, nullable=False, default=1)
    consecutive_normal_count = Column(Integer, nullable=False, default=0)
    first_seen_at = Column(DateTime(timezone=True), default=utcnow)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
    entity_type = Column(String(64), nullable=False)  # MONITOR, MODEL, INCIDENT, LOG_PARSER
    entity_id = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)  # CREATE, UPDATE, DELETE, ACKNOWLEDGE, RESOLVE, BREACH
    details_json = Column(Text, nullable=False, default="{}")
