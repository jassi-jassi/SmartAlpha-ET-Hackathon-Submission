"""
scenarios/scenario3_portfolio.py  — Portfolio-Aware News Prioritisation
Pipeline: DataAgent -> ImpactAgent -> PrioritisationAgent -> AlertAgent

Bugs fixed vs uploaded version:
  1. impact_agent appended fallback dict -> abs(None) crash in prioritisation_agent
     -> parse_to_list() + safe_float() guarantee numeric sort key
  2. split("```")[-1] returned empty string -> handled in llm_parser
  3. impact_agent prompt had no schema -> Llama returned different structure each call
     -> explicit JSON schema added
  4. prioritisation_agent: explanation.get() crashed on wrong fallback keys
     -> parse_to_dict() + schema-matched fallback
  5. alert_agent user=f'{primary}' passed Python repr not JSON
     -> json.dumps(primary)
  6. alert_agent fallback dict printed raw_output during demo
     -> parse_to_dict() + clean fallback, explicit pop of internal keys
"""

import json
from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from utils.llm_parser import parse_to_list, parse_to_dict, safe_float
from data.market_data import fetch_user_portfolio, fetch_market_events


# ── Agent 1: Data Agent ──────────────────────────────────────────────────────

def data_agent(audit: AuditLog) -> tuple:
    portfolio = fetch_user_portfolio()
    events    = fetch_market_events()

    audit.log(
        agent="DataAgent",
        action="fetch_portfolio_and_events",
        input_summary="User portfolio + market events",
        output_summary=(
            f"{len(portfolio['holdings'])} stocks, "
            f"Rs.{portfolio['total_invested']:,} invested. "
            f"{len(events)} simultaneous events."
        ),
        reasoning="Fetched user portfolio holdings and live market events.",
        citations=[e["citation"] for e in events]
    )
    return portfolio, events


# ── Agent 2: Impact Agent ────────────────────────────────────────────────────

def impact_agent(portfolio: dict, events: list, audit: AuditLog) -> list:
    """Returns List[dict] - always. Never crashes downstream."""

    system = """You are a quantitative portfolio analyst.
Calculate the exact financial impact of market events on a user's stock portfolio.
Return ONLY a valid JSON array. No explanation. No markdown. No preamble.
Each element must follow this exact schema:
{
  "event_id": "string",
  "event_title": "string",
  "affected_holdings": [
    {
      "stock_name": "string",
      "current_value": number,
      "impact_pct": number,
      "impact_rupees": number,
      "direction": "GAIN or LOSS"
    }
  ],
  "total_portfolio_impact_rupees": number,
  "total_portfolio_impact_pct": number,
  "impact_direction": "POSITIVE or NEGATIVE",
  "math_shown": "impact_rupees = current_value x (impact_pct / 100)",
  "source_citation": "string"
}"""

    user = f"""Portfolio holdings:
{json.dumps(portfolio['holdings'], indent=2)}

Market events to analyse:
{json.dumps(events, indent=2)}

For each event:
1. Match affected_sectors to holdings in the portfolio by the sector field
2. Calculate: impact_rupees = current_value x (estimated_sector_impact_pct / 100)
3. Sum all impact_rupees for total_portfolio_impact_rupees

Return ONLY the JSON array. No explanation."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=1200)

    impact_results = parse_to_list(response)

    # Enforce numeric type on the sort key - prevents abs(None) crash
    for r in impact_results:
        r["total_portfolio_impact_rupees"] = safe_float(
            r.get("total_portfolio_impact_rupees", 0)
        )
        r["total_portfolio_impact_pct"] = safe_float(
            r.get("total_portfolio_impact_pct", 0)
        )
        r.setdefault("event_title",       "Unknown Event")
        r.setdefault("impact_direction",  "UNKNOWN")
        r.setdefault("affected_holdings", [])
        r.setdefault("source_citation",   "")

    # Safe fallback if LLM returned nothing useful
    if not impact_results:
        impact_results = [
            {
                "event_id":    e.get("event_id", f"EVT_{i+1:03d}"),
                "event_title": e.get("title", f"Event {i+1}"),
                "affected_holdings":              [],
                "total_portfolio_impact_rupees":  0.0,
                "total_portfolio_impact_pct":     0.0,
                "impact_direction":               "UNKNOWN",
                "math_shown":                     "LLM did not return structured data",
                "source_citation":                e.get("citation", "")
            }
            for i, e in enumerate(events)
        ]

    audit.log(
        agent="ImpactAgent",
        action="calculate_portfolio_impact",
        input_summary=f"{len(portfolio['holdings'])} holdings x {len(events)} events",
        output_summary=", ".join([
            f"{r['event_title'][:25]}: Rs.{r['total_portfolio_impact_rupees']:,.0f}"
            for r in impact_results
        ]),
        reasoning="impact_rupees = current_value x (sector_impact_pct / 100) per holding",
        confidence="HIGH" if all(
            r["total_portfolio_impact_rupees"] != 0 for r in impact_results
        ) else "LOW"
    )
    return impact_results


# ── Agent 3: Prioritisation Agent ────────────────────────────────────────────

def prioritisation_agent(impact_results: list, audit: AuditLog) -> dict:
    if not impact_results:
        raise ValueError("ImpactAgent returned empty results - cannot prioritise.")

    ranked    = sorted(
        impact_results,
        key=lambda x: abs(x.get("total_portfolio_impact_rupees", 0)),
        reverse=True
    )
    primary   = ranked[0]
    secondary = ranked[1] if len(ranked) > 1 else None

    system = """You explain investment prioritisation decisions concisely.
