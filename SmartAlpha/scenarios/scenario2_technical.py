"""
scenarios/scenario2_technical.py

SCENARIO 2 — Technical Breakout with Conflicting Signals
"""

from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from data.market_data import fetch_technical_data
import json


# ✅ SAFE JSON PARSER (CRITICAL FIX)
def safe_json_parse(response: str) -> dict:
    try:
        return json.loads(response)
    except:
        return {
            "fallback": True,
            "raw_output": str(response)[:300]
        }


# ─────────────────────────────────────────
# AGENT 1: Data Agent
# ─────────────────────────────────────────
def data_agent(audit: AuditLog) -> dict:
    data = fetch_technical_data()

    audit.log(
        agent="DataAgent",
        action="fetch_technical_indicators",
        input_summary="NSE price/volume feed + FII filing data",
        output_summary=f"{data['stock']} — RSI: {data['rsi_14']}, Breakout: {data['breakout_confirmed']}, FII: {data['fii_last_filing_change_pct']}%",
        reasoning="Fetched OHLCV data, RSI, MACD, FII/DII flows from NSE.",
        citations=[data["citation"]]
    )
    return data


# ─────────────────────────────────────────
# AGENT 2: Pattern Agent
# ─────────────────────────────────────────
def pattern_agent(data: dict, audit: AuditLog) -> dict:

    system = """You are a technical analyst specialising in NSE equities.
Identify the primary pattern and quantify reliability.
Output ONLY valid JSON."""

    user = f"""Analyse:

Stock: {data['stock']}
RSI: {data['rsi_14']}
Breakout: {data['breakout_confirmed']}
Volume: {data['breakout_volume_multiplier']}x

Return JSON."""

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    if "```" in response:
        response = response.split("```")[-1].strip()

    result = safe_json_parse(response)

    audit.log(
        agent="PatternAgent",
        action="detect_pattern",
        input_summary=f"RSI={data['rsi_14']}, Breakout={data['breakout_confirmed']}",
        output_summary=str(result)[:100],
        reasoning="Pattern detection complete"
    )

    return result


# ─────────────────────────────────────────
# AGENT 3: Conflict Agent
# ─────────────────────────────────────────
def conflict_agent(data: dict, pattern: dict, audit: AuditLog) -> dict:

    system = """You are a senior analyst. Present both bull and bear case.
Output JSON only."""

    user = f"""Pattern: {pattern}
RSI: {data['rsi_14']}
FII: {data['fii_last_filing_change_pct']}

Return JSON."""

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    if "```" in response:
        response = response.split("```")[-1].strip()

    result = safe_json_parse(response)

    audit.log(
        agent="ConflictAgent",
        action="resolve_conflict",
        input_summary="Bull vs Bear signals",
        output_summary=str(result)[:100],
        reasoning="Conflict evaluated"
    )

    return result


# ─────────────────────────────────────────
# AGENT 4: Recommendation Agent
# ─────────────────────────────────────────
def recommendation_agent(data: dict, pattern: dict, conflict: dict, audit: AuditLog) -> dict:

    system = """Generate a balanced recommendation. No BUY/SELL only.
Return JSON."""

    user = f"""Stock: {data['stock']}
Pattern: {pattern}
Conflict: {conflict}

Return JSON."""

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    if "```" in response:
        response = response.split("```")[-1].strip()

    result = safe_json_parse(response)

    audit.log(
        agent="RecommendationAgent",
        action="generate_recommendation",
        input_summary="Final decision",
        output_summary=str(result)[:100],
        reasoning="Recommendation generated"
    )

    return result


# ─────────────────────────────────────────
# PIPELINE RUNNER
# ─────────────────────────────────────────
def run_scenario2() -> dict:
    print("\n📈 Running Scenario 2: Technical Breakout + Conflicting Signals...")

    audit = AuditLog("SCENARIO_2_TECHNICAL")

    try:
        print("  [1/4] DataAgent...")
        data = data_agent(audit)

        print("  [2/4] PatternAgent...")
        pattern = pattern_agent(data, audit)

        print("  [3/4] ConflictAgent...")
        conflict = conflict_agent(data, pattern, audit)

        print("  [4/4] RecommendationAgent...")
        recommendation = recommendation_agent(data, pattern, conflict, audit)

        return {
            "status": "SUCCESS",
            "scenario": "Technical Analysis",
            "stock": data["stock"],
            "recommendation": recommendation,
            "pattern": pattern,
            "conflict_analysis": conflict,
            "audit_trail": audit.to_dict()
        }

    except Exception as e:
        audit.log(
            agent="PipelineRunner",
            action="error",
            input_summary="Pipeline error",
            output_summary=str(e),
            reasoning="Recovered safely"
        )

        return {
            "status": "ERROR",
            "error": str(e),
            "audit_trail": audit.to_dict()
        }
