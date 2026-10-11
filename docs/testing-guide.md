# Testing Strategy & Verification Guide
## Intelligent Observability & Event Watchdog

This document details the test categories, execution commands, coverage requirements, and verification procedures for the EventWatchdog application.

---

## 1. Test Architecture & Categories

Testing is organized into three strictly separated tiers:

```text
tests/
├── conftest.py
├── unit/                     # Isolated unit tests for functions, math, schemas, parsers
│   ├── test_schemas.py
│   ├── test_log_parser.py
│   ├── test_rule_engine.py
│   ├── test_anomaly_stats.py
│   └── test_grafana_provisioning.py
├── integration/              # Component interactions with SQLite and mock TSDB
│   ├── test_health.py
│   ├── test_ingestion_api.py
│   ├── test_monitors_api.py
│   └── test_models_api.py
└── functional/               # End-to-end user journeys
    ├── test_incident_journey.py
    └── test_anomaly_journey.py
```

### Deterministic Principles
- **Zero External Dependencies:** Tests use in-memory SQLite fixtures (`sqlite:///:memory:`) and deterministic synthetic math seeds (`random.seed(42)`).
- **No Unpredictable Host Load:** Calculations and thresholds are verified against exact mathematical inputs rather than live clock jitter or dynamic host CPU spikes.
- **Mock External Boundaries:** VictoriaMetrics TSDB queries are mocked in integration tests via `AsyncMock` to ensure test execution runs reliably offline or inside isolated CI runners.

---

## 2. Test Execution Commands

### Run Unit Tests Only
```powershell
python -m pytest tests/unit -v
```

### Run Integration Tests Only
```powershell
python -m pytest tests/integration -v
```

### Run Functional / End-to-End Journeys Only
```powershell
python -m pytest tests/functional -v
```

### Run Complete Test Suite
```powershell
python -m pytest -v
```

### Run with Coverage Reporting
```powershell
python -m pytest --cov=app --cov-report=term-missing
```

---

## 3. Test Coverage Breakdown

| Category | Module / Test File | Purpose | Tests |
| :--- | :--- | :--- | :--- |
| **Unit** | `test_schemas.py` | Validates regexes, finite values, strips high-cardinality labels | 5 |
| **Unit** | `test_log_parser.py` | JSON & syslog parsing, metric derivation, error counting | 4 |
| **Unit** | `test_rule_engine.py` | Operators (`>`, `<`, `==`), deduplication logic, recovery count | 3 |
| **Unit** | `test_anomaly_stats.py` | Robust MAD & Rolling Z-Score fitting, zero-variance $\epsilon$-floor | 5 |
| **Unit** | `test_grafana_provisioning.py`| Datasource YAML syntax, provider config, dashboard JSON schemas | 3 |
| **Integration**| `test_health.py` | App root and `/api/v1/health` status checks | 2 |
| **Integration**| `test_ingestion_api.py` | POST `/api/v1/metrics` and POST `/api/v1/logs` round-trips | 2 |
| **Integration**| `test_monitors_api.py` | CRUD operations for static monitoring rules | 1 |
| **Integration**| `test_models_api.py` | Enrollment, model registry retrieval, patch updates | 1 |
| **Functional** | `test_incident_journey.py` | Static rule breach $\rightarrow$ deduplication $\rightarrow$ ack $\rightarrow$ resolution | 1 |
| **Functional** | `test_anomaly_journey.py` | 2,000 history training $\rightarrow$ outlier $\rightarrow$ incident $\rightarrow$ resolution | 1 |
| **Total** | | | **28** |
