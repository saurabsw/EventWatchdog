import json
import os
import yaml
import pytest


def test_grafana_datasource_provisioning_file():
    ds_path = os.path.join("grafana", "provisioning", "datasources", "datasource.yml")
    assert os.path.exists(ds_path), f"Datasource provisioning file missing: {ds_path}"

    with open(ds_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "datasources" in config
    ds_list = config["datasources"]
    assert len(ds_list) >= 1

    vm_ds = next((d for d in ds_list if d.get("name") == "VictoriaMetrics"), None)
    assert vm_ds is not None, "VictoriaMetrics datasource not defined"
    assert vm_ds["type"] == "prometheus", "Type must be prometheus compatible"
    assert "url" in vm_ds
    assert vm_ds.get("isDefault") is True


def test_grafana_dashboards_provisioning_config():
    prov_path = os.path.join("grafana", "provisioning", "dashboards", "dashboards.yml")
    assert os.path.exists(prov_path), f"Dashboards provisioning file missing: {prov_path}"

    with open(prov_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "providers" in config
    assert len(config["providers"]) >= 1
    provider = config["providers"][0]
    assert provider["type"] == "file"
    assert "/etc/grafana/dashboards" in provider["options"]["path"]


def test_grafana_dashboard_json_files_validity():
    required_dashboards = [
        "collection-health.json",
        "anomaly-detection.json",
        "alerts-incidents.json"
    ]

    for d_name in required_dashboards:
        d_path = os.path.join("grafana", "dashboards", d_name)
        assert os.path.exists(d_path), f"Required dashboard missing: {d_path}"

        with open(d_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "title" in data, f"Dashboard {d_name} missing title"
        assert "uid" in data, f"Dashboard {d_name} missing uid"
        assert "panels" in data, f"Dashboard {d_name} missing panels list"
        assert len(data["panels"]) >= 1, f"Dashboard {d_name} has no panels"

        # Check each panel targets VictoriaMetrics datasource
        for panel in data["panels"]:
            targets = panel.get("targets", [])
            for target in targets:
                ds = target.get("datasource", {})
                assert ds.get("type") == "prometheus"
                assert "expr" in target
