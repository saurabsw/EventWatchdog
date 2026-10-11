# Product Requirements Document
## Intelligent Observability & Event Watchdog

**Version:** 1.0  
**Status:** MVP specification  
**Development environment:** Windows with Docker Desktop  
**Target deployment:** Google Cloud Platform (GCP)  
**Primary language:** Python  
**API framework:** FastAPI

## 1. Product vision

Build a lightweight, API-first observability application that collects host metrics and application-log-derived metrics, evaluates static monitoring rules, detects unusual metric behavior, and manages alert and incident lifecycles.

The solution must run locally on a Windows development machine and have documented, repeatable deployment instructions for a future GCP environment.

The application must be understandable to a new developer or evaluator who clones the repository and follows the README.

## 2. Objectives

1. Collect host metrics using Telegraf.
2. Ingest application logs through an API.
3. Parse supported log formats and convert recognized events into standardized time-series metrics.
4. Allow users to configure static threshold rules.
5. Allow users to enable anomaly detection and select a model strategy for individual metric series.
6. Train statistical models using a configurable history of 2,000 or 4,000 observations per series.
7. Detect anomalous observations and produce expected values and prediction bounds.
8. Create, deduplicate, acknowledge, and automatically resolve incidents.
9. Provide a simple web UI for configuring rules and anomaly detection.
10. Provide standalone Grafana dashboards for metric collections, anomalies, and alert/incident indicators.
11. Include unit, integration, and functional tests.
12. Provide complete setup, operation, troubleshooting, and GCP migration documentation.

## 3. Scope

### Included in the MVP

- Telegraf host monitoring.
- Windows-first local setup.
- Documented Linux/GCP VM Telegraf setup.
- FastAPI metric and log ingestion APIs.
- A defined, versioned metric schema.
- At least one documented application-log format and configurable parsing patterns.
- VictoriaMetrics single-node as the time-series database.
- SQLite for configuration, model metadata, incidents, and audit history.
- Static threshold rules.
- Per-series statistical anomaly detection.
- Configurable model enrollment and training history.
- Continuous rule and anomaly evaluation.
- Incident deduplication, acknowledgement, and recovery.
- Lightweight web UI.
- Provisioned Grafana dashboards.
- Automated tests and sample data.
- Docker Compose for local application services.

### Deferred beyond the MVP

- Kubernetes-based deployment.
- Managed cloud database migration.
- Distributed queues and multi-node processing.
- Arbitrary log-format discovery.
- Deep learning forecasting models.
- Enterprise authentication and multi-tenant authorization.
- PagerDuty, ServiceNow, email, or SMS integrations.
- High-availability production deployment.

## 4. Architecture

### 4.1 Components

**Telegraf:** Collects host CPU, memory, disk, disk I/O, and network metrics using supported input plugins. It sends metrics to VictoriaMetrics using a documented, tested ingestion protocol.

**FastAPI application:** Provides metric and log ingestion, configuration APIs, health checks, the lightweight configuration UI, and incident-management APIs.

**Log parser and normalizer:** Converts recognized application-log events into metric name, timestamp, numeric value, and bounded labels. Unsupported lines must be counted and reported rather than silently discarded.

**VictoriaMetrics:** Stores time-series samples and serves queries for dashboards, rules, and anomaly evaluation.

**SQLite:** Stores rules, metric enrollment/configuration, model metadata, incident records, audit entries, and processing state. It must not be used as the primary time-series store.

**Rule evaluator:** Continuously evaluates enabled threshold rules against recent time-series data.

**Model training service:** Retrieves the configured history for each enrolled series, trains or calculates the selected statistical baseline, and stores model metadata and parameters.

**Anomaly evaluator:** Compares new observations against the active baseline and its bounds, then submits qualifying events to incident management.

**Incident manager:** Creates and deduplicates incidents, records acknowledgement, tracks repeated occurrences, and resolves incidents after configured recovery conditions.

**Grafana:** Runs as a standalone service and reads time-series data from VictoriaMetrics. Dashboards are provisioned from repository files rather than created manually.

### 4.2 Logical data flow