Return ONLY a valid JSON object - no markdown, no text outside the JSON:
{
  "priority_rationale": "2 sentences explaining why the primary event ranks higher for this specific portfolio",
  "impact_multiplier": "how much bigger primary impact is vs secondary, e.g. 2.1x",
  "portfolio_concentration_factor": "which holdings drive the primary event's impact"
}"""

    secondary_line = (
        f"Event: {secondary.get('event_title')}, "
        f"Impact: Rs.{secondary.get('total_portfolio_impact_rupees', 0):,.0f}"
        if secondary else "None"
    )

    user = f"""Primary event (higher portfolio impact):
Event: {primary.get('event_title')}
Direction: {primary.get('impact_direction')}
Impact: Rs.{primary.get('total_portfolio_impact_rupees', 0):,.0f}
Affected stocks: {[h.get('stock_name') for h in primary.get('affected_holdings', [])]}

Secondary event (lower impact):
{secondary_line}

Explain why the primary event is more financially material for this specific investor. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.SIMPLE, max_tokens=400)

    explanation = parse_to_dict(response, fallback={
        "priority_rationale": (
            f"{primary.get('event_title')} has the highest absolute rupee impact "
            f"on this portfolio at Rs.{primary.get('total_portfolio_impact_rupees', 0):,.0f}."
        ),
        "impact_multiplier":              "N/A",
        "portfolio_concentration_factor": "See affected holdings list."
    })

    result = {
        "primary_event":                  primary,
        "secondary_event":                secondary,
        "ranking":                        [r.get("event_title", "Unknown") for r in ranked],
        "priority_rationale":             explanation.get("priority_rationale", ""),
        "impact_multiplier":              explanation.get("impact_multiplier", ""),
        "portfolio_concentration_factor": explanation.get("portfolio_concentration_factor", "")
    }

    audit.log(
        agent="PrioritisationAgent",
        action="rank_events_by_portfolio_materiality",
        input_summary=f"{len(impact_results)} events ranked by absolute rupee impact",
        output_summary=(
            f"Priority: {primary.get('event_title')} "
            f"(Rs.{primary.get('total_portfolio_impact_rupees', 0):,.0f})"
        ),
        reasoning=explanation.get("priority_rationale", ""),
        confidence="HIGH"
    )
    return result


# ── Agent 4: Alert Agent ─────────────────────────────────────────────────────

