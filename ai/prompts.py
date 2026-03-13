"""
prompts.py
----------
All prompt templates used by ShelfGuard's AI enrichment layer.
Keeping prompts in one place makes them easy to tune and version.
"""


SYSTEM_PROMPT = """
You are ShelfGuard, an expert retail loss prevention and inventory analyst.
Your job is to analyze flagged inventory anomalies and generate clear,
actionable investigation summaries for store managers.

Your summaries must be:
- Written in plain English (no jargon)
- Concise but specific (3-5 sentences max)
- Actionable — always end with a concrete next step
- Professional in tone

Always respond in valid JSON only. No extra text, no markdown, no explanation.
""".strip()


def build_enrichment_prompt(record: dict) -> str:
    """
    Build a prompt for a single anomaly record.
    Extracts the most relevant fields for the LLM to reason about.
    """
    return f"""
Analyze this flagged inventory record and return a JSON object.

RECORD:
- Store: {record.get('Store ID')}
- Region: {record.get('Region')}
- Product: {record.get('Product ID')} ({record.get('Category')})
- Date: {record.get('Date')}
- Inventory Level: {record.get('Inventory Level')} units
- Units Sold: {record.get('Units Sold')}
- Demand Forecast: {record.get('Demand Forecast')}
- Sales Discrepancy: {record.get('sales_discrepancy_pct', 0):.1f}% vs forecast
- Unit Price: ${record.get('Price', 0):.2f}
- Competitor Price: ${record.get('Competitor Pricing', 0):.2f}
- Promotion Active: {record.get('is_on_promotion')}
- Discount Applied: {record.get('Discount')}%
- Weather: {record.get('Weather Condition')}
- Season: {record.get('Seasonality')}
- Anomaly Type: {record.get('anomaly_type')}
- Severity: {record.get('severity')}
- Flags Triggered: {', '.join(record.get('anomaly_flags', []))}
- Rule-Based Rationale: {record.get('rationale')}

Return ONLY this JSON structure:
{{
  "investigation_summary": "2-3 sentence plain English explanation of what is happening and why it is concerning",
  "likely_cause": "single most probable cause in one sentence",
  "recommended_action": "one specific actionable next step for the store manager",
  "urgency": "IMMEDIATE | WITHIN_24_HOURS | THIS_WEEK | MONITOR",
  "confidence": "HIGH | MEDIUM | LOW"
}}
""".strip()