1. Telegraf collects host measurements and writes time-series data to VictoriaMetrics.
2. An application sends logs to the FastAPI ingestion endpoint.
3. The log parser normalizes recognized events into metrics and writes them to VictoriaMetrics.
4. Users configure static rules and anomaly detection through the web UI or API.
5. The rule evaluator and anomaly evaluator query the time-series database.
6. Detection events are sent to the incident manager.
7. Incident state is stored in SQLite, with relevant bounded incident indicators exported as time-series metrics where appropriate.
8. Grafana displays collection health, actual values, anomaly bounds, and alert/incident indicators.

Background workers may run as separate processes or modules in the MVP, but their responsibilities and interfaces must be clearly separated.

## 5. Standard metric schema

The application must document a canonical metric representation.

Example:

{
  "metric": "application_errors_total",
  "timestamp": "2026-10-11T12:00:00Z",
  "value": 17,
  "labels": {
    "service": "payment-api",
    "environment": "local",
    "severity": "ERROR",
    "source": "log_parser"
  }
}

Required fields:

- `metric`: metric name.
- `timestamp`: timezone-aware timestamp, normalized to UTC.
- `value`: finite numeric measurement.
- `labels`: string-valued, bounded metadata describing the series.

Labels must not contain raw log messages, stack traces, user identifiers, request IDs, or other high-cardinality values. Metric names and labels must be validated before storage.

Host metrics must retain appropriate host and source labels. Equivalent metric representations from Telegraf and log parsing must be queryable through the same time-series system.

## 6. Telegraf requirements

Telegraf is the only host-system collection agent in the MVP.

The repository must include:

- A Windows-oriented example Telegraf configuration.
- A Linux/GCP VM example configuration.
- A documented installation and configuration procedure.
- A documented output configuration targeting the local or remote VictoriaMetrics endpoint.
- A verification procedure that confirms metrics are arriving.
- Troubleshooting instructions for service startup, connectivity, credentials if enabled, and missing measurements.

For Windows development, Telegraf should run natively on the Windows host when the goal is to monitor that host. Running it inside a container would normally measure the container environment rather than provide the intended native Windows host view.

The configuration must be editable through the configuration file, not by changing application source code. Use the Telegraf installation's documented service mechanism for the relevant operating system.

## 7. Application log ingestion

The API must accept log entries or batches of log entries.

The MVP parser must support at least one clearly documented log format and allow additional patterns to be added through configuration.

Recognized events must produce deterministic metric names and numeric values. Examples include:

- Application error count.
- Warning count.
- Request failure count where the log format contains sufficient information.
- Selected application-event counts.

Parsing must include timestamps where available, source/service metadata, validation, malformed-record handling, and observability for rejected records.

Do not claim to support arbitrary application logs. Unsupported formats must be documented.

## 8. Static rule engine

Users must be able to create, read, update, enable, disable, and delete monitoring rules.

A rule should include:

- Rule name and description.
- Metric name and optional label filters.
- Evaluation window.
- Aggregation function, such as average, maximum, minimum, or count where meaningful.
- Comparison operator.
- Threshold value.
- Severity.
- Consecutive breach and recovery requirements.
- Enabled/disabled status.

The evaluator must run continuously and avoid creating a new incident for every poll of the same continuing breach.

Rules must be validated before saving. Invalid metric names, unsupported operators, or invalid windows must return actionable errors.

## 9. Anomaly detection and model management

Anomaly detection must be configurable independently for each selected metric series.

The configuration must include:

- Enabled/disabled state.
- Model strategy.
- History size: 2,000 or 4,000 observations.
- Sampling interval or resampling strategy.
- Training status and last training time.
- Model version and training window.
- Sensitivity or bound multiplier.
- Retraining policy.
- Minimum data requirements.
- Model error/status information.

The MVP must implement a documented statistical baseline, such as rolling mean and standard deviation or a robust median/MAD strategy. It must calculate an expected value and upper/lower bounds when the chosen method supports them.

A statistical baseline must be described accurately; it must not be presented as a neural forecasting model.

Training history must be selected per series, not pooled indiscriminately across different metrics or hosts. Missing data, duplicate timestamps, insufficient history, constant values, and non-finite values must be handled explicitly.

When a new observation falls outside the configured bounds and satisfies the anomaly policy, the anomaly evaluator submits a detection event to incident management.

