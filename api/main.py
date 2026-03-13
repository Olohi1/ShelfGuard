"""
api/main.py
-----------
Day 3 of the ShelfGuard pipeline.
FastAPI backend that exposes the pipeline as a REST API.
"""

import json
import os
import sys
import math
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add parent directory to path so pipeline imports work
sys.path.append(str(Path(__file__).parent.parent))

from pipeline import ingest, summarize, normalize, to_records, apply_rules, get_anomalies, classify_all
from config import REPORTS_PATH


class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NaN and other non-serializable values."""
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj):
                return None
            elif math.isinf(obj):
                return None
        return super().default(obj)


def safe_json_load(filepath):
    """Load JSON with NaN handling."""
    with open(filepath) as f:
        content = f.read()
        # Replace NaN and Infinity with null
        content = content.replace('NaN', 'null').replace('Infinity', 'null').replace('-Infinity', 'null')
        return json.loads(content)

app = FastAPI(
    title="ShelfGuard API",
    description="Inventory Anomaly & Shrinkage Detector",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "ShelfGuard API is running", "version": "1.0.0"}


@app.get("/api/reports")
def list_reports():
    """List all saved reports."""
    reports_path = Path(REPORTS_PATH)
    if not reports_path.exists():
        return {"reports": []}
    files = sorted(reports_path.glob("*.json"), reverse=True)
    return {"reports": [f.stem for f in files]}


@app.get("/api/reports/latest")
def get_latest_report():
    """Get the most recently generated report."""
    reports_path = Path(REPORTS_PATH)
    files = sorted(reports_path.glob("*.json"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No reports found. Run the pipeline first.")
    return safe_json_load(files[0])


@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    """Get a specific report by ID."""
    report_path = Path(f"{REPORTS_PATH}{report_id}.json")
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    return safe_json_load(report_path)


@app.get("/api/anomalies")
def get_anomalies_filtered(
    severity: str = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    anomaly_type: str = Query(None, description="Filter by type: THEFT, SPOILAGE, etc."),
    store: str = Query(None, description="Filter by store ID"),
    limit: int = Query(None, description="Max records to return (default: all)"),
):
    """Get anomalies from the latest report with optional filters."""
    reports_path = Path(REPORTS_PATH)
    files = sorted(reports_path.glob("*.json"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No reports found.")

    report = safe_json_load(files[0])

    anomalies = report.get("top_anomalies", [])

    if severity:
        anomalies = [a for a in anomalies if a.get("severity") == severity.upper()]
    if anomaly_type:
        anomalies = [a for a in anomalies if a.get("anomaly_type") == anomaly_type.upper()]
    if store:
        anomalies = [a for a in anomalies if a.get("Store ID") == store.upper()]

    return {
        "total": len(anomalies),
        "anomalies": anomalies[:limit] if limit else anomalies,
    }


@app.get("/api/summary")
def get_summary():
    """Get a high level summary from the latest report."""
    reports_path = Path(REPORTS_PATH)
    files = sorted(reports_path.glob("*.json"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No reports found.")

    report = safe_json_load(files[0])

    return {
        "report_id":                report.get("report_id"),
        "generated_at":             report.get("generated_at"),
        "dataset_summary":          report.get("dataset_summary"),
        "total_records_scanned":    report.get("total_records_scanned"),
        "total_anomalies_detected": report.get("total_anomalies_detected"),
        "severity_breakdown":       report.get("severity_breakdown"),
        "anomaly_type_breakdown":   report.get("anomaly_type_breakdown"),
    }


@app.post("/api/run")
def run_pipeline(
    sample: int = Query(5000, description="Number of records to sample"),
    ai: bool = Query(True, description="Enable AI enrichment"),
):
    """Trigger a fresh pipeline run and save the report."""
    import main as pipeline_main
    filepath = "data/raw/retail_store_inventory_data.csv"
    pipeline_main.run_pipeline(filepath, enrich_with_ai=ai, sample=sample)
    return {"status": "ok", "message": "Pipeline complete. Refresh dashboard to see results."}
