import pytest
from datetime import datetime, timezone
from app.core.schemas import MetricSample, MetricBatch, RawLogRecord, LogBatchPayload


def test_valid_metric_sample():
    sample = MetricSample(
        metric="cpu_usage_total",
        value=42.5,
        labels={"host": "server-01", "environment": "prod"}
    )
    assert sample.metric == "cpu_usage_total"
    assert sample.value == 42.5
    assert sample.labels["host"] == "server-01"


def test_invalid_metric_name_rejected():
    with pytest.raises(ValueError):
        MetricSample(
            metric="123_invalid_metric!",
            value=10.0
        )


def test_nan_or_infinite_value_rejected():
    with pytest.raises(ValueError):
        MetricSample(
            metric="cpu_usage",
            value=float("nan")
        )
    with pytest.raises(ValueError):
        MetricSample(
            metric="cpu_usage",
            value=float("inf")
        )


def test_forbidden_high_cardinality_labels_stripped():
    sample = MetricSample(
        metric="api_requests_total",
        value=1.0,
        labels={
            "service": "checkout",
            "trace_id": "993489812409124",
            "request_id": "abc-123",
            "stack_trace": "line 42 error",
            "client_ip": "192.168.1.1"
        }
    )
    assert "service" in sample.labels
    assert "trace_id" not in sample.labels
    assert "request_id" not in sample.labels
    assert "stack_trace" not in sample.labels
    assert "client_ip" not in sample.labels


def test_raw_log_record_model():
    entry = RawLogRecord(
        level="ERROR",
        service="payment-service",
        message="Connection timeout to payment gateway",
        duration_ms=250.5
    )
    assert entry.level == "ERROR"
    assert entry.service == "payment-service"
    assert entry.duration_ms == 250.5
