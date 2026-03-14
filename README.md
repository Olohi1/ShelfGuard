# ShelfGuard 🛒
### Inventory Anomaly & Shrinkage Detector

ShelfGuard is an AI-assisted data pipeline that automatically detects inventory anomalies — including theft, spoilage, pricing issues, and demand shifts — from retail store data.

---

## Project Structure

```
shelfguard/
├── data/
│   ├── raw/                        # Input CSV files go here
│   ├── processed/                  # Cleaned and enriched data
│   └── reports/                    # Generated JSON reports
├── pipeline/
│   ├── ingestor.py                 # Step 1: Load & validate CSV
│   ├── normalizer.py               # Step 2: Clean & enrich records
│   ├── rule_engine.py              # Step 3a: Detect anomalies
│   └── classifier.py              # Step 3b: Label anomaly type
├── ai/                             # AI enrichment module
├── api/                            # FastAPI backend
├── dashboard/                      # Frontend UI
├── config.py                       # Settings & thresholds
├── main.py                         # Pipeline entry point
└── requirements.txt
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your data
cp your_inventory_file.csv data/raw/

# 3. Run the pipeline
python main.py

# 4. Optional: quick demo run on 5000 records
python main.py --sample 5000
```

---

## How It Works

**Step 1 — Ingest:** Loads the raw CSV, validates all columns and data types, flags bad rows.

**Step 2 — Normalize:** Computes derived fields — sales discrepancy vs forecast, financial impact, inventory health signals, competitor pricing pressure.

**Step 3 — Detect:** Applies 11 business rules across every record, scoring each one and assigning a severity level (Critical / High / Medium / Low).

**Step 4 — Classify:** Maps flag combinations to an anomaly type with a plain-English rationale.

**Step 5 — Report:** Outputs the top 50 anomalies as a structured JSON report.

---

## Anomaly Types Detected

| Type | Description |
|------|-------------|
| THEFT | High-value item with unexplained stock loss |
| SPOILAGE | Grocery items not selling before expiry |
| PROMO_FAILURE | Promotion active but sales still fell short |
| PRICING_ISSUE | Competitor undercutting causing lost sales |
| STOCK_MISMANAGEMENT | Low stock with no reorder placed |
| DEMAND_ANOMALY | Sales wildly different from forecast |
| ADMIN_ERROR | Large discrepancy likely from data entry |

---

## Dataset

Uses the [Retail Store Inventory Dataset](https://www.kaggle.com/datasets/sandhyapeesara/retail-store-inventory) from Kaggle — 73,100 records across 5 stores, 20 products, 5 categories, and 2 years of daily data.

---

