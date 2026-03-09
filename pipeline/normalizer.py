"""
normalizer.py
-------------
Step 2 of the ShelfGuard pipeline.
Transforms raw ingested data into enriched, analysis-ready records
by computing derived fields that power the rule engine.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich the ingested DataFrame.
    Adds derived fields for anomaly detection.
    """
    df = df.copy()

    # ── Standardize text fields ──────────────────────────────
    df["Store ID"]         = df["Store ID"].str.strip().str.upper()
    df["Product ID"]       = df["Product ID"].str.strip().str.upper()
    df["Category"]         = df["Category"].str.strip().str.title()
    df["Region"]           = df["Region"].str.strip().str.title()
    df["Weather Condition"]= df["Weather Condition"].str.strip().str.title()
    df["Seasonality"]      = df["Seasonality"].str.strip().str.title()

    # ── Sales performance vs forecast ────────────────────────
    df["sales_discrepancy"]     = df["Units Sold"] - df["Demand Forecast"]
    df["sales_discrepancy_pct"] = (
        df["sales_discrepancy"] / df["Demand Forecast"].replace(0, 1)
    ) * 100

    # ── Inventory health ─────────────────────────────────────
    df["low_inventory"]       = df["Inventory Level"] < 80
    df["zero_sales_high_stock"]= (df["Units Sold"] == 0) & (df["Inventory Level"] > 100)

    # ── Demand flags ─────────────────────────────────────────
    df["oversold"]  = df["Units Sold"] > df["Demand Forecast"] * 1.3
    df["undersold"] = df["Units Sold"] < df["Demand Forecast"] * 0.6

    # ── Pricing signals ──────────────────────────────────────
    df["is_high_value"]          = df["Price"] >= 50.0
    df["price_vs_competitor"]    = df["Price"] - df["Competitor Pricing"]
    df["undercut_by_competitor"] = df["price_vs_competitor"] > 0
    df["discount_applied"]       = df["Discount"] > 0

    # ── Promotion context ────────────────────────────────────
    df["is_on_promotion"] = df["Holiday/Promotion"] == 1

    # ── Financial impact ─────────────────────────────────────
    df["discrepancy_value"] = df["sales_discrepancy"].abs() * df["Price"]

    # ── Date features ────────────────────────────────────────
    df["day_of_week"]  = df["Date"].dt.day_name()
    df["month"]        = df["Date"].dt.month
    df["week_number"]  = df["Date"].dt.isocalendar().week.astype(int)
    df["year"]         = df["Date"].dt.year

    logger.info(f"Normalization complete — {len(df):,} records enriched.")
    return df


def to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a normalized DataFrame to a list of dicts."""
    return df.to_dict(orient="records")
