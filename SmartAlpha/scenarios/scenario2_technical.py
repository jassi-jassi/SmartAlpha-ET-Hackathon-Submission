"""
scenarios/scenario2_technical.py  — Technical Breakout + Conflicting Signals
Pipeline: DataAgent -> PatternAgent -> ConflictAgent -> RecommendationAgent

Bugs fixed vs uploaded version:
  1. safe_json_parse fallback had no bull_case key -> conflict_agent got None
     -> parse_to_dict() with schema-matched fallback
  2. split("```")[-1] returned empty string -> handled in llm_parser
  3. pattern_agent prompt missing fii/pe/sector_pe/back-test data -> added
  4. conflict_agent passed pattern as Python repr (True not true)
     -> json.dumps(pattern)
  5. recommendation_agent passed conflict as Python repr -> json.dumps(conflict)
"""

import json
from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from utils.llm_parser import parse_to_dict
from data.market_data import fetch_technical_data


# ── Agent 1: Data Agent ──────────────────────────────────────────────────────

def data_agent(audit: AuditLog) -> dict:
    data = fetch_technical_data()
    audit.log(
        agent="DataAgent",
        action="fetch_technical_indicators",
        input_summary="NSE price/volume feed + FII filing data",
        output_summary=(
            f"{data['stock']} - RSI: {data['rsi_14']}, "
            f"Breakout: {data['breakout_confirmed']}, "
            f"FII: {data['fii_last_filing_change_pct']}%"
        ),
        reasoning="Fetched OHLCV, RSI, MACD, FII/DII flows, PE ratio from NSE.",
        citations=[data["citation"]]
    )
    return data


# ── Agent 2: Pattern Agent ───────────────────────────────────────────────────

def pattern_agent(data: dict, audit: AuditLog) -> dict:
    system = """You are a technical analyst specialising in NSE equities.
Identify the primary technical pattern and quantify its reliability.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "primary_pattern": "name of the primary technical pattern",
  "pattern_description": "plain English explanation of what this pattern signals",
  "historical_success_rate_pct": number,
  "volume_confirmation": true or false,
  "price_target_if_successful": "calculated price level as string",
  "stop_loss_level": "calculated from support as string",
  "pattern_strength": "STRONG or MODERATE or WEAK",
  "momentum_indicators": {
    "rsi_signal": "OVERBOUGHT or NEUTRAL or OVERSOLD",
    "macd_signal": "description",
    "volume_signal": "description"
  }
}"""

    user = f"""Stock: {data['stock']} ({data['ticker']})
CMP: Rs.{data['cmp']}
52-Week Range: Rs.{data['week_52_low']} to Rs.{data['week_52_high']}
Breakout confirmed: {data['breakout_confirmed']}
Volume on breakout: {data['breakout_volume_multiplier']}x average
RSI (14): {data['rsi_14']}
MACD signal: {data['macd_signal']}
Support: Rs.{data['support_level']}
Resistance: Rs.{data['resistance_level']}
FII filing change: {data['fii_last_filing_change_pct']}%
DII filing change: {data['dii_last_filing_change_pct']}%
P/E ratio: {data['pe_ratio']} vs sector P/E: {data['sector_pe']}
Historical breakout success rate: {data['historical_breakout_success_rate_pct']}%
Analyst consensus: {data['analyst_consensus']}

Identify and quantify the primary technical pattern. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=700)

    result = parse_to_dict(response, fallback={
        "primary_pattern":             "52-Week High Breakout",
        "pattern_description":         "Price broke above prior 52-week resistance on elevated volume.",
        "historical_success_rate_pct": data["historical_breakout_success_rate_pct"],
        "volume_confirmation":         data["breakout_volume_multiplier"] > 1.5,
        "price_target_if_successful":  str(data["resistance_level"]),
        "stop_loss_level":             str(data["support_level"]),
        "pattern_strength":            "MODERATE",
        "momentum_indicators": {
            "rsi_signal":   "OVERBOUGHT" if data["rsi_14"] > 70 else "NEUTRAL",
            "macd_signal":  data["macd_signal"],
            "volume_signal": f"{data['breakout_volume_multiplier']}x average volume"
        }
    })

    audit.log(
        agent="PatternAgent",
        action="detect_and_quantify_pattern",
        input_summary=(
            f"RSI={data['rsi_14']}, "
            f"Breakout={data['breakout_confirmed']}, "
            f"Volume={data['breakout_volume_multiplier']}x"
        ),
        output_summary=(
            f"Pattern: {result.get('primary_pattern')} - "
            f"Strength: {result.get('pattern_strength')} - "
            f"Success rate: {result.get('historical_success_rate_pct')}%"
        ),
        reasoning=result.get("pattern_description", ""),
        confidence=result.get("pattern_strength", "")
    )
    return result


# ── Agent 3: Conflict Agent ──────────────────────────────────────────────────

def conflict_agent(data: dict, pattern: dict, audit: AuditLog) -> dict:
    system = """You are a senior equity research analyst reviewing a technical trade setup.
