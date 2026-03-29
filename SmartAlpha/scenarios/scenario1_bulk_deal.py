"""
scenarios/scenario1_bulk_deal.py  — Bulk Deal Filing Analysis
Pipeline: DataAgent -> SignalAgent -> ContextAgent -> AlertAgent

Bugs fixed vs uploaded version:
  1. safe_json_parse fallback hardcoded classification=DISTRESS_SELLING
     -> parse_to_dict() with neutral fallback
  2. split("```")[-1] returned empty string on fenced JSON
     -> handled inside llm_parser
  3. signal_agent dumped entire data dict with no schema
     -> only relevant fields + explicit JSON schema
  4. context_agent and alert_agent had no schema in prompts
     -> explicit schemas so .get() always finds the right key
  5. Missing 'scenario' key in SUCCESS return dict
     -> added
"""

import json
from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from utils.llm_parser import parse_to_dict
from data.market_data import fetch_bulk_deal_data, fetch_earnings_history


# ── Agent 1: Data Agent ──────────────────────────────────────────────────────

def data_agent(audit: AuditLog) -> dict:
    raw = fetch_bulk_deal_data()

    required = ["company", "stake_sold_pct", "discount_pct", "promoter_name"]
    missing  = [f for f in required if f not in raw]
    if missing:
        raise ValueError(f"Filing data missing required fields: {missing}")

    raw["earnings_context"] = fetch_earnings_history(raw["ticker"])

    audit.log(
        agent="DataAgent",
        action="fetch_and_validate_filing",
        input_summary="NSE bulk deal filing endpoint",
        output_summary=(
            f"{raw['company']} - {raw['stake_sold_pct']}% stake "
            f"sold at {raw['discount_pct']}% discount"
        ),
        reasoning="Fetched bulk deal filing and 3-quarter earnings history. Validated required fields.",
        citations=[raw.get("citation", "")]
    )
    return raw


# ── Agent 2: Signal Agent ────────────────────────────────────────────────────

def signal_agent(data: dict, audit: AuditLog) -> dict:
    system = """You are a SEBI-registered research analyst specialising in bulk deal analysis.
Classify whether this promoter bulk deal is DISTRESS_SELLING or ROUTINE_BLOCK.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "classification": "DISTRESS_SELLING or ROUTINE_BLOCK",
  "confidence": "HIGH or MEDIUM or LOW",
  "distress_signals": ["list of specific distress indicators found"],
  "routine_signals": ["list of routine indicators found"],
  "key_concern": "single most important concern in one sentence",
  "data_points_used": ["exact figures that drove this classification"]
}"""

    user = f"""Bulk deal filing:
Company: {data['company']}
Stake sold: {data['stake_sold_pct']}%
Deal price: Rs.{data['deal_price']} vs market Rs.{data['market_price']} (discount: {data['discount_pct']}%)
Promoter holding: {data['promoter_holding_before_pct']}% -> {data['promoter_holding_after_pct']}%
Prior bulk deals: {data['historical_bulk_deals']}
Deal volume vs 30d avg: {round(data['deal_volume'] / data['avg_volume_30d'], 1)}x
FII holding change: {data['fii_holding_change_pct']}%
Recent earnings growth: {data['recent_earnings_growth_pct']}%
Management commentary: {data['management_commentary']}
Earnings trend: {data['earnings_context']['trend']}

Classify this deal. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=600)

    result = parse_to_dict(response, fallback={
        "classification":  "ROUTINE_BLOCK",
        "confidence":      "LOW",
        "distress_signals": [],
        "routine_signals":  [],
        "key_concern":     "LLM parsing failed - defaulting to neutral classification",
        "data_points_used": []
    })

    audit.log(
        agent="SignalAgent",
        action="classify_bulk_deal",
        input_summary=(
            f"Stake: {data['stake_sold_pct']}%, "
            f"Discount: {data['discount_pct']}%, "
            f"Earnings: {data['earnings_context']['trend']}"
        ),
        output_summary=f"{result.get('classification')} (Confidence: {result.get('confidence')})",
        reasoning=result.get("key_concern", ""),
        confidence=result.get("confidence", ""),
        citations=[data.get("citation", "")]
    )
    return result


# ── Agent 3: Context Agent ───────────────────────────────────────────────────

def context_agent(data: dict, signal: dict, audit: AuditLog) -> dict:
    system = """You are a fundamental equity analyst assessing deal risk severity.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "risk_severity": "CRITICAL or HIGH or MEDIUM or LOW",
  "earnings_trend_assessment": "one sentence on earnings trajectory",
  "institutional_flow_assessment": "one sentence on FII and promoter signal combined",
  "compounding_factors": ["factors that make this worse"],
  "mitigating_factors": ["factors reducing concern"],
  "confidence_adjustment": "UPGRADE or DOWNGRADE or MAINTAIN"
}"""

    user = f"""Deal classification: {signal.get('classification')} (Confidence: {signal.get('confidence')})
Key concern: {signal.get('key_concern')}
Distress signals: {json.dumps(signal.get('distress_signals', []))}

