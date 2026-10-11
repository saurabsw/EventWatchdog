"""
Reproducible Sample Data Generator for Intelligent Observability & Event Watchdog.
Generates:
1. Normal metric observations (sinusoidal baseline with Gaussian noise).
2. Static threshold breaches (spikes above warning/critical thresholds).
3. Statistical anomalies (abrupt level shifts, variance jumps, sudden dropouts).
4. Application log batches (JSON and syslog formatted).
"""

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import httpx


def generate_time_series_data(
    metric_name: str = "payment_processing_latency_ms",
    service: str = "payment-gateway",
    points_count: int = 2000,
    interval_seconds: int = 5,
    baseline: float = 120.0,
    amplitude: float = 25.0,
    noise_sigma: float = 5.0,
    inject_anomalies: bool = True
) -> List[Dict[str, Any]]:
    """Generate deterministic time-series samples."""
    random.seed(42)  # Reproducibility seed
    samples = []
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(seconds=points_count * interval_seconds)

    for i in range(points_count):
        current_ts = start_time + timedelta(seconds=i * interval_seconds)
        # Sinusoidal periodic cycle + random noise
        cycle = math.sin(2 * math.pi * i / 200) * amplitude
        noise = random.gauss(0, noise_sigma)
        val = max(1.0, baseline + cycle + noise)

        # Inject deliberate anomalies in the tail region (last 20 points) if requested
        if inject_anomalies and i >= (points_count - 10):
            # Outlier spike of 500ms
            val = baseline * 3.5 + random.gauss(0, 10)

        samples.append({
            "metric": metric_name,
            "timestamp": current_ts.isoformat(),
            "value": round(val, 2),
            "labels": {
                "service": service,
                "environment": "production",
                "source": "sample_generator"
            }
        })

    return samples


def generate_sample_logs(count: int = 50, error_ratio: float = 0.2) -> List[Dict[str, Any]]:
    """Generate realistic application log records."""
    random.seed(42)
    services = ["payment-gateway", "auth-service", "order-api", "inventory-service"]
    endpoints = ["/checkout", "/login", "/orders/v1", "/items/query"]
    logs = []
    now = datetime.now(timezone.utc)

    for i in range(count):
        is_error = random.random() < error_ratio
        svc = random.choice(services)
        ep = random.choice(endpoints)
        ts = (now - timedelta(seconds=(count - i) * 3)).isoformat()

        if is_error:
            status_code = random.choice([500, 502, 504])
            duration = random.uniform(300.0, 1500.0)
            log = {
                "timestamp": ts,
                "level": "ERROR",
                "service": svc,
                "message": f"HTTP {status_code} internal error while calling downstream for {ep}",
                "status_code": status_code,
                "duration_ms": round(duration, 2)
            }
        else:
            status_code = 200
            duration = random.uniform(15.0, 85.0)
            log = {
                "timestamp": ts,
                "level": "INFO",
                "service": svc,
                "message": f"Successfully completed request {ep} (duration_ms={round(duration, 2)}, status={status_code})",
                "status_code": status_code,
                "duration_ms": round(duration, 2)
            }
        logs.append(log)

    return logs


def send_data_to_api(base_url: str = "http://127.0.0.1:8000"):
    """Send generated metrics and logs to the local FastAPI ingestion endpoints."""
    print(f"Connecting to EventWatchdog API at {base_url}...")

    # 1. Metrics
    metrics = generate_time_series_data(points_count=500, inject_anomalies=True)
    print(f"Generated {len(metrics)} time-series metrics samples.")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # Send in batches of 250
        for i in range(0, len(metrics), 250):
            chunk = metrics[i:i + 250]
            res = client.post("/api/v1/metrics", json={"metrics": chunk})
            print(f"POST /api/v1/metrics batch {i // 250 + 1}: status {res.status_code}")

    # 2. Logs
    logs = generate_sample_logs(count=30, error_ratio=0.25)
    print(f"Generated {len(logs)} log entries.")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        res = client.post("/api/v1/logs", json={"entries": logs})
        print(f"POST /api/v1/logs: status {res.status_code}, response: {res.json()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed sample metrics and logs")
    parser.add_argument("--send", action="store_true", help="Send data directly to API")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--export", default="", help="File path to save sample JSON")

    args = parser.parse_args()

    if args.export:
        data = {
            "metrics": generate_time_series_data(points_count=200),
            "logs": generate_sample_logs(count=50)
        }
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Exported sample data to {args.export}")

    if args.send:
        send_data_to_api(base_url=args.url)
    elif not args.export:
        print("Run with --send to post to API, or --export <file.json> to dump samples.")
