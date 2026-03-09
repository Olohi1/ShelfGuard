"""
rule_engine.py
--------------
Step 3a of the ShelfGuard pipeline.
Applies 11 business rules to normalized inventory records
and assigns each record an anomaly severity score.
"""

import pandas as pd
import logging
from config import THRESHOLDS

logger = logging.getLogger(__name__)


# ── Rule Definitions ────────────────────────────────────────────────────────
# Each rule checks a condition and returns (flag_name, score) if triggered.

def _rule_severe_undersell(row):
    if row["sales_discrepancy_pct"] <= THRESHOLDS["undersell_pct_severe"]:
        return ("SEVERE_UNDERSELL", 40)

def _rule_moderate_undersell(row):
    if THRESHOLDS["undersell_pct_severe"] < row["sales_discrepancy_pct"] <= THRESHOLDS["undersell_pct_moderate"]:
        return ("MODERATE_UNDERSELL", 20)

def _rule_severe_oversell(row):
    if row["sales_discrepancy_pct"] >= THRESHOLDS["oversell_pct_severe"]:
        return ("SEVERE_OVERSELL", 35)

def _rule_moderate_oversell(row):
    if THRESHOLDS["oversell_pct_moderate"] <= row["sales_discrepancy_pct"] < THRESHOLDS["oversell_pct_severe"]:
        return ("MODERATE_OVERSELL", 15)

def _rule_high_value_undersell(row):
    if row["is_high_value"] and row["undersold"]:
        return ("HIGH_VALUE_UNDERSELL", 30)

def _rule_low_stock_no_reorder(row):
    if row["low_inventory"] and row["Units Ordered"] == 0:
        return ("LOW_STOCK_NO_REORDER", 25)

def _rule_competitor_undercut(row):
    if row["undercut_by_competitor"] and row["is_high_value"]:
        return ("COMPETITOR_UNDERCUT_HIGH_VALUE", 20)

def _rule_promo_underperformance(row):
    if row["is_on_promotion"] and row["undersold"]:
        return ("PROMO_UNDERPERFORMANCE", 30)

def _rule_high_value_discrepancy(row):
    if row["discrepancy_value"] > THRESHOLDS["high_discrepancy_value"]:
        return ("HIGH_VALUE_DISCREPANCY", 25)

def _rule_zero_sales_high_stock(row):
    if row["zero_sales_high_stock"]:
        return ("ZERO_SALES_HIGH_STOCK", 35)

def _rule_grocery_spoilage(row):
    if row["Category"] in THRESHOLDS["spoilage_categories"] and row["sales_discrepancy_pct"] <= -30:
        return ("GROCERY_SPOILAGE_RISK", 20)


RULES = [
    _rule_severe_undersell,
    _rule_moderate_undersell,
    _rule_severe_oversell,
    _rule_moderate_oversell,
    _rule_high_value_undersell,
    _rule_low_stock_no_reorder,
    _rule_competitor_undercut,
    _rule_promo_underperformance,
    _rule_high_value_discrepancy,
    _rule_zero_sales_high_stock,
    _rule_grocery_spoilage,
]


def _score_to_severity(score: int) -> str:
    if score >= 60:   return "CRITICAL"
    elif score >= 35: return "HIGH"
    elif score >= 15: return "MEDIUM"
    elif score > 0:   return "LOW"
    return "NORMAL"


# ── Main Engine ─────────────────────────────────────────────────────────────

def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all rules against every record.
    Adds anomaly_flags, severity, and severity_score columns.
    """
    df = df.copy()
    df["anomaly_flags"]  = [[] for _ in range(len(df))]
    df["severity"]       = "NORMAL"
    df["severity_score"] = 0

    for idx, row in df.iterrows():
        flags = []
        score = 0

        for rule in RULES:
            result = rule(row)
            if result:
                flag, points = result
                flags.append(flag)
                score += points

        df.at[idx, "anomaly_flags"]  = flags
        df.at[idx, "severity"]       = _score_to_severity(score)
        df.at[idx, "severity_score"] = score

    anomaly_count = (df["severity"] != "NORMAL").sum()
    logger.info(f"Rule engine complete — {anomaly_count:,} anomalies in {len(df):,} records.")
    return df


def get_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Return only flagged anomaly records."""
    return df[df["severity"] != "NORMAL"].copy()
