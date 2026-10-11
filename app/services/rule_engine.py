import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models import MonitorRule
from app.core.tsdb_client import tsdb_client
from app.services.incident_mgr import incident_service

logger = logging.getLogger(__name__)


def evaluate_condition(val: float, op: str, threshold: float) -> bool:
    """Evaluate comparator."""
    if op == ">":
        return val > threshold
    if op == ">=":
        return val >= threshold
    if op == "<":
        return val < threshold
    if op == "<=":
        return val <= threshold
    if op == "==":
        return abs(val - threshold) < 1e-9
    if op == "!=":
        return abs(val - threshold) >= 1e-9
    return False


def build_promql_query(rule: MonitorRule) -> str:
    """Construct PromQL aggregation expression for the rule."""
    filters = []
    if rule.label_filters_json:
        try:
            labels_dict = json.loads(rule.label_filters_json)
            for k, v in labels_dict.items():
                filters.append(f'{k}="{v}"')
        except Exception:
            pass

    filter_str = "{" + ",".join(filters) + "}" if filters else ""
    window_s = f"{max(15, rule.evaluation_window_seconds)}s"

    agg = rule.aggregation_func.lower()
    if agg == "avg":
        return f"avg_over_time({rule.metric_name}{filter_str}[{window_s}])"
    if agg == "max":
        return f"max_over_time({rule.metric_name}{filter_str}[{window_s}])"
    if agg == "min":
        return f"min_over_time({rule.metric_name}{filter_str}[{window_s}])"
    if agg == "sum":
        return f"sum_over_time({rule.metric_name}{filter_str}[{window_s}])"
    if agg == "count":
        return f"count_over_time({rule.metric_name}{filter_str}[{window_s}])"
    # Default fallback to instant
    return f"{rule.metric_name}{filter_str}"


class RuleEngineService:
    """Evaluates static monitor rules against VictoriaMetrics."""

    async def evaluate_rule(self, db: Session, rule: MonitorRule) -> Dict[str, Any]:
        """Evaluate a single enabled monitor rule."""
        if not rule.enabled:
            return {"rule_id": rule.id, "status": "disabled"}

        query = build_promql_query(rule)
        res = await tsdb_client.query_instant(query)

        data = res.get("data", {})
        result_list = data.get("result", [])

        if not result_list:
            # No data in current window
            return {"rule_id": rule.id, "status": "no_data", "query": query}

        evaluation_results = []
        for item in result_list:
            labels = item.get("metric", {})
            labels.pop("__name__", None)
            value_entry = item.get("value", [0, "0"])
            try:
                val = float(value_entry[1])
            except (ValueError, TypeError, IndexError):
                continue

            breached = evaluate_condition(val, rule.comparison_operator, rule.threshold)

            if breached:
                summary = (
                    f"Rule '{rule.name}' breach on {rule.metric_name}: "
                    f"value {val:.2f} {rule.comparison_operator} threshold {rule.threshold:.2f}"
                )
                inc = incident_service.process_breach(
                    db=db,
                    detection_type="STATIC",
                    source_id=rule.id,
                    metric_name=rule.metric_name,
                    labels=labels,
                    severity=rule.severity,
                    summary=summary,
                    observed_value=val,
                    expected_value=rule.threshold
                )
                evaluation_results.append({"status": "breached", "incident_id": inc.id, "value": val})
            else:
                inc = incident_service.process_normal(
                    db=db,
                    detection_type="STATIC",
                    source_id=rule.id,
                    metric_name=rule.metric_name,
                    labels=labels,
                    required_recoveries=rule.consecutive_recoveries
                )
                evaluation_results.append({
                    "status": "normal",
                    "incident_resolved": inc.state == "RESOLVED" if inc else False,
                    "value": val
                })

        return {"rule_id": rule.id, "status": "evaluated", "results": evaluation_results}

    async def evaluate_all_rules(self, db: Session) -> List[Dict[str, Any]]:
        """Evaluate all active monitor rules."""
        rules = db.query(MonitorRule).filter(MonitorRule.enabled.is_(True)).all()
        results = []
        for r in rules:
            res = await self.evaluate_rule(db, r)
            results.append(res)
        return results


rule_engine_service = RuleEngineService()