The model-training service and anomaly-evaluation service must have separate interfaces, even if they run in the same application process initially.

## 10. Incident lifecycle

Supported states:

- `OPEN`
- `ACKNOWLEDGED`
- `RESOLVED`

Incident records must include source type, rule or model reference, metric and relevant labels, severity, first/last observed timestamps, occurrence count, current state, and resolution metadata.

Requirements:

- Deduplicate continuing detections using a stable identity based on detection type, rule/model, and metric series.
- Increment occurrence count and update last-observed time when the same incident recurs.
- Allow acknowledgement through the API and UI.
- Resolve incidents after configurable consecutive normal evaluations.
- Preserve incident history for investigation.
- Record state transitions in the audit history.
- Make detection processing idempotent where practical.

External notifications are out of scope for the MVP. Provide a clean integration interface and a simulated webhook/logging adapter.

## 11. Web UI

Provide a lightweight UI served by the application; a separate frontend build system is not required for the MVP.

The UI must support:

- Browsing known metrics and their labels.
- Creating and editing static rules.
- Enabling/disabling anomaly detection for a metric series.
- Selecting a model strategy and training history.
- Viewing model training status and recent detection results.
- Browsing incidents and acknowledging them.
- Displaying useful API or validation errors.

Grafana remains the primary dashboard and visualization system; the configuration UI must not attempt to replace Grafana.

## 12. Grafana dashboards

Provision Grafana data sources and dashboards from files in the repository.

Required dashboards:

1. **Collection & Service Health:** host CPU, memory, disk, network, ingestion rate, parser success/failure, and service health.
2. **Anomaly Detection:** actual metric values, expected baseline and bounds where available, anomaly indicators, and model status where practical.
3. **Alerts & Incidents:** active incident counts, severity distribution, detections over time, and available rule/model indicators.

Dashboards must be usable after a fresh Docker Compose startup without manual dashboard construction.

Incident lifecycle records remain authoritative in SQLite and the FastAPI API. Grafana visualizations must not imply that aggregate time-series indicators are a full incident-management interface.

## 13. API requirements

Use versioned routes under `/api/v1`.

Minimum endpoint groups:

