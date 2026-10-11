# Intelligent Observability & Event Watchdog

An API-first, lightweight observability application that collects host metrics via Telegraf, ingests application logs via FastAPI, extracts normalized time-series data into VictoriaMetrics, evaluates static threshold alerts, runs statistical anomaly detection (Rolling Z-Score / Robust MAD), and manages incident lifecycles (OPEN, ACKNOWLEDGED, RESOLVED).

---

## Architecture Stack

- **FastAPI (Python 3.12+):** API-first engine, metric/log ingestion, rule evaluator, model trainer, incident manager, and lightweight web UI.
- **VictoriaMetrics (Single-Node):** Time-series database storing host and log metrics, serving high-throughput range queries.
- **SQLite:** Transactional relational store for static monitor rules, anomaly model metadata, incident states, and audit trails.
- **Grafana OSS:** Provisioned visualizations for Collection Health, Anomaly Detection & Bounds, and Alerts & Incidents.
- **Telegraf:** Native Windows and Linux host-system collection agent.

---

## Documentation Quick Links

- [Step-by-Step Windows Local Setup Guide](file:///c:/Users/USER/Videos/EventWatchdog/docs/windows-setup.md)
- [Telegraf Host Monitoring & Verification Guide](file:///c:/Users/USER/Videos/EventWatchdog/docs/telegraf-setup.md)
- [GCP Compute Engine VM Deployment & Migration Guide](file:///c:/Users/USER/Videos/EventWatchdog/docs/gcp-migration.md)
- [Testing Strategy & Test Execution Guide](file:///c:/Users/USER/Videos/EventWatchdog/docs/testing-guide.md)
- [Full System Architecture & Technical Specifications](file:///c:/Users/USER/Videos/EventWatchdog/docs/architecture.md)
- [Approved PRD Requirements Specification](file:///c:/Users/USER/Videos/EventWatchdog/docs/PRD.md)

---

## Quick Start (Docker Compose)

### 1. Start the Stack
```powershell
docker compose up -d
```
All services bind to localhost only by default:
- **Web Console UI:** [http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/)
- **FastAPI App & Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **FastAPI Health Endpoint:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **VictoriaMetrics TSDB:** [http://127.0.0.1:8428](http://127.0.0.1:8428)
- **Grafana Dashboards:** [http://127.0.0.1:3000](http://127.0.0.1:3000) (User: `admin`, Pass: `admin`)

### 2. View Service Logs
```powershell
docker compose logs -f
```

### 3. Stop the Stack
```powershell
docker compose down
```

### 4. Reset Persistent Volumes (Fresh State)
```powershell
docker compose down -v
```

---

## Running Automated Tests

Tests are organized into three strictly separated tiers using pytest:

### Run by Category
```powershell
# 1. Unit tests only (schemas, parsers, rule evaluation math, anomaly baselines, provisioning)
python -m pytest tests/unit -v

# 2. Integration tests only (FastAPI endpoints, SQLite persistence, TSDB round-trips)
python -m pytest tests/integration -v

# 3. Functional / End-to-end journey tests only (complete incident lifecycle & anomaly journey)
python -m pytest tests/functional -v
```

### Run Entire Suite with Coverage Report
```powershell
python -m pytest --cov=app --cov-report=term-missing
```

---

## Production Readiness & Limitations

> [!WARNING]
> This MVP is designed for local development and demonstration. Before exposing to production or public internet:
> 1. **Authentication:** Add OAuth2 / JWT / SSO authentication to FastAPI routes and Web UI.
> 2. **TLS Termination:** Deploy a reverse proxy (Nginx / Caddy / Cloud Load Balancer) to terminate HTTPS/TLS.
> 3. **Database Scalability:** Migrate SQLite to Cloud SQL PostgreSQL when scaling past a single server node.
> 4. **Distributed Workers:** Transition the in-process evaluation loop to Celery / Cloud Tasks for horizontal scaling.
