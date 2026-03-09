"""
classifier.py
-------------
Step 3b of the ShelfGuard pipeline.
Maps anomaly flag combinations to a human-readable
shrinkage/anomaly type with a plain-English rationale.
"""

import logging
from config import ANOMALY_TYPES, THRESHOLDS

logger = logging.getLogger(__name__)


def classify(record: dict) -> dict:
    """
    Classify a single anomaly record into a shrinkage type.
    Priority-ordered rules determine the most likely cause.
    """
    flags    = record.get("anomaly_flags", [])
    category = record.get("Category", "")
    is_high_value    = record.get("is_high_value", False)
    is_on_promotion  = record.get("is_on_promotion", False)
    units_sold       = record.get("Units Sold", 0)
    inventory        = record.get("Inventory Level", 0)

    anomaly_type = "UNKNOWN"
    rationale    = ""

    # Priority 1 — Zero sales on high-value item with full shelves → theft
    if "ZERO_SALES_HIGH_STOCK" in flags and is_high_value:
        anomaly_type = "THEFT"
        rationale = (
            f"High-value item (${record.get('Price', 0):.2f}) recorded zero sales "
            f"despite {inventory} units in stock — unexplained stock loss suggests theft."
        )

    # Priority 2 — Grocery severely underselling → spoilage
    elif "GROCERY_SPOILAGE_RISK" in flags or (
        category in THRESHOLDS["spoilage_categories"] and "SEVERE_UNDERSELL" in flags
    ):
        anomaly_type = "SPOILAGE"
        rationale = (
            f"Grocery item sold {abs(record.get('sales_discrepancy_pct', 0)):.1f}% "
            f"below forecast — likely spoilage or expiry reducing sellable stock."
        )

    # Priority 3 — Promotion active but sales still fell short
    elif "PROMO_UNDERPERFORMANCE" in flags:
        anomaly_type = "PROMO_FAILURE"
        rationale = (
            f"Promotional period active but sales were "
            f"{abs(record.get('sales_discrepancy_pct', 0)):.1f}% below forecast — "
            f"promotion failed to drive expected uplift."
        )

    # Priority 4 — High value item undercut by competitor
    elif "COMPETITOR_UNDERCUT_HIGH_VALUE" in flags and "HIGH_VALUE_UNDERSELL" in flags:
        anomaly_type = "PRICING_ISSUE"
        rationale = (
            f"Item priced at ${record.get('Price', 0):.2f} while competitor charges "
            f"${record.get('Competitor Pricing', 0):.2f} — lost sales to lower competitor price."
        )

    # Priority 5 — Low stock with no reorder placed
    elif "LOW_STOCK_NO_REORDER" in flags:
        anomaly_type = "STOCK_MISMANAGEMENT"
        rationale = (
            f"Only {inventory} units remaining with no reorder placed — "
            f"replenishment process failure risks stockout."
        )

    # Priority 6 — Severe oversell beyond forecast
    elif "SEVERE_OVERSELL" in flags:
        anomaly_type = "DEMAND_ANOMALY"
        rationale = (
            f"Sales exceeded forecast by "
            f"{record.get('sales_discrepancy_pct', 0):.1f}% — "
            f"unexpected demand spike not captured in forecast model."
        )

    # Priority 7 — Large financial discrepancy
    elif "HIGH_VALUE_DISCREPANCY" in flags:
        anomaly_type = "ADMIN_ERROR"
        rationale = (
            f"Financial discrepancy of ${record.get('discrepancy_value', 0):.2f} "
            f"without a clear operational cause — likely forecasting or data entry error."
        )

    # Priority 8 — General undersell
    elif "SEVERE_UNDERSELL" in flags or "MODERATE_UNDERSELL" in flags:
        anomaly_type = "DEMAND_ANOMALY"
        rationale = (
            f"Sales came in {abs(record.get('sales_discrepancy_pct', 0)):.1f}% "
            f"below forecast — possible demand shift, external factor, or model inaccuracy."
        )

    else:
        anomaly_type = "UNKNOWN"
        rationale = "Anomaly flagged but does not match a known pattern — manual review recommended."

    record["anomaly_type"]        = anomaly_type
    record["anomaly_description"] = ANOMALY_TYPES[anomaly_type]
    record["rationale"]           = rationale
    return record


def classify_all(records: list[dict]) -> list[dict]:
    """Classify a list of anomaly records."""
    classified = [classify(r) for r in records]
    logger.info(f"Classification complete — {len(classified)} records classified.")
    return classified
