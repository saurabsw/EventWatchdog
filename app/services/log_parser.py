import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
from app.core.schemas import MetricSample, normalize_to_utc

logger = logging.getLogger(__name__)

# Standard Syslog / Common Log Pattern
# Format: 2026-10-11T12:00:00Z [INFO] [order-service] Processed order #123 (duration_ms=45.2, status=200)
SYSLOG_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+\[(?P<level>[A-Za-z]+)\]\s+\[(?P<service>[A-Za-z0-9_\-]+)\]\s+(?P<message>.*)$"
)

# Extract key-value hints from log text (e.g., status=200, duration_ms=45.2, error_code=TIMEOUT)
KV_PATTERN = re.compile(r"([a-zA-Z_]+)=([a-zA-Z0-9_\-\.]+)")


class LogParserService:
    """
    Parses application logs in structured JSON or standard syslog/text format,
    normalizing recognized events into canonical MetricSamples.
    Malformed and unparseable lines are counted and converted into parse error metrics.
    """

    def parse_single_line(self, line: str) -> Tuple[List[MetricSample], Optional[str]]:
        """Parse a single text line or JSON line."""
        line = line.strip()
        if not line:
            return [], None

        # 1. Attempt JSON parse
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    return self.parse_json_record(data)
            except Exception as e:
                return [], f"Invalid JSON syntax: {str(e)[:100]}"

        # 2. Attempt Syslog/standard text pattern parse
        match = SYSLOG_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            try:
                ts = normalize_to_utc(groups["timestamp"])
            except Exception:
                ts = datetime.now(timezone.utc)

            level = groups["level"].upper()
            service = groups["service"].lower()
            msg = groups["message"]

            samples: List[MetricSample] = []
            bounded_labels = {"service": service, "level": level, "source": "log_parser"}

            # Event count metric
            samples.append(MetricSample(
                metric="app_log_events_total",
                timestamp=ts,
                value=1.0,
                labels=bounded_labels
            ))

            # Error metric if severity is error/fatal
            if level in ("ERROR", "FATAL", "CRITICAL"):
                samples.append(MetricSample(
                    metric="app_log_errors_total",
                    timestamp=ts,
                    value=1.0,
                    labels={"service": service, "level": level, "source": "log_parser"}
                ))

            # Extract numeric indicators if present in msg (e.g., duration_ms, status)
            for k, v in KV_PATTERN.findall(msg):
                k_lower = k.lower()
                if k_lower in ("duration_ms", "latency_ms", "response_time_ms"):
                    try:
                        dur_val = float(v)
                        samples.append(MetricSample(
                            metric="app_request_duration_ms",
                            timestamp=ts,
                            value=dur_val,
                            labels={"service": service, "source": "log_parser"}
                        ))
                    except ValueError:
                        pass
                elif k_lower in ("status", "status_code"):
                    try:
                        status_code = int(v)
                        if status_code >= 400:
                            samples.append(MetricSample(
                                metric="app_http_errors_total",
                                timestamp=ts,
                                value=1.0,
                                labels={"service": service, "status_code": str(status_code), "source": "log_parser"}
                            ))
                    except ValueError:
                        pass

            return samples, None

        # 3. Line does not match any recognized format
        return [], "Line format does not match recognized JSON or syslog pattern"

    def parse_json_record(self, data: Dict[str, Any]) -> Tuple[List[MetricSample], Optional[str]]:
        """Parse structured JSON log dictionary."""
        # Validate or default timestamp
        raw_ts = data.get("timestamp") or data.get("time") or data.get("@timestamp")
        try:
            ts = normalize_to_utc(raw_ts) if raw_ts else datetime.now(timezone.utc)
        except Exception as e:
            return [], f"Invalid timestamp: {str(e)[:100]}"

        # Service and level
        service = str(data.get("service") or data.get("app") or "unknown").strip().lower()[:64]
        level = str(data.get("level") or data.get("severity") or "INFO").strip().upper()[:16]

        samples: List[MetricSample] = []
        bounded_labels = {"service": service, "level": level, "source": "log_parser"}

        # Log event count
        samples.append(MetricSample(
            metric="app_log_events_total",
            timestamp=ts,
            value=1.0,
            labels=bounded_labels
        ))

        # Error count
        if level in ("ERROR", "FATAL", "CRITICAL"):
            samples.append(MetricSample(
                metric="app_log_errors_total",
                timestamp=ts,
                value=1.0,
                labels=bounded_labels
            ))

        # Check for duration / latency numeric values
        for dur_key in ("duration_ms", "latency_ms", "response_time_ms", "elapsed_ms"):
            if dur_key in data:
                try:
                    val = float(data[dur_key])
                    samples.append(MetricSample(
                        metric="app_request_duration_ms",
                        timestamp=ts,
                        value=val,
                        labels={"service": service, "source": "log_parser"}
                    ))
                    break
                except (ValueError, TypeError):
                    pass

        # Check for HTTP status code
        status_code = data.get("status_code") or data.get("status")
        if status_code is not None:
            try:
                sc = int(status_code)
                if sc >= 400:
                    samples.append(MetricSample(
                        metric="app_http_errors_total",
                        timestamp=ts,
                        value=1.0,
                        labels={"service": service, "status_code": str(sc), "source": "log_parser"}
                    ))
            except (ValueError, TypeError):
                pass

        return samples, None

    def process_batch(self, items: List[Any]) -> Tuple[List[MetricSample], int, List[str]]:
        """
        Process a mixed batch of JSON objects or string lines.
        Returns: (metrics_list, parse_error_count, error_messages)
        """
        all_metrics: List[MetricSample] = []
        parse_errors = 0
        reasons: List[str] = []

        now = datetime.now(timezone.utc)

        for item in items:
            if isinstance(item, dict):
                metrics, err = self.parse_json_record(item)
            elif isinstance(item, str):
                metrics, err = self.parse_single_line(item)
            else:
                metrics, err = [], f"Unsupported entry type: {type(item).__name__}"

            if err:
                parse_errors += 1
                if len(reasons) < 5:  # Cap recorded reasons
                    reasons.append(err)
                # Count the parse error as an observability metric
                all_metrics.append(MetricSample(
                    metric="app_log_parse_errors_total",
                    timestamp=now,
                    value=1.0,
                    labels={"service": "unknown", "source": "log_parser", "format": "unsupported"}
                ))
            else:
                all_metrics.extend(metrics)

        return all_metrics, parse_errors, reasons


log_parser = LogParserService()
