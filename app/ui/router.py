from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EventWatchdog - Configuration & Incident Console</title>
    <style>
        :root {
            --bg-color: #0b1120;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --danger: #f43f5e;
            --warning: #fbbf24;
            --success: #34d399;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-color); color: var(--text-main); padding: 24px; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
        h1 { font-size: 22px; color: var(--accent); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
        .card h2 { font-size: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .badge-OPEN { background: rgba(244, 63, 94, 0.2); color: var(--danger); border: 1px solid var(--danger); }
        .badge-ACKNOWLEDGED { background: rgba(251, 191, 36, 0.2); color: var(--warning); border: 1px solid var(--warning); }
        .badge-RESOLVED { background: rgba(52, 211, 153, 0.2); color: var(--success); border: 1px solid var(--success); }
        .badge-TRAINED { background: rgba(52, 211, 153, 0.2); color: var(--success); }
        .badge-PENDING { background: rgba(251, 191, 36, 0.2); color: var(--warning); }
        .badge-FAILED { background: rgba(244, 63, 94, 0.2); color: var(--danger); }
        button { background: var(--accent); color: #0b1120; border: none; padding: 6px 12px; border-radius: 4px; font-weight: 600; cursor: pointer; }
        button:hover { opacity: 0.9; }
        .btn-ack { background: var(--warning); color: #000; }
        .btn-train { background: #818cf8; color: #000; }
        .btn-toggle { background: #475569; color: #fff; padding: 4px 8px; font-size: 11px; }
        form { display: grid; gap: 12px; font-size: 13px; }
        label { display: flex; flex-direction: column; gap: 4px; color: var(--text-muted); }
        input, select { background: #0b1120; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 4px; }
        .links a { color: var(--accent); text-decoration: none; margin-left: 14px; font-size: 13px; font-weight: 500; }
        .links a:hover { text-decoration: underline; }
        .tag { background: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 4px; }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>EventWatchdog Console</h1>
            <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">Lightweight Management & Incident Triage Console</p>
        </div>
        <div class="links">
            <a href="/docs" target="_blank">&#128214; OpenAPI Docs</a>
            <a href="http://127.0.0.1:3000" target="_blank">&#128202; Standalone Grafana</a>
        </div>
    </header>

    <div class="grid">
        <!-- 1. Incidents List -->
        <div class="card" style="grid-column: span 2;">
            <h2>
                <span>Active & Recent Incidents (Authoritative SQLite State)</span>
                <button onclick="loadIncidents()">Refresh</button>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Metric</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Observed</th>
                        <th>Expected</th>
                        <th>Occurrences</th>
                        <th>Last Seen</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="incidents-body">
                    <tr><td colspan="10" style="text-align: center; color: var(--text-muted);">Loading incidents...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 2. Browsable Metrics Catalog -->
        <div class="card" style="grid-column: span 2;">
            <h2>
                <span>Discovered Metric Series Catalog</span>
                <button onclick="loadMetrics()">Refresh Catalog</button>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric Name</th>
                        <th>Source</th>
                        <th>Static Rule</th>
                        <th>Anomaly Model</th>
                        <th>Quick Actions</th>
                    </tr>
                </thead>
                <tbody id="metrics-body">
                    <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Discovering metrics...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 3. Anomaly Model Registry -->
        <div class="card" style="grid-column: span 2;">
            <h2>
                <span>Statistical Anomaly Models & Baseline Registry</span>
                <button onclick="loadModels()">Refresh Models</button>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Metric Name</th>
                        <th>Strategy</th>
                        <th>History Window</th>
                        <th>Bounds Multiplier</th>
                        <th>Status</th>
                        <th>Active Bounds [Lower, Upper]</th>
                        <th>Baseline</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="models-body">
                    <tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Loading model registry...</td></tr>
                </tbody>
            </table>

            <div style="margin-top: 20px; border-top: 1px solid var(--border); padding-top: 16px;">
                <h3 style="font-size: 14px; margin-bottom: 12px; color: var(--accent);">Enroll Metric Series for Anomaly Detection</h3>
                <form id="enroll-form" onsubmit="handleEnroll(event)" style="grid-template-columns: 2fr 1fr 1fr 1fr auto; display: grid; align-items: end;">
                    <label>Metric Name
                        <input type="text" id="model-metric" required placeholder="payment_processing_latency_ms" />
                    </label>
                    <label>Strategy
                        <select id="model-strategy">
                            <option value="robust_mad">Robust MAD (Median/MAD)</option>
                            <option value="rolling_zscore">Rolling Z-Score (Mean/StdDev)</option>
                        </select>
                    </label>
                    <label>History Size
                        <select id="model-history">
                            <option value="2000">2,000 samples</option>
                            <option value="4000">4,000 samples</option>
                        </select>
                    </label>
                    <label>Multiplier (k-sigma/k-MAD)
                        <input type="number" step="0.5" id="model-mult" value="3.0" />
                    </label>
                    <button type="submit" style="height: 35px;">Enroll Metric</button>
                </form>
            </div>
        </div>

        <!-- 4. Create Static Rule Form -->
        <div class="card">
            <h2>Create Static Threshold Rule</h2>
            <form id="create-rule-form" onsubmit="handleCreateRule(event)">
                <label>Rule Name
                    <input type="text" id="rule-name" required placeholder="High Error Rate Alert" />
                </label>
                <label>Metric Name
                    <input type="text" id="rule-metric" required placeholder="app_log_errors_total" />
                </label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <label>Operator
                        <select id="rule-op">
                            <option value=">">&gt; (Greater than)</option>
                            <option value=">=">&gt;= (Greater or equal)</option>
                            <option value="<">&lt; (Less than)</option>
                            <option value="<=">&lt;= (Less or equal)</option>
                        </select>
                    </label>
                    <label>Threshold
                        <input type="number" step="any" id="rule-threshold" required placeholder="5.0" />
                    </label>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <label>Severity
                        <select id="rule-severity">
                            <option value="WARNING">WARNING</option>
                            <option value="CRITICAL">CRITICAL</option>
                            <option value="INFO">INFO</option>
                        </select>
                    </label>
                    <label>Evaluation Window (s)
                        <input type="number" id="rule-window" value="60" min="15" />
                    </label>
                </div>
                <button type="submit" style="margin-top: 8px;">Save Static Rule</button>
            </form>
        </div>

        <!-- 5. Configured Rules List -->
        <div class="card">
            <h2>
                <span>Configured Static Rules</span>
                <button onclick="loadRules()">Refresh</button>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Metric</th>
                        <th>Condition</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="rules-body">
                    <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Loading rules...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 6. Recent Audit / Detection Events -->
        <div class="card" style="grid-column: span 2;">
            <h2>
                <span>Recent Audit Trail & Detection Log</span>
                <button onclick="loadDetections()">Refresh Detections</button>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Entity</th>
                        <th>ID</th>
                        <th>Action</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody id="detections-body">
                    <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading audit history...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function loadIncidents() {
            try {
                const res = await fetch('/api/v1/incidents');
                const data = await res.json();
                const tbody = document.getElementById('incidents-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: var(--text-muted);">No active incidents.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(inc => `
                    <tr>
                        <td>#${inc.id}</td>
                        <td><span class="tag">${inc.detection_type}</span></td>
                        <td><code>${inc.metric_name}</code></td>
                        <td>${inc.severity}</td>
                        <td><span class="badge badge-${inc.state}">${inc.state}</span></td>
                        <td>${inc.latest_value !== null ? inc.latest_value.toFixed(2) : '-'}</td>
                        <td>${inc.expected_value !== null ? inc.expected_value.toFixed(2) : '-'}</td>
                        <td><strong>${inc.occurrence_count}</strong></td>
                        <td>${new Date(inc.last_seen_at).toLocaleTimeString()}</td>
                        <td>
                            ${inc.state === 'OPEN' ? `<button class="btn-ack" onclick="acknowledgeIncident(${inc.id})">Acknowledge</button>` : '-'}
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function acknowledgeIncident(id) {
            await fetch(`/api/v1/incidents/${id}/acknowledge`, { method: 'POST' });
            loadIncidents();
        }

        async function loadMetrics() {
            try {
                const res = await fetch('/api/v1/metrics/discovered');
                const data = await res.json();
                const tbody = document.getElementById('metrics-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No metric series discovered.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(m => `
                    <tr>
                        <td><code>${m.metric_name}</code></td>
                        <td>${m.source}</td>
                        <td>${m.has_rule ? '&#9989; Active' : '&#10060; None'}</td>
                        <td>${m.has_anomaly_model ? '&#9989; Enrolled' : '&#10060; None'}</td>
                        <td>
                            <button class="btn-toggle" onclick="prefillRule('${m.metric_name}')">+ Rule</button>
                            <button class="btn-toggle" onclick="prefillEnroll('${m.metric_name}')">+ Model</button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        function prefillRule(metric) {
            document.getElementById('rule-metric').value = metric;
            document.getElementById('rule-name').value = 'Monitor for ' + metric;
            window.scrollTo({ top: document.getElementById('create-rule-form').offsetTop - 50, behavior: 'smooth' });
        }

        function prefillEnroll(metric) {
            document.getElementById('model-metric').value = metric;
            window.scrollTo({ top: document.getElementById('enroll-form').offsetTop - 50, behavior: 'smooth' });
        }

        async function loadModels() {
            try {
                const res = await fetch('/api/v1/models');
                const data = await res.json();
                const tbody = document.getElementById('models-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No metric series enrolled.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(m => {
                    const bounds = m.active_model ? `[${m.active_model.lower_bound.toFixed(2)}, ${m.active_model.upper_bound.toFixed(2)}]` : 'Pending Training';
                    const baseline = m.active_model ? m.active_model.baseline_expected.toFixed(2) : '-';
                    return `
                    <tr>
                        <td>#${m.id}</td>
                        <td><code>${m.metric_name}</code></td>
                        <td>${m.model_strategy}</td>
                        <td>${m.history_size} samples</td>
                        <td>k=${m.bound_multiplier}</td>
                        <td><span class="badge badge-${m.model_status}">${m.model_status}</span></td>
                        <td>${bounds}</td>
                        <td>${baseline}</td>
                        <td>
                            <button class="btn-train" onclick="triggerTrain(${m.id})">Train</button>
                            <button class="btn-toggle" onclick="toggleEnroll(${m.id}, ${!m.enabled})">${m.enabled ? 'Disable' : 'Enable'}</button>
                        </td>
                    </tr>
                `}).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function toggleEnroll(id, enabled) {
            await fetch(`/api/v1/models/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabled })
            });
            loadModels();
        }

        async function triggerTrain(id) {
            const res = await fetch('/api/v1/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enrollment_id: id })
            });
            if (res.ok) {
                loadModels();
                loadDetections();
            } else {
                const err = await res.json();
                alert('Training note: ' + (err.detail || 'Insufficient historical samples in TSDB'));
            }
        }

        async function handleEnroll(e) {
            e.preventDefault();
            const payload = {
                metric_name: document.getElementById('model-metric').value,
                model_strategy: document.getElementById('model-strategy').value,
                history_size: parseInt(document.getElementById('model-history').value, 10),
                bound_multiplier: parseFloat(document.getElementById('model-mult').value)
            };
            const res = await fetch('/api/v1/models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('enroll-form').reset();
                loadModels();
                loadMetrics();
            } else {
                const err = await res.json();
                alert('Enrollment error: ' + (err.detail || 'Unknown error'));
            }
        }

        async function loadRules() {
            try {
                const res = await fetch('/api/v1/monitors');
                const data = await res.json();
                const tbody = document.getElementById('rules-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No rules defined.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td><strong>${r.name}</strong></td>
                        <td><code>${r.metric_name}</code></td>
                        <td>${r.comparison_operator} ${r.threshold}</td>
                        <td>${r.severity}</td>
                        <td>${r.enabled ? 'Active' : 'Disabled'}</td>
                        <td>
                            <button class="btn-toggle" onclick="toggleRule(${r.id}, ${!r.enabled})">${r.enabled ? 'Disable' : 'Enable'}</button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function toggleRule(id, enabled) {
            await fetch(`/api/v1/monitors/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabled })
            });
            loadRules();
        }

        async function handleCreateRule(e) {
            e.preventDefault();
            const payload = {
                name: document.getElementById('rule-name').value,
                metric_name: document.getElementById('rule-metric').value,
                comparison_operator: document.getElementById('rule-op').value,
                threshold: parseFloat(document.getElementById('rule-threshold').value),
                severity: document.getElementById('rule-severity').value,
                evaluation_window_seconds: parseInt(document.getElementById('rule-window').value, 10),
                aggregation_func: 'avg'
            };
            const res = await fetch('/api/v1/monitors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('create-rule-form').reset();
                loadRules();
                loadMetrics();
            } else {
                const err = await res.json();
                alert('Failed to create rule: ' + (err.detail || 'Unknown error'));
            }
        }

        async function loadDetections() {
            try {
                const res = await fetch('/api/v1/detections');
                const data = await res.json();
                const tbody = document.getElementById('detections-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No detection events.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.slice(0, 15).map(d => `
                    <tr>
                        <td>${new Date(d.timestamp).toLocaleTimeString()}</td>
                        <td>${d.entity_type}</td>
                        <td>#${d.entity_id}</td>
                        <td><span class="tag">${d.action}</span></td>
                        <td><code>${d.details.length > 70 ? d.details.substring(0, 70) + '...' : d.details}</code></td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        // Initial fetch
        loadIncidents();
        loadMetrics();
        loadModels();
        loadRules();
        loadDetections();
        setInterval(loadIncidents, 10000);
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def get_console_ui():
    """Lightweight single-page administrative web UI for rules, models, and incidents."""
    return HTML_CONTENT
