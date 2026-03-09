"""
ingestor.py
-----------
Step 1 of the ShelfGuard pipeline.
Loads the raw inventory CSV, validates structure,
and flags any records with data quality issues.
"""

import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "Date", "Store ID", "Product ID", "Category", "Region",
    "Inventory Level", "Units Sold", "Units Ordered",
    "Demand Forecast", "Price", "Discount",
    "Weather Condition", "Holiday/Promotion",
    "Competitor Pricing", "Seasonality",
]

NUMERIC_COLUMNS = [
    "Inventory Level", "Units Sold", "Units Ordered",
    "Demand Forecast", "Price", "Discount", "Competitor Pricing",
]


def ingest(filepath: str) -> pd.DataFrame:
    """
    Load and validate the raw inventory CSV.
    Returns a clean DataFrame ready for normalization.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {path.suffix}")

    logger.info(f"Loading file: {filepath}")
    df = pd.read_csv(filepath)

    # Check all required columns exist
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Remove completely empty rows
    before = len(df)
    df.dropna(how="all", inplace=True)
    removed = before - len(df)
    if removed:
        logger.warning(f"Removed {removed} empty rows.")

    # Coerce numeric columns — invalid values become NaN
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag rows with bad numeric data
    bad_rows = df[NUMERIC_COLUMNS].isnull().any(axis=1)
    df["ingestion_flag"] = bad_rows.map({True: "INVALID_NUMERIC", False: None})
    if bad_rows.sum():
        logger.warning(f"{bad_rows.sum()} rows flagged for invalid numeric values.")

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad_dates = df["Date"].isnull().sum()
    if bad_dates:
        logger.warning(f"{bad_dates} rows have unparseable dates.")

    logger.info(f"Ingestion complete — {len(df):,} records loaded.")
    return df


def summarize(df: pd.DataFrame) -> dict:
    """Return a high-level summary of the ingested dataset."""
    return {
        "total_records":   len(df),
        "stores":          df["Store ID"].nunique(),
        "products":        df["Product ID"].nunique(),
        "categories":      sorted(df["Category"].unique().tolist()),
        "regions":         sorted(df["Region"].unique().tolist()),
        "date_range": {
            "start": str(df["Date"].min().date()),
            "end":   str(df["Date"].max().date()),
        },
        "flagged_records": int(df["ingestion_flag"].notnull().sum()),
    }
