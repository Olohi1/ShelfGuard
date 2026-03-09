"""
main.py
-------
ShelfGuard entry point.
Runs the full Day 1 pipeline:
  Ingest → Normalize → Detect → Classify → Report

Usage:
  python main.py                          # run on full dataset
  python main.py --sample 5000           # quick demo run
  python main.py --ai                    # enable AI enrichment (Day 2)
"""

import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

from pipeline import ingest, summarize, normalize, to_records, apply_rules, get_anomalies, classify_all
from config import REPORTS_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("shelfguard")


def run_pipeline(filepath: str, enrich_with_ai: bool = False, sample: int = None) -> dict:
    """Execute the full ShelfGuard pipeline and return the generated report."""

    logger.info("━" * 55)
    logger.info("  ShelfGuard — Inventory Anomaly Detector")
    logger.info("━" * 55)

    # ── Step 1: Ingest ───────────────────────────────────────
    raw_df = ingest(filepath)
    if sample:
        raw_df = raw_df.sample(n=min(sample, len(raw_df)), random_state=42)
        logger.info(f"Demo mode: sampled {len(raw_df):,} records.")

    dataset_summary = summarize(raw_df)
    logger.info(f"Summary: {dataset_summary}")

    # ── Step 2: Normalize ────────────────────────────────────
    normalized_df = normalize(raw_df)

    # ── Step 3: Detect anomalies ─────────────────────────────
    flagged_df   = apply_rules(normalized_df)
    anomalies_df = get_anomalies(flagged_df)

    # ── Step 4: Classify top 50 by severity ──────────────────
    all_anomaly_records = to_records(anomalies_df)
    all_anomaly_records.sort(key=lambda x: x.get("severity_score", 0), reverse=True)
    top_50 = all_anomaly_records[:50]
    classified = classify_all(top_50)

    # ── Step 5: AI Enrichment (Day 2) ────────────────────────
    if enrich_with_ai:
        from ai.enricher import enrich_all
        logger.info("Running AI enrichment...")
        classified = enrich_all(classified)

    # ── Build Report ─────────────────────────────────────────
    report = {
        "report_id":               f"SG-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "generated_at":            datetime.now().isoformat(),
        "source_file":             filepath,
        "dataset_summary":         dataset_summary,
        "total_records_scanned":   len(flagged_df),
        "total_anomalies_detected":len(anomalies_df),
        "anomalies_in_report":     len(classified),
        "severity_breakdown":      _count_by(all_anomaly_records, "severity"),
        "anomaly_type_breakdown":  _count_by(classified, "anomaly_type"),
        "top_anomalies":           classified,
    }

    # ── Save Report ──────────────────────────────────────────
    Path(REPORTS_PATH).mkdir(parents=True, exist_ok=True)
    report_path = f"{REPORTS_PATH}{report['report_id']}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Report saved → {report_path}")
    logger.info("━" * 55)
    return report


def _count_by(records: list[dict], key: str) -> dict:
    counts = {}
    for r in records:
        val = r.get(key, "UNKNOWN")
        counts[val] = counts.get(val, 0) + 1
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShelfGuard — Inventory Anomaly Detector")
    parser.add_argument("--file",   default="data/raw/retail_store_inventory_data.csv")
    parser.add_argument("--sample", type=int, default=None, help="Sample N records for quick runs")
    parser.add_argument("--ai",     action="store_true",    help="Enable AI enrichment (Day 2)")
    args = parser.parse_args()

    report = run_pipeline(args.file, enrich_with_ai=args.ai, sample=args.sample)

    print()
    print("━" * 55)
    print(f"  Report ID          : {report['report_id']}")
    print(f"  Records Scanned    : {report['total_records_scanned']:,}")
    print(f"  Anomalies Detected : {report['total_anomalies_detected']:,}")
    print(f"  Severity Breakdown : {report['severity_breakdown']}")
    print(f"  Anomaly Types      : {report['anomaly_type_breakdown']}")
    print(f"  Report Saved To    : data/reports/{report['report_id']}.json")
    print("━" * 55)
