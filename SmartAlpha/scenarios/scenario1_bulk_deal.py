"""
scenarios/scenario1_bulk_deal.py

SCENARIO 1 — Bulk Deal Filing Analysis
Agent pipeline: DataAgent → SignalAgent → ContextAgent → AlertAgent

Handles the exact judge scenario:
  "A promoter of a mid-cap FMCG company has just sold 4.2% of their stake
   via a bulk deal at a 6% discount to market price..."
"""

from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from data.market_data import fetch_bulk_deal_data, fetch_earnings_history
import json


# ─────────────────────────────────────────────────────────────
# AGENT 1: Data Agent (simple → Haiku)
# Fetches and validates the raw filing data
# ─────────────────────────────────────────────────────────────

def data_agent(audit: AuditLog) -> dict:
    raw = fetch_bulk_deal_data()

    # Validate required fields
    required = ["company", "stake_sold_pct", "discount_pct", "promoter_name"]
    missing = [f for f in required if f not in raw]
    if missing:
        raise ValueError(f"Filing data missing fields: {missing}")

    earnings = fetch_earnings_history(raw["ticker"])
    raw["earnings_context"] = earnings

    audit.log(
        agent="DataAgent",
        action="fetch_and_validate_filing",
        input_summary="NSE bulk deal filing endpoint",
        output_summary=f"{raw['company']} — {raw['stake_sold_pct']}% stake sold at {raw['discount_pct']}% discount",
        reasoning="Fetched bulk deal filing and earnings history. Validated required fields.",
        citations=[raw.get("citation", "")]
    )
    return raw


# ─────────────────────────────────────────────────────────────
# AGENT 2: Signal Classification Agent (complex → Sonnet)
# Classifies: distress selling vs routine block deal
# ─────────────────────────────────────────────────────────────

def signal_agent(data: dict, audit: AuditLog) -> dict:
    system = """You are a SEBI-registered research analyst specialising in bulk deal analysis.
Your job: classify whether a promoter bulk deal is DISTRESS SELLING or ROUTINE BLOCK.

Rules:
- Distress signals: large stake (>3%), deep discount (>5%), declining earnings, negative sentiment, no prior deals
- Routine signals: small stake, near market price, strong earnings, positive commentary, pattern of historical deals
- Always cite the specific data points driving your classification
- Output ONLY valid JSON, no markdown, no explanation outside the JSON"""

    user = f"""Analyse this bulk deal filing and classify it:

Filing Data:
{json.dumps(data, indent=2, default=str)}

Return this exact JSON structure:
{{
  "classification": "DISTRESS_SELLING" or "ROUTINE_BLOCK",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "distress_signals": ["list of specific distress indicators found"],
  "routine_signals": ["list of routine indicators found"],
  "key_concern": "single most important concern in one sentence",
  "data_points_used": ["exact figures from the filing that drove this classification"]
}}"""

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    # Clean JSON from response
    if "```" in response:
        response = response.split("```json")[-1].split("```")[0].strip()

    result = json.loads(response)

    audit.log(
        agent="SignalAgent",
        action="classify_bulk_deal",
        input_summary=f"Stake: {data['stake_sold_pct']}%, Discount: {data['discount_pct']}%, Earnings trend: {data['earnings_context']['trend']}",
        output_summary=f"Classification: {result['classification']} (Confidence: {result['confidence']})",
        reasoning=f"Key concern: {result['key_concern']}",
        confidence=result["confidence"],
        citations=data.get("citation", "").split(",")
    )
    return result


# ─────────────────────────────────────────────────────────────
# AGENT 3: Context Enrichment Agent (complex → Sonnet)
# Cross-references earnings trajectory + management tone
# ─────────────────────────────────────────────────────────────

def context_agent(data: dict, signal: dict, audit: AuditLog) -> dict:
    system = """You are a fundamental equity analyst. Your job is to enrich a bulk deal signal
with earnings trajectory context and produce a risk severity assessment.
Output ONLY valid JSON."""

    user = f"""Given this bulk deal classification and company fundamentals, assess risk severity:

Signal Classification: {json.dumps(signal, indent=2)}

Earnings History: {json.dumps(data['earnings_context'], indent=2)}

Additional Context:
- Promoter holding before: {data['promoter_holding_before_pct']}%
- Promoter holding after: {data['promoter_holding_after_pct']}%
- FII holding change: {data['fii_holding_change_pct']}%
- Deal volume vs avg: {round(data['deal_volume']/data['avg_volume_30d'], 1)}x normal

Return this exact JSON:
{{
  "risk_severity": "CRITICAL" or "HIGH" or "MEDIUM" or "LOW",
  "earnings_trend_assessment": "one sentence on earnings trajectory",
  "institutional_flow_assessment": "one sentence on FII/promoter combined signal",
  "compounding_factors": ["factors that make this worse or better together"],
  "mitigating_factors": ["anything that reduces concern"],
  "confidence_adjustment": "UPGRADE" or "DOWNGRADE" or "MAINTAIN"
}}"""

    response = call_llm(system, user, TaskComplexity.COMPLEX)
    if "```" in response:
        response = response.split("```json")[-1].split("```")[0].strip()

    result = json.loads(response)

    audit.log(
        agent="ContextAgent",
        action="enrich_with_fundamentals",
        input_summary=f"Classification={signal['classification']}, Earnings trend={data['earnings_context']['trend']}, FII change={data['fii_holding_change_pct']}%",
        output_summary=f"Risk severity: {result['risk_severity']}. {result['earnings_trend_assessment']}",
        reasoning=result["institutional_flow_assessment"],
        confidence=result["risk_severity"]
    )
    return result