Earnings context:
{json.dumps(data['earnings_context'], indent=2)}

Additional context:
- Promoter holding drop: {data['promoter_holding_before_pct']}% to {data['promoter_holding_after_pct']}%
- FII change: {data['fii_holding_change_pct']}%

Assess risk severity. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=600)

    result = parse_to_dict(response, fallback={
        "risk_severity":                "HIGH",
        "earnings_trend_assessment":    "Earnings context unavailable - conservative HIGH risk assigned.",
        "institutional_flow_assessment": "Institutional flow data unavailable.",
        "compounding_factors":          [],
        "mitigating_factors":           [],
        "confidence_adjustment":        "MAINTAIN"
    })

    audit.log(
        agent="ContextAgent",
        action="enrich_with_fundamentals",
        input_summary=(
            f"Classification={signal.get('classification')}, "
            f"Earnings={data['earnings_context']['trend']}, "
            f"FII={data['fii_holding_change_pct']}%"
        ),
        output_summary=(
            f"Risk severity: {result.get('risk_severity')}. "
            f"{result.get('earnings_trend_assessment', '')}"
        ),
        reasoning=result.get("institutional_flow_assessment", ""),
        confidence=result.get("risk_severity", "")
    )
    return result


# ── Agent 4: Alert Agent ─────────────────────────────────────────────────────

def alert_agent(data: dict, signal: dict, context: dict, audit: AuditLog) -> dict:
    system = """You are a SEBI-compliant investment alert system for retail investors.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "alert_title": "short headline",
  "severity_label": "CRITICAL ALERT or HIGH ALERT or WATCH",
  "plain_english_summary": "2-3 sentences explaining what happened and why it matters",
  "what_it_means_for_you": "direct explanation for a retail investor holding this stock",
  "recommended_action": "specific risk-adjusted action - never a binary BUY or SELL",
  "risk_factors": ["top 3 risks ranked by severity"],
  "watch_indicators": ["what to monitor next"],
  "filing_reference": "exact NSE filing citation",
  "disclaimer": "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
}"""

    user = f"""Company: {data['company']} (Rs.{data['market_price']} CMP)
Classification: {signal.get('classification')} - Confidence: {signal.get('confidence')}
Risk severity: {context.get('risk_severity')}
Key concern: {signal.get('key_concern')}
Distress signals: {json.dumps(signal.get('distress_signals', []))}
Mitigating factors: {json.dumps(context.get('mitigating_factors', []))}
Filing: {data.get('citation', 'NSE Bulk Deal Filings')}

Generate the investor alert. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=900)

    result = parse_to_dict(response, fallback={
        "alert_title":          f"Bulk Deal Alert: {data['company']}",
        "severity_label":       "WATCH",
        "plain_english_summary": f"Promoter sold {data['stake_sold_pct']}% stake at {data['discount_pct']}% discount.",
        "what_it_means_for_you": "Monitor the stock closely for further institutional movements.",
        "recommended_action":   "Consider reducing position size if risk tolerance is low.",
        "risk_factors":         signal.get("distress_signals", []),
        "watch_indicators":     ["Next quarterly result", "FII holding changes", "Management commentary"],
        "filing_reference":     data.get("citation", "NSE Bulk Deal Filings"),
        "disclaimer":           "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    })

    result.setdefault(
        "disclaimer",
        "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    )

    audit.log(
        agent="AlertAgent",
        action="generate_retail_alert",
        input_summary=(
            f"Risk={context.get('risk_severity')}, "
            f"Classification={signal.get('classification')}"
        ),
        output_summary=f"{result.get('severity_label')}: {result.get('alert_title')}",
        reasoning=result.get("plain_english_summary", ""),
        confidence=signal.get("confidence", ""),
        citations=[result.get("filing_reference", "")]
    )
    return result


# ── Pipeline Runner ──────────────────────────────────────────────────────────

def run_scenario1() -> dict:
    print("\n[Scenario 1] Bulk Deal Filing Analysis...")
    audit = AuditLog("SCENARIO_1_BULK_DEAL")
    try:
        print("  [1/4] DataAgent: fetching filing...")
        data = data_agent(audit)

        print("  [2/4] SignalAgent: classifying deal...")
        signal = signal_agent(data, audit)

        print("  [3/4] ContextAgent: enriching with fundamentals...")
        context = context_agent(data, signal, audit)

        print("  [4/4] AlertAgent: generating retail alert...")
        alert = alert_agent(data, signal, context, audit)

        print(f"  Done: {alert.get('severity_label')} - {alert.get('alert_title')}")
        return {
            "status":      "SUCCESS",
            "scenario":    "Bulk Deal Filing Analysis",
            "company":     data["company"],
            "alert":       alert,
            "signal":      signal,
            "context":     context,
            "audit_trail": audit.to_dict()
        }
    except Exception as e:
        audit.log(
            agent="PipelineRunner", action="error_recovery",
            input_summary="Unhandled pipeline exception",
            output_summary=str(e), reasoning="Logged for human review"
        )
        return {"status": "ERROR", "error": str(e), "audit_trail": audit.to_dict()}