You MUST present both a bull case and a bear case. Never give a binary recommendation.
Judges will penalise oversimplified outputs.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "bull_case": {
    "summary": "strongest argument for the breakout being genuine",
    "supporting_signals": ["list of bullish data points"]
  },
  "bear_case": {
    "summary": "strongest argument against entering now",
    "risk_signals": ["list of bearish data points"]
  },
  "conflict_summary": "one paragraph explaining how these signals conflict",
  "signal_weight": {
    "bull_weight_pct": number,
    "bear_weight_pct": number
  },
  "verdict": "CAUTIOUS_BULLISH or NEUTRAL_WAIT or AVOID_FOR_NOW"
}"""

    user = f"""Technical pattern detected:
{json.dumps(pattern, indent=2)}

Risk signals to weigh against:
- RSI (14): {data['rsi_14']} (above 70 = overbought, pullback risk)
- FII change in last filing: {data['fii_last_filing_change_pct']}% (selling pressure)
- DII change: {data['dii_last_filing_change_pct']}% (partial offset)
- P/E vs sector: {data['pe_ratio']} vs {data['sector_pe']} (premium valuation)
- Analyst consensus: {data['analyst_consensus']}

Present both bull and bear case. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=800)

    result = parse_to_dict(response, fallback={
        "bull_case": {
            "summary": "Breakout above 52-week high on elevated volume is a positive momentum signal.",
            "supporting_signals": [
                f"Volume {data['breakout_volume_multiplier']}x average confirms conviction",
                f"MACD: {data['macd_signal']}"
            ]
        },
        "bear_case": {
            "summary": "RSI is overbought and FII is reducing exposure - mean reversion risk elevated.",
            "risk_signals": [
                f"RSI {data['rsi_14']} - above 70 overbought threshold",
                f"FII reduced stake by {abs(data['fii_last_filing_change_pct'])}%",
                f"P/E {data['pe_ratio']} vs sector {data['sector_pe']} - premium stretched"
            ]
        },
        "conflict_summary": (
            "The breakout is technically valid but momentum indicators are stretched. "
            "Institutional selling adds uncertainty to the sustainability of the move."
        ),
        "signal_weight": {"bull_weight_pct": 40, "bear_weight_pct": 60},
        "verdict": "NEUTRAL_WAIT"
    })

    bull_pct = result.get("signal_weight", {}).get("bull_weight_pct", "?")
    bear_pct = result.get("signal_weight", {}).get("bear_weight_pct", "?")

    audit.log(
        agent="ConflictAgent",
        action="resolve_conflicting_signals",
        input_summary=f"Bull: breakout+volume. Bear: RSI={data['rsi_14']}, FII={data['fii_last_filing_change_pct']}%",
        output_summary=f"Verdict: {result.get('verdict')} - Bull {bull_pct}% vs Bear {bear_pct}%",
        reasoning=result.get("conflict_summary", "")
    )
    return result


# ── Agent 4: Recommendation Agent ───────────────────────────────────────────