def alert_agent(portfolio: dict, prioritisation: dict, audit: AuditLog) -> dict:
    primary        = prioritisation["primary_event"]
    total_invested = portfolio.get("total_invested", 1)
    impact_rupees  = primary.get("total_portfolio_impact_rupees", 0.0)
    impact_pct     = round(abs(impact_rupees) / total_invested * 100, 2)

    system = """You are a SEBI-compliant investment alert system for retail investors.
Generate a personalised portfolio alert.
Return ONLY a valid JSON object - no markdown, no text outside the JSON:
{
  "alert_headline": "personalised headline mentioning the investor's actual stock names",
  "severity_label": "CRITICAL ALERT or HIGH ALERT or WATCH",
  "why_this_matters_to_you": "specific explanation referencing their actual stocks by name",
  "estimated_impact": {
    "rupee_change": number,
    "direction": "POSITIVE or NEGATIVE",
    "as_pct_of_portfolio": number
  },
  "stock_level_actions": [
    {"stock": "name", "action": "specific action", "reason": "why"}
  ],
  "next_steps": ["3 specific actions for the investor in the next 24 hours"],
  "disclaimer": "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
}"""

    user = f"""Event: {primary.get('event_title')}
Direction: {primary.get('impact_direction')}
Estimated portfolio impact: Rs.{impact_rupees:,.0f} ({impact_pct}% of total portfolio)

Affected holdings:
{json.dumps(primary.get('affected_holdings', []), indent=2)}

Priority rationale: {prioritisation.get('priority_rationale', '')}

Generate a personalised alert for this investor. Return JSON only."""

    response = call_llm(system, user, TaskComplexity.COMPLEX, max_tokens=900)

    alert = parse_to_dict(response, fallback={
        "alert_headline":        f"Alert: {primary.get('event_title')} affects your portfolio",
        "severity_label":        "WATCH",
        "why_this_matters_to_you": (
            f"{primary.get('event_title')} directly affects sectors you hold. "
            f"Estimated impact: Rs.{impact_rupees:,.0f}."
        ),
        "estimated_impact": {
            "rupee_change":        impact_rupees,
            "direction":           primary.get("impact_direction", "UNKNOWN"),
            "as_pct_of_portfolio": impact_pct
        },
        "stock_level_actions": [
            {
                "stock":  h.get("stock_name", ""),
                "action": "Monitor closely",
                "reason": f"Estimated impact: Rs.{safe_float(h.get('impact_rupees', 0)):,.0f}"
            }
            for h in primary.get("affected_holdings", [])
        ],
        "next_steps": [
            "Review your affected holdings in your broker app.",
            "Check the latest filing or circular linked in the source.",
            "Consult your registered investment advisor before taking action."
        ],
        "disclaimer": "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    })

    # Enforce disclaimer regardless of LLM output
    alert.setdefault(
        "disclaimer",
        "This is AI-generated analysis. Consult a SEBI-registered investment advisor before making any decisions."
    )
    # Remove internal keys that would print raw during demo
    alert.pop("fallback",   None)
    alert.pop("raw_output", None)

    audit.log(
        agent="AlertAgent",
        action="generate_personalised_alert",
        input_summary=f"Primary: {primary.get('event_title')}, Impact: Rs.{impact_rupees:,.0f}",
        output_summary=alert.get("alert_headline", ""),
        reasoning=alert.get("why_this_matters_to_you", ""),
        confidence="HIGH",
        citations=[primary.get("source_citation", "")]
    )
    return alert


# ── Pipeline Runner ──────────────────────────────────────────────────────────

def run_scenario3() -> dict:
    print("\n[Scenario 3] Portfolio-Aware News Prioritisation...")
    audit = AuditLog("SCENARIO_3_PORTFOLIO")
    try:
        print("  [1/4] DataAgent: fetching portfolio + events...")
        portfolio, events = data_agent(audit)

        print("  [2/4] ImpactAgent: calculating rupee impact per holding...")
        impact = impact_agent(portfolio, events, audit)

        print("  [3/4] PrioritisationAgent: ranking by portfolio materiality...")
        priority = prioritisation_agent(impact, audit)

        print("  [4/4] AlertAgent: generating personalised alert...")
        alert = alert_agent(portfolio, priority, audit)

        print(f"  Done: {alert.get('alert_headline', '')}")
        return {
            "status":      "SUCCESS",
            "scenario":    "Portfolio-Aware News Prioritisation",
            "alert":       alert,
            "impact":      impact,
            "priority":    priority,
            "audit_trail": audit.to_dict()
        }
    except Exception as e:
        audit.log(
            agent="PipelineRunner", action="error_recovery",
            input_summary="Unhandled pipeline exception",
            output_summary=str(e), reasoning="Logged for human review"
        )
        return {"status": "ERROR", "error": str(e), "audit_trail": audit.to_dict()}