- `GET /api/v1/health`
- `POST /api/v1/metrics`
- `POST /api/v1/logs`
- `GET /api/v1/metrics`
- `GET /api/v1/services`
- `GET /api/v1/monitors`
- `POST /api/v1/monitors`
- `GET /api/v1/monitors/{id}`
- `PATCH /api/v1/monitors/{id}`
- `GET /api/v1/models`
- `POST /api/v1/models/train`
- `GET /api/v1/detections`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{id}`
- `POST /api/v1/incidents/{id}/acknowledge`

Additional routes may be introduced for model enrollment, rule deletion, recovery, and diagnostic information.

Document request/response schemas and error responses. Provide OpenAPI documentation through FastAPI.

## 14. Storage and configuration

Use VictoriaMetrics single-node for time-series data and SQLite for application metadata and workflow state.

Keep storage paths, API ports, evaluation intervals, retention settings, and other environment-specific values configurable. Persist local development data in named Docker volumes or clearly documented local directories.

Do not commit secrets, machine-specific absolute paths, or personal data. Provide a `.env.example` and validate required settings at startup.

Design repository configuration so a future GCP deployment can replace local endpoints and storage settings without rewriting application logic.

## 15. Testing strategy

### Unit tests

Test individual functions and services, including:

- Metric schema validation.
- Timestamp normalization.
- Log parsing and normalization.
- Invalid and malformed log handling.
- Static rule comparison and aggregation.
- Anomaly-bound calculation.
- Training with insufficient, missing, constant, and irregular data.
- Incident identity and deduplication.
- Acknowledgement and recovery transitions.
- API input validation.

Use deterministic fixtures and mocked external boundaries where appropriate.

### Integration tests

Test interactions between components, including:

- FastAPI metric ingestion and VictoriaMetrics persistence/query.
- Log ingestion, parsing, and normalized metric storage.
- Rule evaluation against stored time-series samples.
- Model training and anomaly evaluation using seeded data.
- Incident persistence and deduplication.
- Docker service health and Grafana data-source connectivity where practical.

Integration tests must be marked separately and clearly document required services.

### Functional/end-to-end tests

Automate at least these user journeys:

1. Start the application stack.
2. Submit or generate a known metric.
3. Configure a static threshold rule.
4. Send a value above the threshold.
5. Verify an incident is created.
6. Send repeated breaches and verify the incident is deduplicated.
7. Acknowledge the incident.
8. Send normal values and verify recovery after the configured conditions.
9. Submit application logs and verify they become normalized metrics.
10. Enroll a metric series, train a baseline using seeded historical data, and verify that an out-of-bound observation is detected.
11. Confirm Grafana and API health checks pass.

Tests must not depend on live external services or unpredictable host load. Provide deterministic synthetic data for reliable evaluation.

### Test execution

Provide documented commands for:

- Unit tests only.
- Integration tests only.
- Functional tests only.
- All tests.
- Coverage reporting.

Use pytest. Tests must be runnable by a new developer following the README.

## 16. Security, reliability, and operations

- Validate and limit incoming payload sizes.
- Apply request timeouts and clear error handling.
- Avoid logging secrets or full sensitive log content.
- Keep high-cardinality data out of metric labels.
- Provide health/readiness endpoints and container health checks.
- Make background worker failures observable.
- Use structured application logging.
- Document local ports, data persistence, reset procedures, and troubleshooting.
- Do not expose development services publicly by default.

Authentication and production hardening must be explicitly documented as required before public or enterprise deployment.

## 17. GCP migration requirements

The MVP must remain container-friendly and avoid dependence on Windows-specific application paths.

Provide a separate deployment guide covering:

- Running the stack locally on Windows.
- Deploying to a GCP Compute Engine VM as the simplest initial cloud path.
- Installing Telegraf on the monitored VM and directing it to the intended ingestion endpoint.
- Firewall and network considerations.
- Persistent storage and backup considerations.
- Environment-specific configuration.
- Secret management and TLS requirements before public exposure.
- A future migration path to managed GCP services where appropriate.

Do not claim that the MVP is production-ready for high availability or internet exposure.

## 18. Required repository structure

The exact layout may evolve, but it must keep application responsibilities, infrastructure, tests, and documentation separated.

- `app/` — API, schemas, services, workers, rule engine, anomaly detection, incident manager.
- `tests/unit/`
- `tests/integration/`
- `tests/functional/`
- `docker/` or root-level Docker Compose files.
- `grafana/provisioning/`
- `grafana/dashboards/`
- `telegraf/`
- `scripts/`
- `sample_data/`
- `docs/`
- `prompts.md`
- `README.md`
- `.env.example`
- `pyproject.toml`
- `docker-compose.yml`

Include database initialization/migration handling and a reproducible sample-data generator.

## 19. Definition of done

The MVP is complete only when:

1. A fresh clone can be started using documented commands.
2. VictoriaMetrics, Grafana, and the application report healthy status.
3. Telegraf setup instructions are tested and demonstrate host metric ingestion.
4. Application logs can be converted to normalized time-series data.
5. Static rules produce incidents from known test data.
6. Per-series anomaly configuration, training, bounds, and evaluation work.
7. Incident deduplication, acknowledgement, and recovery work.
8. All three test categories exist and their commands are documented.
9. Provisioned Grafana dashboards load without manual dashboard creation.
10. Unit tests pass, and integration/functional results are reported accurately.
11. No secrets or local-only absolute paths are required.
12. `README.md`, architecture documentation, Telegraf setup, testing guide, GCP guide, and `prompts.md` are complete.
13. Antigravity provides a final acceptance report with actual test results, known limitations, startup instructions, and elapsed time.

## 20. MVP prioritization

Prioritize a working end-to-end vertical slice over broad feature coverage:

1. Start infrastructure and API.
2. Ingest and query metrics.
3. Convert sample logs into metrics.
4. Evaluate a static rule and manage an incident.
5. Train and evaluate a statistical baseline.
6. Provision Grafana dashboards.
7. Automate tests and document installation.
8. Verify a clean startup and final demo.

If time is constrained, reduce supported log formats and UI complexity before compromising the tests, setup instructions, or end-to-end workflow.
