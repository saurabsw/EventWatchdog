import pytest
from datetime import datetime, timezone
from app.services.log_parser import log_parser


def test_parse_valid_json_log():
    record = {
        "timestamp": "2026-10-11T12:00:00Z",
        "level": "ERROR",
        "service": "checkout-service",
        "message": "Payment processing failed",
        "duration_ms": 145.5,
        "status_code": 500
    }
    metrics, err = log_parser.parse_json_record(record)
    assert err is None
    metric_names = [m.metric for m in metrics]

    assert "app_log_events_total" in metric_names
    assert "app_log_errors_total" in metric_names
    assert "app_request_duration_ms" in metric_names
    assert "app_http_errors_total" in metric_names

    duration_metric = next(m for m in metrics if m.metric == "app_request_duration_ms")
    assert duration_metric.value == 145.5
    assert duration_metric.labels["service"] == "checkout-service"


def test_parse_valid_syslog_line():
    line = '2026-10-11T12:05:00Z [INFO] [auth-api] Token refreshed successfully duration_ms=25.0 status=200'
    metrics, err = log_parser.parse_single_line(line)
    assert err is None
    metric_names = [m.metric for m in metrics]

    assert "app_log_events_total" in metric_names
    assert "app_request_duration_ms" in metric_names
    assert "app_log_errors_total" not in metric_names  # INFO level should not trigger errors_total


def test_parse_malformed_log_line():
    line = 'Malformed random non-log string with no structure'
    metrics, err = log_parser.parse_single_line(line)
    assert err is not None
    assert len(metrics) == 0


def test_batch_processing_with_malformed_records():
    batch = [
        {"timestamp": "2026-10-11T12:00:00Z", "level": "INFO", "service": "api", "message": "ok"},
        "Malformed plain text garbage",
        {"timestamp": "invalid_date_format", "level": "WARN", "service": "db", "message": "warn"}
    ]
    metrics, parse_errors, reasons = log_parser.process_batch(batch)

    # 1 valid, 2 invalid
    assert parse_errors == 2
    assert len(reasons) == 2
    # Check that error counter metric was generated for observability
    error_metrics = [m for m in metrics if m.metric == "app_log_parse_errors_total"]
    assert len(error_metrics) == 2
