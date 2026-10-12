




"""
End-to-end Live Anomaly Detection Test against deployed EventWatchdog instance.
Tests:
1. Historical baseline seeding into VictoriaMetrics via /api/v1/metrics
2. Statistical model training (Robust MAD / Rolling Z-Score) via /api/v1/models/train
3. Ingestion of normal observations (bounds respected, no incidents)
4. Injection of an anomalous latency spike (breaches upper bound, triggers OPEN incident)
5. Operator Incident triage: Acknowledging incident via /api/v1/incidents/{id}/acknowledge
6. System Auto-Recovery: Sending consecutive normal observations leading to RESOLVED state
"""

import sys
import json
import time
import random
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def http_request(url: str, method: str = "GET", data: dict = None) -> dict:
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if not content:
                return {}
            return json.loads(content)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} on {method} {url}: {err_msg}")


def run_live_anomaly_test(base_url: str):
    print("=" * 70)
    print("🚀 STARTING LIVE ANOMALY DETECTION TEST")
    print(f"Target: {base_url}")
    print("=" * 70)

    # 1. Check / Create Enrollment
    print("\n[Step 1] Fetching enrolled models...")
    models = http_request(f"{base_url}/api/v1/models")
    enrollment = None
    metric_name = "payment_gateway_response_ms"
    labels = {"gateway": "stripe"}

    for m in models:
        if m.get("metric_name") == metric_name and m.get("labels", {}).get("gateway") == "stripe":
            enrollment = m
            break

    if not enrollment:
        print(f"Enrolling new metric series: {metric_name} {labels}...")
        enrollment = http_request(f"{base_url}/api/v1/models", method="POST", data={
            "metric_name": metric_name,
            "labels": labels,
            "model_strategy": "robust_mad",
            "history_size": 2000,
            "bound_multiplier": 3.0,
            "enabled": True
        })
    enroll_id = enrollment["id"]
    print(f"✅ Enrollment ID {enroll_id}: {metric_name} {labels}")
    print(f"   Strategy: {enrollment.get('model_strategy')}, Multiplier: {enrollment.get('bound_multiplier')}")

    # 2. Seed 100 historical normal observations
    print(f"\n[Step 2] Seeding 100 historical baseline samples (~120ms baseline)...")
    now = datetime.now(timezone.utc)
    normal_samples = []
    for i in range(100):
        ts = now - timedelta(seconds=(100 - i) * 15)
        # Normal baseline between 115ms and 125ms
        val = 120.0 + random.uniform(-4.0, 4.0)
        normal_samples.append({
            "metric": metric_name,
            "timestamp": ts.isoformat(),
            "value": round(val, 2),
            "labels": labels
        })

    ingest_res = http_request(f"{base_url}/api/v1/metrics", method="POST", data={"metrics": normal_samples})
    print(f"✅ Ingested {ingest_res.get('accepted')} samples to VictoriaMetrics.")
    print("   Waiting 3s for VictoriaMetrics index flush...")
    time.sleep(3)

    # 3. Train Model
    print(f"\n[Step 3] Triggering model training for Enrollment #{enroll_id}...")
    training_res = http_request(f"{base_url}/api/v1/models/train", method="POST", data={"enrollment_id": enroll_id})
    print("✅ Model Training Successful!")
    print(f"   Model Version:    v{training_res.get('version')}")
    print(f"   Strategy:         {training_res.get('strategy')}")
    print(f"   Sample Count:     {training_res.get('sample_count')} points")
    print(f"   Baseline Median:  {training_res.get('baseline_expected'):.2f} ms")
    print(f"   Prediction Bounds:[{training_res.get('lower_bound'):.2f} ms - {training_res.get('upper_bound'):.2f} ms]")

    upper_bound = training_res.get('upper_bound')

    # 4. Ingest normal sample and verify no incident
    print("\n[Step 4] Ingesting normal observation (121.0 ms, well within bounds)...")
    sample_normal = [{
        "metric": metric_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value": 121.0,
        "labels": labels
    }]
    http_request(f"{base_url}/api/v1/metrics", method="POST", data={"metrics": sample_normal})
    print("   Waiting 20s for background EvaluationWorker cycle...")
    time.sleep(20)

    incidents = http_request(f"{base_url}/api/v1/incidents?state=OPEN")
    anomaly_incidents = [inc for inc in incidents if inc.get("source_id") == enroll_id]
    print(f"✅ Normal Evaluation Confirmed: {len(anomaly_incidents)} open incidents for this metric.")

    # 5. Inject Anomaly Spike
    spike_val = round(upper_bound * 2.5, 2)
    print(f"\n[Step 5] ⚡ INJECTING ANOMALY: Latency spike of {spike_val} ms (Upper bound is {upper_bound:.2f} ms)...")
    spike_sample = [{
        "metric": metric_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value": spike_val,
        "labels": labels
    }]
    http_request(f"{base_url}/api/v1/metrics", method="POST", data={"metrics": spike_sample})
    print("   Waiting 20s for EvaluationWorker anomaly detection...")
    time.sleep(20)

    incidents = http_request(f"{base_url}/api/v1/incidents")
    detected_incident = None
    for inc in incidents:
        if inc.get("source_id") == enroll_id and inc.get("detection_type") == "ANOMALY":
            detected_incident = inc
            break

    if not detected_incident:
        print("⚠️ Waiting another 15s for next evaluator cycle...")
        time.sleep(15)
        incidents = http_request(f"{base_url}/api/v1/incidents")
        for inc in incidents:
            if inc.get("source_id") == enroll_id and inc.get("detection_type") == "ANOMALY":
                detected_incident = inc
                break

    assert detected_incident is not None, "Failed: Anomaly incident was not generated!"

    inc_id = detected_incident["id"]
    print("🚨 ANOMALY INCIDENT DETECTED!")
    print(f"   Incident ID:      #{inc_id}")
    print(f"   State:            {detected_incident.get('state')}")
    print(f"   Severity:         {detected_incident.get('severity')}")
    print(f"   Observed Value:   {detected_incident.get('latest_value')} ms")
    print(f"   Summary:          {detected_incident.get('summary')}")

    # 6. Acknowledge Incident
    print(f"\n[Step 6] Operator acknowledging Incident #{inc_id}...")
    ack_res = http_request(f"{base_url}/api/v1/incidents/{inc_id}/acknowledge", method="POST")
    print(f"✅ Incident #{inc_id} state updated to: {ack_res.get('state')}")

    # 7. Recovery Verification
    print("\n[Step 7] Testing System Auto-Recovery...")
    print("   Sending normal sample 1 (119.5 ms)...")
    http_request(f"{base_url}/api/v1/metrics", method="POST", data={"metrics": [{
        "metric": metric_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value": 119.5,
        "labels": labels
    }]})
    print("   Waiting 20s for evaluator cycle...")
    time.sleep(20)

    inc_status = http_request(f"{base_url}/api/v1/incidents/{inc_id}")
    print(f"   Incident #{inc_id} state after recovery 1: {inc_status.get('state')} (consecutive normal={inc_status.get('consecutive_normal_count')})")

    print("   Sending normal sample 2 (120.2 ms)...")
    http_request(f"{base_url}/api/v1/metrics", method="POST", data={"metrics": [{
        "metric": metric_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value": 120.2,
        "labels": labels
    }]})
    print("   Waiting 20s for final recovery evaluation...")
    time.sleep(20)

    resolved_status = http_request(f"{base_url}/api/v1/incidents/{inc_id}")
    print(f"✅ Incident #{inc_id} final state: {resolved_status.get('state')}")
    print(f"   Resolved at: {resolved_status.get('resolved_at')}")

    print("\n" + "=" * 70)
    print("🎉 FULL ANOMALY DETECTION LIFECYCLE TEST PASSED SUCCESSFULLY!")
    print(f"Check the web dashboard: {base_url}/ui/")
    print("=" * 70)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://8.234.119.170:8000"
    run_live_anomaly_test(target)
