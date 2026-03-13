"""
enricher.py
-----------

Using Groq API (LLaMA 3) to enrich each anomaly record
with a plain-English investigation summary and recommended action.
"""

import os
import json
import time
import logging
from groq import Groq
from dotenv import load_dotenv
from ai.prompts import SYSTEM_PROMPT, build_enrichment_prompt

load_dotenv()
logger = logging.getLogger(__name__)

# ── Groq Client ─────────────────────────────────────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL        = "llama-3.1-8b-instant"
MAX_TOKENS   = 300
TEMPERATURE  = 0.3   # lower = more consistent, factual outputs
RETRY_LIMIT  = 3
RETRY_DELAY  = 2     # seconds between retries


# ── Single Record Enrichment ─────────────────────────────────────────────────

def enrich(record: dict) -> dict:
    """
    Send a single anomaly record to Groq and add AI-generated fields.
    Retries up to RETRY_LIMIT times on failure.
    """
    prompt = build_enrichment_prompt(record)

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown code fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            ai_output = json.loads(raw)

            # Merge AI fields into the record
            record["ai_investigation_summary"] = ai_output.get("investigation_summary", "")
            record["ai_likely_cause"]          = ai_output.get("likely_cause", "")
            record["ai_recommended_action"]    = ai_output.get("recommended_action", "")
            record["ai_urgency"]               = ai_output.get("urgency", "MONITOR")
            record["ai_confidence"]            = ai_output.get("confidence", "LOW")
            record["ai_enriched"]              = True

            return record

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt}: JSON parse error — {e}")
        except Exception as e:
            logger.warning(f"Attempt {attempt}: API error — {e}")

        if attempt < RETRY_LIMIT:
            time.sleep(RETRY_DELAY)

    # If all retries fail, mark record as unenriched
    logger.error(f"Enrichment failed after {RETRY_LIMIT} attempts for record: {record.get('Product ID')}")
    record["ai_enriched"] = False
    return record


# ── Batch Enrichment ─────────────────────────────────────────────────────────

def enrich_all(records: list[dict], delay: float = 0.5) -> list[dict]:
    """
    Enrich a list of anomaly records with AI summaries.
    Selectively enriches top anomalies by severity to conserve API calls.
    """
    from config import AI_ENRICH_TOP_N
    
    enriched = []
    total = len(records)

    logger.info(f"Starting selective AI enrichment for {total} records...")

    # Group records by severity
    severity_groups = {}
    for record in records:
        severity = record.get('severity', 'LOW')
        if severity not in severity_groups:
            severity_groups[severity] = []
        severity_groups[severity].append(record)

    # Select top records for enrichment
    records_to_enrich = []
    for severity, count in AI_ENRICH_TOP_N.items():
        if severity in severity_groups and count > 0:
            # Sort by severity_score (highest first) and take top N
            sorted_records = sorted(severity_groups[severity], 
                                 key=lambda x: x.get('severity_score', 0), 
                                 reverse=True)
            records_to_enrich.extend(sorted_records[:count])
            logger.info(f"Selected top {count} {severity} severity records for enrichment")

    # Create a set of records to enrich for quick lookup
    enrich_set = {(r.get('Store ID'), r.get('Product ID')) for r in records_to_enrich}

    # Process all records, but only enrich the selected ones
    for i, record in enumerate(records, 1):
        record_key = (record.get('Store ID'), record.get('Product ID'))
        
        if record_key in enrich_set:
            logger.info(f"Enriching record {i}/{total} — {record.get('Product ID')} @ {record.get('Store ID')}")
            enriched_record = enrich(record)
            # Add delay only for enriched records
            if i < total and any(record_key == (er.get('Store ID'), er.get('Product ID')) for er in records_to_enrich):
                time.sleep(delay)
        else:
            # Mark as not enriched
            record["ai_enriched"] = False
            enriched_record = record

        enriched.append(enriched_record)

    success = sum(1 for r in enriched if r.get("ai_enriched"))
    logger.info(f"AI enrichment complete — {success}/{total} records enriched successfully.")
    return enriched
