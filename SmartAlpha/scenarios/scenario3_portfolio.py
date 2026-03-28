"""
scenarios/scenario3_portfolio.py
"""

from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from data.market_data import fetch_user_portfolio, fetch_market_events
import json


# ✅ SAFE JSON PARSER
def safe_json_parse(response: str):
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
def data_agent(audit: AuditLog):
    portfolio = fetch_user_portfolio()
    events = fetch_market_events()

    audit.log(
        agent="DataAgent",
        action="fetch_portfolio_and_events",
        input_summary="User portfolio + market events",
        output_summary=f"{len(portfolio['holdings'])} stocks, {len(events)} events",
        reasoning="Fetched portfolio and events",
        citations=[e["citation"] for e in events]
    )
    return portfolio, events


# ─────────────────────────────────────────
# AGENT 2: Impact Agent
# ─────────────────────────────────────────
def impact_agent(portfolio, events, audit):

    system = "Calculate portfolio impact. Return JSON only."
    user = f"{portfolio}\n{events}"

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    if "```" in response:
        response = response.split("```")[-1].strip()

    results = safe_json_parse(response)

    audit.log(
        agent="ImpactAgent",
        action="calculate_impact",
        input_summary="portfolio + events",
        output_summary=str(results)[:100],
        reasoning="Impact calculated"
    )

    return results


# ─────────────────────────────────────────
# AGENT 3: Prioritisation Agent
# ─────────────────────────────────────────
def prioritisation_agent(impact_results, audit):

    ranked = sorted(
        impact_results,
        key=lambda x: abs(x.get("total_portfolio_impact_rupees", 0)),
        reverse=True
    )

    primary = ranked[0]
    secondary = ranked[1] if len(ranked) > 1 else None

    system = "Explain priority. Return JSON."
    user = f"Primary: {primary}\nSecondary: {secondary}"

    # ❌ removed max_tokens
    response = call_llm(system, user, TaskComplexity.SIMPLE)

    if "```" in response:
        response = response.split("```")[-1].strip()

    explanation = safe_json_parse(response)

    result = {
        "primary_event": primary,
        "secondary_event": secondary,
        "ranking": [r.get("event_title", "") for r in ranked],
        "priority_rationale": explanation.get("priority_rationale", ""),
    }

    audit.log(
        agent="PrioritisationAgent",
        action="rank_events",
        input_summary="impact results",
        output_summary=str(primary.get("event_title")),
        reasoning=explanation.get("priority_rationale", "")
    )

    return result


# ─────────────────────────────────────────
# AGENT 4: Alert Agent
# ─────────────────────────────────────────
def alert_agent(portfolio, prioritisation, audit):

    primary = prioritisation["primary_event"]

    system = "Generate alert. Return JSON."
    user = f"{primary}"

    response = call_llm(system, user, TaskComplexity.COMPLEX)

    if "```" in response:
        response = response.split("```")[-1].strip()

    result = safe_json_parse(response)

    audit.log(
        agent="AlertAgent",
        action="generate_alert",
        input_summary="final step",
        output_summary=str(result)[:100],
        reasoning="Alert generated"
    )

    return result


# ─────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────
def run_scenario3():
    print("\n📊 Running Scenario 3: Portfolio-Aware News Prioritisation...")

    audit = AuditLog("SCENARIO_3_PORTFOLIO")

    try:
        portfolio, events = data_agent(audit)
        impact = impact_agent(portfolio, events, audit)
        priority = prioritisation_agent(impact, audit)
        alert = alert_agent(portfolio, priority, audit)

        return {
            "status": "SUCCESS",
            "alert": alert,
            "impact": impact,
            "priority": priority,
            "audit_trail": audit.to_dict()
        }

    except Exception as e:
        audit.log(
            agent="PipelineRunner",
            action="error",
            input_summary="pipeline",
            output_summary=str(e),
            reasoning="Recovered"
        )
        return {
            "status": "ERROR",
            "error": str(e),
            "audit_trail": audit.to_dict()
        }
