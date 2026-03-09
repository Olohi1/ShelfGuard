import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# API Keys
# ─────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─────────────────────────────────────────
# File Paths
# ─────────────────────────────────────────
RAW_DATA_PATH      = "data/raw/"
PROCESSED_DATA_PATH = "data/processed/"
REPORTS_PATH       = "data/reports/"
OUTPUTS_PATH       = "outputs/"

# ─────────────────────────────────────────
# Anomaly Detection Thresholds
# (tuned to real Kaggle dataset ranges)
# ─────────────────────────────────────────
THRESHOLDS = {
    # Sales vs forecast discrepancy
    "undersell_pct_moderate": -25.0,   # sold 25% below forecast = warning
    "undersell_pct_severe":   -40.0,   # sold 40% below forecast = critical
    "oversell_pct_moderate":   30.0,   # sold 30% above forecast = warning
    "oversell_pct_severe":     50.0,   # sold 50% above forecast = critical

    # Inventory
    "low_inventory_threshold": 80,     # below 80 units = low stock alert
    "zero_sales_min_stock":    100,    # zero sales but 100+ units in stock = suspicious

    # Pricing
    "high_value_price":        50.0,   # items above $50 = high value
    "high_discrepancy_value":  1000.0, # financial loss above $1000 = flag

    # Spoilage
    "spoilage_categories": ["Groceries"],
}

# ─────────────────────────────────────────
# Shrinkage / Anomaly Type Definitions
# ─────────────────────────────────────────
ANOMALY_TYPES = {
    "THEFT":              "Suspected theft or pilferage",
    "SPOILAGE":           "Product spoilage or expiry loss",
    "PROMO_FAILURE":      "Promotion did not drive expected sales uplift",
    "PRICING_ISSUE":      "Competitor pricing causing lost sales",
    "STOCK_MISMANAGEMENT":"Poor stock replenishment or reorder failure",
    "DEMAND_ANOMALY":     "Unexpected demand shift vs forecast",
    "ADMIN_ERROR":        "Likely forecasting or data entry error",
    "UNKNOWN":            "Unclassified anomaly — needs investigation",
}
