# Telegraf Setup, Operations & Verification Guide
## Intelligent Observability & Event Watchdog

This guide documents the installation, configuration, operational management, network routing, and troubleshooting for **Telegraf** on both native Windows development hosts and Linux / GCP Compute Engine VMs.

---

## 1. Architecture & Protocol Verification

- **Ingestion Protocol:** InfluxDB Line Protocol over HTTP POST.
- **VictoriaMetrics Target Endpoint:** `/write` on port `8428`.
- **Output Plugin:** `[[outputs.http]]`
- **Verification Result:** VictoriaMetrics natively accepts standard InfluxDB Line Protocol batches on `/write`. It translates Influx measurements `<measurement>_<field>` into standard Prometheus-compatible time-series metrics without requiring an InfluxDB server or translation proxy.

---

## 2. Windows Native Host Setup

Running Telegraf directly on the Windows host ensures measurements reflect actual host CPU, Memory, Disk, and Network performance (rather than measuring the Docker VM container).

### 2.1 Download & Installation
1. Download the official Telegraf Windows distribution zip package from InfluxData:
   ```powershell
   # In an administrative PowerShell terminal:
   Invoke-WebRequest -Uri "https://dl.influxdata.com/telegraf/releases/telegraf-1.30.0_windows_amd64.zip" -OutFile "$env:TEMP\telegraf.zip"
   Expand-Archive -Path "$env:TEMP\telegraf.zip" -DestinationPath "C:\Program Files\InfluxData\"
   Rename-Item -Path "C:\Program Files\InfluxData\telegraf-1.30.0" -NewName "Telegraf"
   ```
2. Copy the project's Windows configuration file:
   ```powershell
   Copy-Item "c:\Users\USER\Videos\EventWatchdog\telegraf\telegraf-windows.conf" "C:\Program Files\InfluxData\Telegraf\telegraf.conf"
   ```

### 2.2 Running & Testing in Foreground
Test the configuration and metric gathering before registering as a service:
```powershell
cd "C:\Program Files\InfluxData\Telegraf"
.\telegraf.exe --config .\telegraf.conf --test
```
You should see sample metrics output to console (e.g., `cpu,cpu=cpu-total usage_idle=...`, `mem used_percent=...`).

### 2.3 Managing as a Windows Service
Install and start Telegraf as an automated background Windows Service:
```powershell
# Install service
.\telegraf.exe --service install --config "C:\Program Files\InfluxData\Telegraf\telegraf.conf"

# Start service
Start-Service telegraf

# Check status
Get-Service telegraf

# Stop / Restart
Restart-Service telegraf
Stop-Service telegraf
```

---

## 3. Linux / GCP Compute Engine VM Setup

### 3.1 Installation (Ubuntu / Debian)
1. Add the InfluxData repository key and install Telegraf:
   ```bash
   sudo apt-get update && sudo apt-get install -y wget gnupg
   wget -q https://repos.influxdata.com/influxdata-archive_compat.key
   echo '393eadd02de3e8d7ceba804d49395ab871291f8e158351c16cf53304746456c6 influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
   echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
   sudo apt-get update && sudo apt-get install -y telegraf
   ```

2. Copy the Linux configuration:
   ```bash
   sudo cp telegraf/telegraf-linux.conf /etc/telegraf/telegraf.conf
   ```

3. Manage Systemd Service:
   ```bash
   # Enable and start
   sudo systemctl enable --now telegraf

   # Check status and logs
   sudo systemctl status telegraf
   sudo journalctl -u telegraf -f
   ```

---

## 4. Destination URL Configuration

In `telegraf.conf`, customize the `[[outputs.http]]` block based on your environment:

### Local Development (Windows $\rightarrow$ Local VictoriaMetrics)
```toml
[[outputs.http]]
  url = "http://127.0.0.1:8428/write"
  method = "POST"
  data_format = "influx"
  timeout = "5s"
```

### Remote Ingestion (External Host or Compute Engine VM)
If your EventWatchdog stack is running on a remote GCP server (e.g., `10.128.0.5` or `https://watchdog.example.internal`):
```toml
[[outputs.http]]
  url = "http://10.128.0.5:8428/write"
  method = "POST"
  data_format = "influx"
  timeout = "5s"
```

---

## 5. Verification: Confirming Metrics Arrive

### Step 1: Query VictoriaMetrics Directly
Query VictoriaMetrics instant PromQL endpoint for CPU metrics:
```powershell
# Using PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8428/api/v1/query?query=cpu_usage_idle"
```
Or with curl:
```bash
curl -G "http://127.0.0.1:8428/api/v1/query" --data-urlencode "query=cpu_usage_idle"
```
Expected output:
```json
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": { "__name__": "cpu_usage_idle", "cpu": "cpu-total", "environment": "local" },
        "value": [ 1700000000, "94.2" ]
      }
    ]
  }
}
```

### Step 2: Confirm in Grafana
1. Open [http://127.0.0.1:3000](http://127.0.0.1:3000) (Login: `admin` / `admin`).
2. Navigate to **Dashboards $\rightarrow$ Observability $\rightarrow$ Collection and Service Health**.
3. Confirm that **Host CPU Utilization (%)** and **Host Memory Used (%)** panels render active live graphs.

---

## 6. Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Service fails to start (`Access Denied`)** | Service account lacks permissions to write logs or read disk. | Run Command Prompt/PowerShell as **Administrator**. In Linux, ensure user is added to `telegraf` group. |
| **Connection Refused (`127.0.0.1:8428`)** | VictoriaMetrics container is not running or port 8428 is blocked. | Verify Docker status: `docker compose ps`. Check if port 8428 is listening: `netstat -ano \| findstr 8428`. |
| **Metrics not appearing in VictoriaMetrics** | Incorrect output data format configured. | Verify `telegraf.conf` contains `data_format = "influx"` inside `[[outputs.http]]`. |
| **Disk/Network permissions error on Windows** | Standard user cannot access Windows performance counters. | Ensure Telegraf service runs as `Local System` account. |
| **High network latency / drops to remote GCP VM** | Firewall rule blocks port 8428 or MTU issues. | Ensure GCP firewall allows TCP traffic on port 8428 from the source IP/VPC subnet. |