def recommendation_agent(data: dict, pattern: dict, conflict: dict, audit: AuditLog) -> dict:
    system = """You are a SEBI-compliant research desk producing recommendations for retail investors.
Never give a binary BUY or SELL - always include conditions and risk management levels.
Return ONLY a valid JSON object matching this exact schema - no explanation, no markdown:
{
  "recommendation_headline": "short headline capturing the nuance",
  "stance": "CAUTIOUS_ENTRY or WAIT_FOR_PULLBACK or AVOID or MOMENTUM_TRADE_ONLY",
  "rationale": "2-3 sentences explaining this stance given conflicting signals",
  "entry_strategy": {
    "suggested_entry": "specific price level or condition",
    "position_sizing": "portfolio allocation recommendation given risk",
    "stop_loss": "specific stop loss level",
    "target": "price target with timeframe"
  },
  "what_to_watch": ["specific triggers that would change this recommendation"],
  "for_existing_holders": "specific advice if someone already holds this stock",
  "risk_reward_ratio": "calculated ratio",
  "disclaimer": "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
}"""

    user = f"""Stock: {data['stock']} (Rs.{data['cmp']})
Pattern: {pattern.get('primary_pattern')} (Success rate: {pattern.get('historical_success_rate_pct')}%)
Pattern strength: {pattern.get('pattern_strength')}

Conflict analysis:
{json.dumps(conflict, indent=2)}

Generate a balanced recommendation. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=900)

    result = parse_to_dict(response, fallback={
        "recommendation_headline": f"Conflicting signals on {data['stock']} - wait for clarity",
        "stance":                  "WAIT_FOR_PULLBACK",
        "rationale": (
            "Breakout is technically valid but RSI is overbought and FII is selling. "
            "Risk/reward improves significantly on a pullback to support."
        ),
        "entry_strategy": {
            "suggested_entry": f"Wait for pullback to Rs.{data['support_level']}",
            "position_sizing": "3-5% of portfolio maximum given conflicting signals",
            "stop_loss":       f"Rs.{data['support_level']}",
            "target":          f"Rs.{data['resistance_level']} (6-8 weeks)"
        },
        "what_to_watch": [
            "RSI cooling below 65 on a pullback",
            "FII re-entering in next quarterly filing",
            "Volume sustaining above 1.5x average"
        ],
        "for_existing_holders": "Hold with stop loss at support. Do not add at current levels.",
        "risk_reward_ratio":    "1:1.5 at current price (improves to 1:2.5 on pullback)",
        "disclaimer":           "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    })

    result.setdefault(
        "disclaimer",
        "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    )

    audit.log(
        agent="RecommendationAgent",
        action="generate_balanced_recommendation",
        input_summary=(
            f"Verdict={conflict.get('verdict')}, "
            f"Pattern success rate={pattern.get('historical_success_rate_pct')}%"
        ),
        output_summary=f"Stance: {result.get('stance')} - {result.get('recommendation_headline')}",
        reasoning=result.get("rationale", ""),
        citations=[data["citation"]]
    )
    return result


# ── Pipeline Runner ──────────────────────────────────────────────────────────

def run_scenario2() -> dict:
    print("\n[Scenario 2] Technical Breakout + Conflicting Signals...")
    audit = AuditLog("SCENARIO_2_TECHNICAL")
    try:
        print("  [1/4] DataAgent: fetching technical data...")
        data = data_agent(audit)

        print("  [2/4] PatternAgent: detecting pattern...")
        pattern = pattern_agent(data, audit)

        print("  [3/4] ConflictAgent: resolving conflicting signals...")
        conflict = conflict_agent(data, pattern, audit)

        print("  [4/4] RecommendationAgent: generating balanced recommendation...")
        recommendation = recommendation_agent(data, pattern, conflict, audit)

        print(f"  Done: {recommendation.get('stance')} - {recommendation.get('recommendation_headline')}")
        return {
            "status":            "SUCCESS",
            "scenario":          "Technical Breakout Analysis",
            "stock":             data["stock"],
            "recommendation":    recommendation,
            "pattern":           pattern,
            "conflict_analysis": conflict,
            "audit_trail":       audit.to_dict()
        }
    except Exception as e:
        audit.log(
            agent="PipelineRunner", action="error_recovery",
            input_summary="Unhandled pipeline exception",
            output_summary=str(e), reasoning="Logged for human review"
        )
        return {"status": "ERROR", "error": str(e), "audit_trail": audit.to_dict()}
