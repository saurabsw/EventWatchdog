from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EventWatchdog Console - Intelligent Observability</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #090d16;
            --bg-card: #111827;
            --bg-card-subtle: #182234;
            --border: #1f293d;
            --border-hover: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --danger: #f43f5e;
            --danger-bg: rgba(244, 63, 94, 0.15);
            --warning: #f59e0b;
            --warning-bg: rgba(245, 158, 11, 0.15);
            --success: #10b981;
            --success-bg: rgba(16, 185, 129, 0.15);
            --purple: #a855f7;
            --purple-bg: rgba(168, 85, 247, 0.15);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-body);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Header */
        header {
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 0 16px var(--accent-glow);
        }
        .brand h1 {
            font-size: 18px;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #f8fafc, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand span.sub {
            font-size: 12px;
            color: var(--text-dim);
            margin-left: 8px;
            font-weight: 500;
        }

        /* Nav view tabs */
        .primary-nav {
            display: flex;
            background: var(--bg-body);
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--border);
            gap: 4px;
        }
        .nav-btn {
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        .nav-btn:hover {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.04);
        }
        .nav-btn.active {
            background: var(--bg-card-subtle);
            color: var(--accent);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-hover);
        }
        .badge-counter {
            background: var(--danger);
            color: #fff;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 6px var(--success);
        }
        .link-btn {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            transition: all 0.15s;
        }
        .link-btn:hover {
            color: var(--accent);
            border-color: var(--accent);
            background: var(--accent-glow);
        }

        /* Main Container */
        main {
            flex: 1;
            padding: 24px 28px;
            max-width: 1600px;
            width: 100%;
            margin: 0 auto;
        }

        /* Sub Tab Bar */
        .sub-tab-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 14px;
            margin-bottom: 24px;
        }
        .sub-tabs {
            display: flex;
            gap: 10px;
        }
        .sub-tab-btn {
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        .sub-tab-btn:hover {
            color: var(--text-main);
            background: var(--bg-card);
        }
        .sub-tab-btn.active {
            color: var(--accent);
            background: var(--bg-card);
            border: 1px solid var(--border);
        }

        /* Content Views */
        .view-section { display: none; }
        .view-section.active { display: block; animation: fadeIn 0.2s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        /* Cards and Grids */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 22px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            margin-bottom: 24px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
        }
        .card-header h2 {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card-header p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 3px;
        }
        .grid-split {
            display: grid;
            grid-template-columns: 3fr 2fr;
            gap: 24px;
        }
        @media (max-width: 1024px) {
            .grid-split { grid-template-columns: 1fr; }
        }

        /* Tables & Scroll Containers */
        .table-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 6px;
        }
        .bounded-scroll {
            max-height: 520px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 6px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }
        th {
            background: var(--bg-card-subtle);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 12px 14px;
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--border);
        }
        td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            color: var(--text-main);
        }
        tbody tr {
            transition: background 0.15s;
        }
        tbody tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.2);
        }

        /* Filter Controls */
        .filter-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            margin-bottom: 16px;
        }
        .search-input {
            background: var(--bg-body);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 13px;
            min-width: 280px;
            transition: border 0.2s;
        }
        .search-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 8px var(--accent-glow);
        }
        .chip-group {
            display: flex;
            gap: 6px;
        }
        .chip {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }
        .chip:hover {
            color: var(--text-main);
            border-color: var(--border-hover);
        }
        .chip.active {
            background: var(--accent-glow);
            color: var(--accent);
            border-color: var(--accent);
            font-weight: 600;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            letter-spacing: 0.02em;
        }
        .badge-OPEN { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger); }
        .badge-ACKNOWLEDGED { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning); }
        .badge-RESOLVED { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
        .badge-CRITICAL { background: var(--danger-bg); color: var(--danger); }
        .badge-WARNING { background: var(--warning-bg); color: var(--warning); }
        .badge-INFO { background: var(--accent-glow); color: var(--accent); }
        .badge-TRAINED { background: var(--success-bg); color: var(--success); }
        .badge-PENDING { background: var(--warning-bg); color: var(--warning); }
        .badge-FAILED { background: var(--danger-bg); color: var(--danger); }

        /* Buttons & Forms */
        button.btn-primary {
            background: var(--accent);
            color: #090d16;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s;
        }
        button.btn-primary:hover { opacity: 0.9; }
        button.btn-sm {
            padding: 5px 10px;
            font-size: 12px;
            border-radius: 5px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
        }
        .btn-ack { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning) !important; }
        .btn-ack:hover { background: var(--warning); color: #000; }
        .btn-resolve { background: var(--success-bg); color: var(--success); border: 1px solid var(--success) !important; margin-left: 4px; }
        .btn-resolve:hover { background: var(--success); color: #000; }
        .btn-train { background: var(--purple-bg); color: var(--purple); border: 1px solid var(--purple) !important; }
        .btn-train:hover { background: var(--purple); color: #fff; }
        .btn-ghost { background: transparent; color: var(--text-muted); border: 1px solid var(--border) !important; }
        .btn-ghost:hover { color: var(--text-main); border-color: var(--border-hover) !important; }

        form { display: grid; gap: 14px; font-size: 13px; }
        label { display: flex; flex-direction: column; gap: 6px; color: var(--text-muted); font-weight: 500; }
        input[type="text"], input[type="number"], select {
            background: var(--bg-body);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 9px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-family: inherit;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 8px var(--accent-glow);
        }

        /* Toast Notifications */
        #toast {
            position: fixed;
            bottom: 24px;
            right: 28px;
            background: var(--bg-card-subtle);
            color: var(--text-main);
            border: 1px solid var(--accent);
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            font-size: 13px;
            font-weight: 500;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        #toast.show { transform: translateY(0); opacity: 1; }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="brand">
            <div class="logo-icon">&#128065;</div>
            <div>
                <h1>EventWatchdog<span class="sub">Intelligent Observability</span></h1>
            </div>
        </div>

        <nav class="primary-nav">
            <button class="nav-btn active" id="btn-view-ops" onclick="switchMainView('ops')">
                &#128680; Live Operations
                <span class="badge-counter" id="active-incidents-count" style="display: none;">0</span>
            </button>
            <button class="nav-btn" id="btn-view-config" onclick="switchMainView('config')">
                &#9881; Policies & Configuration
            </button>
        </nav>

        <div class="header-actions">
            <div class="status-pill">
                <div class="status-dot"></div>
                <span id="health-label">System Healthy</span>
            </div>
            <a href="/docs" target="_blank" class="link-btn">&#128214; OpenAPI Docs</a>
            <a id="grafana-link" href="http://127.0.0.1:3000" target="_blank" class="link-btn">&#128202; Grafana</a>
        </div>
    </header>

    <main>
        <!-- ========================================== -->
        <!-- VIEW 1: LIVE OPERATIONS & MONITORING       -->
        <!-- ========================================== -->
        <section id="view-ops" class="view-section active">
            <div class="sub-tab-bar">
                <div class="sub-tabs">
                    <button class="sub-tab-btn active" onclick="switchOpsTab('incidents')">&#128680; Incidents & Alerts</button>
                    <button class="sub-tab-btn" onclick="switchOpsTab('metrics')">&#128202; Metric Catalog (<span id="metrics-count">0</span>)</button>
                    <button class="sub-tab-btn" onclick="switchOpsTab('audit')">&#128220; Detection Audit Trail</button>
                </div>
                <button class="btn-primary" onclick="refreshCurrentOps()">&#8635; Refresh View</button>
            </div>

            <!-- Tab 1.1: Incidents & Alerts -->
            <div id="ops-incidents" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2>Authoritative Incidents Register</h2>
                            <p>Real-time lifecycle triage (Open, Acknowledged, and Auto-Resolved anomalies & breaches).</p>
                        </div>
                    </div>
                    
                    <div class="filter-bar">
                        <div class="chip-group">
                            <button class="chip active" onclick="filterIncidents('ALL', this)">All</button>
                            <button class="chip" onclick="filterIncidents('OPEN', this)">Open</button>
                            <button class="chip" onclick="filterIncidents('ACKNOWLEDGED', this)">Acknowledged</button>
                            <button class="chip" onclick="filterIncidents('RESOLVED', this)">Resolved</button>
                        </div>
                        <input type="text" class="search-input" id="search-incidents" placeholder="Filter by metric name or summary..." oninput="renderIncidents()" />
                    </div>

                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Type</th>
                                    <th>Target Metric</th>
                                    <th>Severity</th>
                                    <th>Status</th>
                                    <th>Observed</th>
                                    <th>Expected</th>
                                    <th>Occurrences</th>
                                    <th>Last Seen</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="incidents-body">
                                <tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 30px;">Loading incidents...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab 1.2: Discovered Metric Catalog (No Endless Scroll!) -->
            <div id="ops-metrics" class="tab-content" style="display: none;">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2>Discovered Metric Series Catalog</h2>
                            <p>Active telemetry collected via Telegraf, Application Logs, and VictoriaMetrics.</p>
                        </div>
                        <div style="font-size: 13px; color: var(--text-muted);">
                            Showing <strong id="catalog-visible-count">0</strong> series
                        </div>
                    </div>

                    <div class="filter-bar">
                        <input type="text" class="search-input" id="search-metrics" placeholder="Search metric name (e.g. cpu, latency, mem)..." oninput="filterMetricCatalog()" />
                        <div class="chip-group">
                            <button class="chip active" onclick="filterMetricCategory('ALL', this)">All</button>
                            <button class="chip" onclick="filterMetricCategory('HOST', this)">Host (Telegraf)</button>
                            <button class="chip" onclick="filterMetricCategory('APP', this)">Application Logs</button>
                            <button class="chip" onclick="filterMetricCategory('ENROLLED', this)">Enrolled / Rules</button>
                        </div>
                    </div>

                    <div class="bounded-scroll">
                        <table>
                            <thead>
                                <tr>
                                    <th>Metric Name</th>
                                    <th>Category Source</th>
                                    <th>Static Rule</th>
                                    <th>Anomaly Model</th>
                                    <th>Quick Configure</th>
                                </tr>
                            </thead>
                            <tbody id="metrics-body">
                                <tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 30px;">Discovering metrics...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab 1.3: Audit Trail -->
            <div id="ops-audit" class="tab-content" style="display: none;">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2>Detection & Incident Audit Log</h2>
                            <p>Authoritative audit trail of breaches, acknowledgments, resolutions, and model training runs.</p>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Entity</th>
                                    <th>ID</th>
                                    <th>Action</th>
                                    <th>Event Details</th>
                                </tr>
                            </thead>
                            <tbody id="audit-body">
                                <tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 30px;">Loading audit trail...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <!-- ========================================== -->
        <!-- VIEW 2: POLICIES & CONFIGURATION           -->
        <!-- ========================================== -->
        <section id="view-config" class="view-section">
            <div class="sub-tab-bar">
                <div class="sub-tabs">
                    <button class="sub-tab-btn active" onclick="switchConfigTab('rules')">&#9889; Static Threshold Rules</button>
                    <button class="sub-tab-btn" onclick="switchConfigTab('models')">&#129504; Statistical Anomaly Models</button>
                </div>
                <button class="btn-primary" onclick="refreshCurrentConfig()">&#8635; Refresh Configuration</button>
            </div>

            <!-- Tab 2.1: Static Threshold Rules -->
            <div id="config-rules" class="tab-content">
                <div class="grid-split">
                    <!-- Configured Rules List -->
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <h2>Configured Static Monitors</h2>
                                <p>Rules evaluated against TSDB time-series on a scheduled window.</p>
                            </div>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Target Metric</th>
                                        <th>Condition</th>
                                        <th>Severity</th>
                                        <th>Status</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="rules-body">
                                    <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">Loading static rules...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Create Rule Form -->
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <h2>Create Static Threshold Rule</h2>
                                <p>Trigger static breaches when values cross defined bounds.</p>
                            </div>
                        </div>
                        <form id="create-rule-form" onsubmit="handleCreateRule(event)">
                            <label>Rule Name
                                <input type="text" id="rule-name" required placeholder="High Error Rate Alert" />
                            </label>
                            <label>Target Metric Name
                                <input type="text" id="rule-metric" required placeholder="app_log_errors_total" />
                            </label>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <label>Operator
                                    <select id="rule-op">
                                        <option value=">">&gt; (Greater than)</option>
                                        <option value=">=">&gt;= (Greater or equal)</option>
                                        <option value="<">&lt; (Less than)</option>
                                        <option value="<=">&lt;= (Less or equal)</option>
                                    </select>
                                </label>
                                <label>Threshold Value
                                    <input type="number" step="any" id="rule-threshold" required placeholder="5.0" />
                                </label>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <label>Severity
                                    <select id="rule-severity">
                                        <option value="CRITICAL">CRITICAL</option>
                                        <option value="WARNING">WARNING</option>
                                        <option value="INFO">INFO</option>
                                    </select>
                                </label>
                                <label>Evaluation Window (s)
                                    <input type="number" id="rule-window" value="60" min="15" />
                                </label>
                            </div>
                            <button type="submit" class="btn-primary" style="margin-top: 8px;">Save Static Rule</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Tab 2.2: Anomaly Detection Models -->
            <div id="config-models" class="tab-content" style="display: none;">
                <div class="grid-split">
                    <!-- Enrolled Models List -->
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <h2>Enrolled Anomaly Models</h2>
                                <p>Dynamic statistical baselines and prediction bounds.</p>
                            </div>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Metric Name</th>
                                        <th>Strategy</th>
                                        <th>Status</th>
                                        <th>Active Bounds [Low, Up]</th>
                                        <th>Baseline</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="models-body">
                                    <tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">Loading anomaly models...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Enroll Model Form -->
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <h2>Enroll Metric Series for Anomaly Detection</h2>
                                <p>Compute automated bounds via Robust MAD or Rolling Z-Score.</p>
                            </div>
                        </div>
                        <form id="enroll-form" onsubmit="handleEnroll(event)">
                            <label>Target Metric Name
                                <input type="text" id="model-metric" required placeholder="payment_gateway_response_ms" />
                            </label>
                            <label>Statistical Strategy
                                <select id="model-strategy">
                                    <option value="robust_mad">Robust MAD (Median Absolute Deviation)</option>
                                    <option value="rolling_zscore">Rolling Z-Score (Mean & StdDev)</option>
                                </select>
                            </label>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <label>Historical Samples
                                    <select id="model-history">
                                        <option value="2000">2,000 samples</option>
                                        <option value="4000">4,000 samples</option>
                                    </select>
                                </label>
                                <label>Bound Multiplier (k)
                                    <input type="number" step="0.5" id="model-mult" value="3.5" />
                                </label>
                            </div>
                            <button type="submit" class="btn-primary" style="margin-top: 8px;">Enroll & Initialize Model</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- Toast Component -->
    <div id="toast">Operation completed successfully</div>

    <script>
        // Resolve Grafana dynamic link
        const host = window.location.hostname || '127.0.0.1';
        document.getElementById('grafana-link').href = `http://${host}:3000`;

        // State caches
        let allIncidents = [];
        let currentIncidentFilter = 'ALL';
        let allMetrics = [];
        let currentMetricCategory = 'ALL';

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3500);
        }

        // View Switcher (Ops vs Config)
        function switchMainView(view) {
            document.getElementById('view-ops').classList.toggle('active', view === 'ops');
            document.getElementById('view-config').classList.toggle('active', view === 'config');
            document.getElementById('btn-view-ops').classList.toggle('active', view === 'ops');
            document.getElementById('btn-view-config').classList.toggle('active', view === 'config');

            if (view === 'ops') refreshCurrentOps();
            else refreshCurrentConfig();
        }

        // Sub Tab Switchers
        function switchOpsTab(tab) {
            const tabs = ['incidents', 'metrics', 'audit'];
            tabs.forEach(t => {
                document.getElementById(`ops-${t}`).style.display = (t === tab) ? 'block' : 'none';
            });
            document.querySelectorAll('#view-ops .sub-tab-btn').forEach((btn, idx) => {
                btn.classList.toggle('active', tabs[idx] === tab);
            });
            if (tab === 'incidents') loadIncidents();
            if (tab === 'metrics') loadMetrics();
            if (tab === 'audit') loadAudit();
        }

        function switchConfigTab(tab) {
            const tabs = ['rules', 'models'];
            tabs.forEach(t => {
                document.getElementById(`config-${t}`).style.display = (t === tab) ? 'block' : 'none';
            });
            document.querySelectorAll('#view-config .sub-tab-btn').forEach((btn, idx) => {
                btn.classList.toggle('active', tabs[idx] === tab);
            });
            if (tab === 'rules') loadRules();
            if (tab === 'models') loadModels();
        }

        function refreshCurrentOps() {
            loadIncidents();
            loadMetrics();
            loadAudit();
        }

        function refreshCurrentConfig() {
            loadRules();
            loadModels();
        }

        // Quick prefill transitions from Catalog to Config
        function prefillRule(metric) {
            switchMainView('config');
            switchConfigTab('rules');
            document.getElementById('rule-metric').value = metric;
            document.getElementById('rule-name').value = 'Monitor for ' + metric;
            showToast(`Pre-filled rule form for ${metric}`);
        }

        function prefillEnroll(metric) {
            switchMainView('config');
            switchConfigTab('models');
            document.getElementById('model-metric').value = metric;
            showToast(`Pre-filled anomaly enrollment for ${metric}`);
        }

        // --- 1. INCIDENTS ---
        async function loadIncidents() {
            try {
                const res = await fetch('/api/v1/incidents');
                allIncidents = await res.json();
                
                // Update badge
                const openCount = allIncidents.filter(i => i.state === 'OPEN').length;
                const counterPill = document.getElementById('active-incidents-count');
                if (openCount > 0) {
                    counterPill.innerText = openCount;
                    counterPill.style.display = 'inline-block';
                } else {
                    counterPill.style.display = 'none';
                }

                renderIncidents();
            } catch (err) {
                console.error(err);
            }
        }

        function filterIncidents(state, btn) {
            currentIncidentFilter = state;
            document.querySelectorAll('#ops-incidents .chip').forEach(c => c.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderIncidents();
        }

        function renderIncidents() {
            const tbody = document.getElementById('incidents-body');
            const search = document.getElementById('search-incidents').value.toLowerCase();
            
            let filtered = allIncidents.filter(inc => {
                const matchState = (currentIncidentFilter === 'ALL') || (inc.state === currentIncidentFilter);
                const matchSearch = inc.metric_name.toLowerCase().includes(search) || (inc.summary || '').toLowerCase().includes(search);
                return matchState && matchSearch;
            });

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 30px;">No matching incidents found.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(inc => `
                <tr>
                    <td><strong>#${inc.id}</strong></td>
                    <td><span class="badge badge-${inc.severity}">${inc.detection_type}</span></td>
                    <td><code>${inc.metric_name}</code></td>
                    <td><span class="badge badge-${inc.severity}">${inc.severity}</span></td>
                    <td><span class="badge badge-${inc.state}">${inc.state}</span></td>
                    <td><strong>${inc.latest_value !== null ? inc.latest_value.toFixed(2) : '-'}</strong></td>
                    <td style="color: var(--text-muted);">${inc.expected_value !== null ? inc.expected_value.toFixed(2) : '-'}</td>
                    <td>${inc.occurrence_count}</td>
                    <td>${new Date(inc.last_seen_at).toLocaleTimeString()}</td>
                    <td>
                        ${inc.state === 'OPEN' ? `<button class="btn-sm btn-ack" onclick="acknowledgeIncident(${inc.id})">Acknowledge</button>` : ''}
                        ${inc.state !== 'RESOLVED' ? `<button class="btn-sm btn-resolve" onclick="resolveIncident(${inc.id})">Resolve</button>` : '<span style="color: var(--text-dim);">&#10003; Closed</span>'}
                    </td>
                </tr>
            `).join('');
        }

        async function acknowledgeIncident(id) {
            await fetch(`/api/v1/incidents/${id}/acknowledge`, { method: 'POST' });
            showToast(`Incident #${id} acknowledged`);
            loadIncidents();
        }

        async function resolveIncident(id) {
            await fetch(`/api/v1/incidents/${id}/resolve`, { method: 'POST' });
            showToast(`Incident #${id} resolved`);
            loadIncidents();
        }

        // --- 2. METRICS CATALOG (Clean Search + Bounded Scroll) ---
        async function loadMetrics() {
            try {
                const res = await fetch('/api/v1/metrics/discovered');
                allMetrics = await res.json();
                document.getElementById('metrics-count').innerText = allMetrics.length;
                filterMetricCatalog();
            } catch (err) {
                console.error(err);
            }
        }

        function filterMetricCategory(cat, btn) {
            currentMetricCategory = cat;
            document.querySelectorAll('#ops-metrics .chip').forEach(c => c.classList.remove('active'));
            if (btn) btn.classList.add('active');
            filterMetricCatalog();
        }

        function filterMetricCatalog() {
            const query = (document.getElementById('search-metrics').value || '').toLowerCase();
            const tbody = document.getElementById('metrics-body');

            let filtered = allMetrics.filter(m => {
                const name = m.metric_name.toLowerCase();
                const matchSearch = name.includes(query);
                
                let matchCat = true;
                if (currentMetricCategory === 'HOST') {
                    matchCat = name.startsWith('cpu_') || name.startsWith('mem_') || name.startsWith('disk') || name.startsWith('net_') || name.startsWith('system_');
                } else if (currentMetricCategory === 'APP') {
                    matchCat = name.startsWith('app_');
                } else if (currentMetricCategory === 'ENROLLED') {
                    matchCat = m.has_rule || m.has_anomaly_model;
                }
                return matchSearch && matchCat;
            });

            document.getElementById('catalog-visible-count').innerText = filtered.length;

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 30px;">No metrics match filter.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(m => `
                <tr>
                    <td><code>${m.metric_name}</code></td>
                    <td style="color: var(--text-muted);">${m.source}</td>
                    <td>${m.has_rule ? '<span class="badge badge-TRAINED">&#9989; Configured</span>' : '<span style="color: var(--text-dim);">&#8212;</span>'}</td>
                    <td>${m.has_anomaly_model ? '<span class="badge badge-TRAINED">&#9989; Enrolled</span>' : '<span style="color: var(--text-dim);">&#8212;</span>'}</td>
                    <td>
                        <button class="btn-sm btn-ghost" onclick="prefillRule('${m.metric_name}')">+ Rule</button>
                        <button class="btn-sm btn-ghost" onclick="prefillEnroll('${m.metric_name}')">+ Anomaly</button>
                    </td>
                </tr>
            `).join('');
        }

        // --- 3. AUDIT TRAIL ---
        async function loadAudit() {
            try {
                const res = await fetch('/api/v1/detections');
                const data = await res.json();
                const tbody = document.getElementById('audit-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 30px;">No audit events recorded yet.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(a => `
                    <tr>
                        <td style="color: var(--text-muted);">${new Date(a.timestamp).toLocaleString()}</td>
                        <td><span class="badge badge-INFO">${a.entity_type}</span></td>
                        <td>#${a.entity_id || '-'}</td>
                        <td><strong>${a.action}</strong></td>
                        <td style="font-size: 12px; color: var(--text-muted);">${a.details || '-'}</td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        // --- 4. STATIC RULES CONFIG ---
        async function loadRules() {
            try {
                const res = await fetch('/api/v1/monitors');
                const data = await res.json();
                const tbody = document.getElementById('rules-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">No rules configured.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td><strong>${r.name}</strong></td>
                        <td><code>${r.metric_name}</code></td>
                        <td>${r.comparison_operator} ${r.threshold}</td>
                        <td><span class="badge badge-${r.severity}">${r.severity}</span></td>
                        <td><span class="badge ${r.enabled ? 'badge-TRAINED' : 'badge-FAILED'}">${r.enabled ? 'Active' : 'Disabled'}</span></td>
                        <td>
                            <button class="btn-sm btn-ghost" onclick="toggleRule(${r.id}, ${!r.enabled})">${r.enabled ? 'Disable' : 'Enable'}</button>
                            <button class="btn-sm btn-ghost" style="color: var(--danger);" onclick="deleteRule(${r.id})">&#128465;</button>
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
            showToast(`Rule updated`);
            loadRules();
        }

        async function deleteRule(id) {
            if (!confirm('Are you sure you want to delete this static monitor rule?')) return;
            await fetch(`/api/v1/monitors/${id}`, { method: 'DELETE' });
            showToast(`Rule deleted`);
            loadRules();
            loadMetrics();
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
                showToast(`Static Rule created successfully`);
                loadRules();
                loadMetrics();
            } else {
                const err = await res.json();
                alert('Rule creation error: ' + (err.detail || 'Error'));
            }
        }

        // --- 5. ANOMALY MODELS CONFIG ---
        async function loadModels() {
            try {
                const res = await fetch('/api/v1/models');
                const data = await res.json();
                const tbody = document.getElementById('models-body');
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">No anomaly models enrolled.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(m => {
                    const bounds = m.active_model ? `[${m.active_model.lower_bound.toFixed(1)}, ${m.active_model.upper_bound.toFixed(1)}]` : '<span style="color: var(--text-dim);">Awaiting Train</span>';
                    const baseline = m.active_model ? `${m.active_model.baseline_expected.toFixed(1)} ms` : '-';
                    return `
                    <tr>
                        <td><strong>#${m.id}</strong></td>
                        <td><code>${m.metric_name}</code></td>
                        <td>${m.model_strategy} (k=${m.bound_multiplier})</td>
                        <td><span class="badge badge-${m.model_status}">${m.model_status}</span></td>
                        <td>${bounds}</td>
                        <td style="color: var(--accent);">${baseline}</td>
                        <td>
                            <button class="btn-sm btn-train" onclick="triggerTrain(${m.id})">Train</button>
                            <button class="btn-sm btn-ghost" onclick="toggleEnroll(${m.id}, ${!m.enabled})">${m.enabled ? 'Disable' : 'Enable'}</button>
                        </td>
                    </tr>
                `}).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function triggerTrain(id) {
            showToast(`Training model #${id}...`);
            const res = await fetch('/api/v1/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enrollment_id: id })
            });
            if (res.ok) {
                const data = await res.json();
                showToast(`Model v${data.version} trained! Expected baseline: ${data.baseline_expected.toFixed(2)}`);
                loadModels();
                loadAudit();
            } else {
                const err = await res.json();
                alert('Training failed: ' + (err.detail || 'Insufficient historical samples in VictoriaMetrics'));
            }
        }

        async function toggleEnroll(id, enabled) {
            await fetch(`/api/v1/models/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabled })
            });
            showToast(`Enrollment updated`);
            loadModels();
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
                showToast(`Metric enrolled! Click Train to calculate baselines.`);
                loadModels();
                loadMetrics();
            } else {
                const err = await res.json();
                alert('Enrollment error: ' + (err.detail || 'Error'));
            }
        }

        // Initial Load
        loadIncidents();
        loadMetrics();
        loadAudit();
        setInterval(loadIncidents, 10000); // Periodic live refresh for incidents

        // URL Deep Linking
        function handleDeepLink() {
            const params = new URLSearchParams(window.location.search);
            const view = params.get('view');
            const tab = params.get('tab') || window.location.hash.replace('#', '');
            if (view === 'config' || tab === 'rules' || tab === 'models') {
                switchMainView('config');
                if (tab === 'models') switchConfigTab('models');
                else if (tab === 'rules') switchConfigTab('rules');
            } else if (tab === 'metrics') {
                switchOpsTab('metrics');
            } else if (tab === 'audit') {
                switchOpsTab('audit');
            }
        }
        handleDeepLink();
        window.addEventListener('hashchange', handleDeepLink);
    </script>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def get_console_ui():
    """Renders the comprehensive EventWatchdog Management & Incident Triage Console."""
    return HTMLResponse(content=HTML_CONTENT)
