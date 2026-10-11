# Step-by-Step Windows Local Setup Guide
## Intelligent Observability & Event Watchdog

This guide walks you through setting up and running the EventWatchdog application locally on **Windows 10/11**.

---

## 1. Prerequisites

1. **Python 3.12+ (Python 3.14 verified):**
   - Verify installation: `python --version`
2. **Git for Windows:**
   - Verify installation: `git --version`
3. **Docker Desktop for Windows (Recommended for full stack):**
   - Ensure Docker Desktop is running with WSL 2 backend enabled.
   - Verify installation: `docker --version` and `docker compose version`
4. **Telegraf (for native Windows host monitoring):**
   - See [`docs/telegraf-setup.md`](file:///c:/Users/USER/Videos/EventWatchdog/docs/telegraf-setup.md) for official distribution download instructions.

---

## 2. Clone & Environment Configuration

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd c:\Users\USER\Videos\EventWatchdog
   ```

2. Copy the example configuration to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   > [!NOTE]
   > `.env.example` contains safe local defaults with no real secrets, passwords, or machine-specific absolute paths.

---

## 3. Option A: Run Full Stack with Docker Compose (Recommended)

Starts VictoriaMetrics TSDB, the FastAPI Application, and Standalone Grafana OSS with pre-provisioned dashboards:

```powershell
# 1. Start all containers in background
docker compose up -d

# 2. Verify container health status
docker compose ps

# 3. Stream container logs
docker compose logs -f

# 4. Stop all containers
docker compose down

# 5. Reset all persistent volumes (Fresh state)
docker compose down -v
```

### Active Port Endpoints:
- **FastAPI Management Console:** [http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/)
- **Swagger OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **FastAPI Health Status:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **VictoriaMetrics TSDB:** [http://127.0.0.1:8428](http://127.0.0.1:8428)
- **Standalone Grafana Dashboards:** [http://127.0.0.1:3000](http://127.0.0.1:3000) (User: `admin`, Pass: `admin`)

---

## 4. Option B: Run Standalone Python Application (Without Docker)

If running in a lightweight development environment:

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run application with auto-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 5. End-to-End Demo Walkthrough

Once the stack is running, execute the following steps to demonstrate the complete observability and alerting pipeline:

### Step 1: Ingest Normal Application Metrics
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/metrics" -Method Post -ContentType "application/json" -Body '{
  "metrics": [
    {
      "metric": "payment_latency_ms",
      "value": 45.2,
      "labels": { "service": "checkout", "environment": "local" }
    }
  ]
}'
```

### Step 2: Create a Static Monitor Rule
Open [http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/) or call the API:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/monitors" -Method Post -ContentType "application/json" -Body '{
  "name": "Checkout Latency SLA",
  "metric_name": "payment_latency_ms",
  "comparison_operator": ">",
  "threshold": 100.0,
  "severity": "CRITICAL",
  "evaluation_window_seconds": 60,
  "consecutive_breaches": 1,
  "consecutive_recoveries": 2
}'
```

### Step 3: Trigger a Threshold Breach
Send an elevated metric observation exceeding the 100.0 threshold:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/metrics" -Method Post -ContentType "application/json" -Body '{
  "metrics": [
    {
      "metric": "payment_latency_ms",
      "value": 240.0,
      "labels": { "service": "checkout", "environment": "local" }
    }
  ]
}'
```
Wait 15 seconds for the background evaluator loop to run. Refresh [http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/) and observe the incident in **`OPEN`** state.

### Step 4: Acknowledge and Auto-Recover
1. In the Web UI, click **Acknowledge** on the open incident. The status transitions to **`ACKNOWLEDGED`**.
2. Send healthy observations below 100.0:
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/metrics" -Method Post -ContentType "application/json" -Body '{
     "metrics": [
       { "metric": "payment_latency_ms", "value": 35.0, "labels": { "service": "checkout", "environment": "local" } }
     ]
   }'
   ```
3. After 2 consecutive normal evaluation cycles, the incident automatically transitions to **`RESOLVED`**.

### Step 5: Statistical Anomaly Detection
1. In the Web UI, locate **Statistical Anomaly Models & Baseline Registry**.
2. Enroll `payment_processing_latency_ms` with strategy `robust_mad` and history `2,000 samples`.
3. Generate synthetic training data:
   ```powershell
   python sample_data/seed_historical_series.py --send --url http://127.0.0.1:8000
   ```
4. Click **Train** on the enrolled series. The UI displays updated upper/lower bounds and expected baseline.
5. In Grafana ([http://127.0.0.1:3000](http://127.0.0.1:3000)), open the **Anomaly Detection and Prediction Bounds** dashboard to see the live baseline and bound envelopes.
