from datetime import datetime
from core.models import DriftStats, Rule
import random


def analyze_rule(rule: Rule, fp_rate: float, tp_rate: float, alert_volume: int) -> DriftStats:
    """
    Analyze a SIEM rule and return drift statistics.

    Args:
        rule (Rule): The detection rule object.
        fp_rate (float): False positive rate.
        tp_rate (float): True positive rate.
        alert_volume (int): Number of alerts.

    Returns:
        DriftStats: Drift statistics for the rule.
    """

    # Example drift score calculation (you can refine this later)
    drift_score = round((1 - tp_rate) * 5 + fp_rate * 5, 2)

    return DriftStats(
        rule_id=rule.id,
        fp_rate=fp_rate,
        tp_rate=tp_rate,
        alert_volume=alert_volume,
        drift_score=drift_score,
        last_checked=datetime.utcnow(),
        drift_type="rule"
    )