# ─────────────────────────────────────────────────────────────
# AGENT 4: Alert Generation Agent (complex → Sonnet)
# Generates the final retail investor alert with citation
# ─────────────────────────────────────────────────────────────

def alert_agent(data: dict, signal: dict, context: dict, audit: AuditLog) -> dict:
    system = """You are a SEBI-compliant investment alert system for retail investors.
Generate a clear, actionable alert from a bulk deal analysis.

IMPORTANT RULES:
- No binary BUY/SELL — always risk-adjusted recommendation
- Must cite the specific NSE filing
- Must explain what the signal means for a retail investor holding this stock
- Include a SEBI disclaimer
- Output ONLY valid JSON"""

    user = f"""Generate a retail investor alert for this bulk deal:

Company: {data['company']} (₹{data['market_price']} CMP)
Signal: {signal['classification']} — Confidence: {signal['confidence']}
Risk Severity: {context['risk_severity']}
Key Concern: {signal['key_concern']}
Distress Signals: {signal['distress_signals']}
Mitigating Factors: {context['mitigating_factors']}
Filing Citation: {data['citation']}

Return this exact JSON:
{{
  "alert_title": "short headline for the alert",
  "severity_label": "CRITICAL ALERT" or "HIGH ALERT" or "WATCH LIST",
  "plain_english_summary": "2-3 sentences explaining what happened and why it matters",
  "what_it_means_for_you": "direct explanation for a retail investor holding this stock",
  "recommended_action": "specific risk-adjusted action (not binary buy/sell)",
  "risk_factors": ["top 3 risks ranked by severity"],
  "watch_indicators": ["what to monitor next — price level, next quarter result, etc."],
  "filing_reference": "exact filing citation",
  "disclaimer": "SEBI compliance disclaimer"
}}"""

    response = call_llm(system, user, TaskComplexity.COMPLEX)
    if "```" in response:
        response = response.split("```json")[-1].split("```")[0].strip()

    result = json.loads(response)

    audit.log(
        agent="AlertAgent",
        action="generate_retail_alert",
        input_summary=f"Risk={context['risk_severity']}, Classification={signal['classification']}",
        output_summary=f"{result['severity_label']}: {result['alert_title']}",
        reasoning=result["plain_english_summary"],
        confidence=signal["confidence"],
        citations=[result["filing_reference"]]
    )
    return result


# ─────────────────────────────────────────────────────────────
# PIPELINE RUNNER
# ─────────────────────────────────────────────────────────────

def run_scenario1() -> dict:
    """
    Full 4-step autonomous pipeline for Scenario 1.
    No human input between steps — satisfies autonomy requirement.
    """
    print("\n🔍 Running Scenario 1: Bulk Deal Filing Analysis...")

    audit = AuditLog("SCENARIO_1_BULK_DEAL")

    try:
        # Step 1: Fetch & validate data
        print("  [1/4] DataAgent: Fetching filing...")
        data = data_agent(audit)

        # Step 2: Classify the signal
        print("  [2/4] SignalAgent: Classifying deal type...")
        signal = signal_agent(data, audit)

        # Step 3: Enrich with context
        print("  [3/4] ContextAgent: Enriching with fundamentals...")
        context = context_agent(data, signal, audit)

        # Step 4: Generate alert
        print("  [4/4] AlertAgent: Generating retail alert...")
        alert = alert_agent(data, signal, context, audit)

        result = {
            "status": "SUCCESS",
            "scenario": "Bulk Deal Filing Analysis",
            "company": data["company"],
            "alert": alert,
            "signal": signal,
            "context": context,
            "audit_trail": audit.to_dict()
        }

        print(f"\n  ✅ Complete — {alert['severity_label']}: {alert['alert_title']}")
        return result

    except Exception as e:
        audit.log(
            agent="PipelineRunner",
            action="error_recovery",
            input_summary="Pipeline error",
            output_summary=str(e),
            reasoning="Unrecoverable error — escalating to human review"
        )
        return {
            "status": "ERROR",
            "error": str(e),
            "audit_trail": audit.to_dict()
        }
