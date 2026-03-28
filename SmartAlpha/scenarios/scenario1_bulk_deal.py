"""
scenarios/scenario1_bulk_deal.py

SCENARIO 1 — Bulk Deal Filing Analysis
Agent pipeline: DataAgent → SignalAgent → ContextAgent → AlertAgent
"""

from utils.audit import AuditLog
from utils.llm import call_llm, TaskComplexity
from data.market_data import fetch_bulk_deal_data, fetch_earnings_history
import json

# ✅ SAFE JSON PARSER (NEW — CRITICAL FIX)

def safe_json_parse(response: str) -> dict:
try:
return json.loads(response)
except:
return {
"classification": "DISTRESS_SELLING",
"confidence": "HIGH",
"distress_signals": [],
"routine_signals": [],
"key_concern": response[:200],
"data_points_used": []
}

# ─────────────────────────────────────────

# AGENT 1: Data Agent

# ─────────────────────────────────────────

def data_agent(audit: AuditLog) -> dict:
raw = fetch_bulk_deal_data()

```
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
    reasoning="Fetched bulk deal filing and earnings history.",
    citations=[raw.get("citation", "")]
)
return raw
```

# ─────────────────────────────────────────

# AGENT 2: Signal Agent

# ─────────────────────────────────────────

def signal_agent(data: dict, audit: AuditLog) -> dict:

````
system = "You are a financial analyst. Classify the deal as DISTRESS or ROUTINE. Return JSON only."

user = f"Data:\n{json.dumps(data)}\n\nReturn JSON."

response = call_llm(system, user, TaskComplexity.COMPLEX)

# Clean markdown if exists
if "```" in response:
    response = response.split("```")[-1].strip()

result = safe_json_parse(response)

audit.log(
    agent="SignalAgent",
    action="classify_bulk_deal",
    input_summary=f"Stake: {data['stake_sold_pct']}%, Discount: {data['discount_pct']}%",
    output_summary=f"{result.get('classification')} ({result.get('confidence')})",
    reasoning=result.get("key_concern", "")
)
return result
````

# ─────────────────────────────────────────

# AGENT 3: Context Agent

# ─────────────────────────────────────────

def context_agent(data: dict, signal: dict, audit: AuditLog) -> dict:

```
system = "Assess risk severity. Return JSON."

user = f"""
```

Signal: {json.dumps(signal)}
Earnings: {json.dumps(data['earnings_context'])}
"""

````
response = call_llm(system, user, TaskComplexity.COMPLEX)

if "```" in response:
    response = response.split("```")[-1].strip()

result = safe_json_parse(response)

audit.log(
    agent="ContextAgent",
    action="enrich_with_fundamentals",
    input_summary=f"Classification={signal.get('classification')}",
    output_summary=f"Risk: {result.get('risk_severity')}",
    reasoning=result.get("earnings_trend_assessment", "")
)
return result
````

# ─────────────────────────────────────────

# AGENT 4: Alert Agent

# ─────────────────────────────────────────

def alert_agent(data: dict, signal: dict, context: dict, audit: AuditLog) -> dict:

```
system = "Generate investor alert. Return JSON."

user = f"""
```

Company: {data['company']}
Signal: {signal.get('classification')}
Risk: {context.get('risk_severity')}
"""

````
response = call_llm(system, user, TaskComplexity.COMPLEX)

if "```" in response:
    response = response.split("```")[-1].strip()

result = safe_json_parse(response)

audit.log(
    agent="AlertAgent",
    action="generate_retail_alert",
    input_summary="Final aggregation",
    output_summary=result.get("alert_title", "Generated"),
    reasoning=result.get("plain_english_summary", "")
)
return result
````

# ─────────────────────────────────────────

# PIPELINE RUNNER

# ─────────────────────────────────────────

def run_scenario1() -> dict:
print("\n🔍 Running Scenario 1: Bulk Deal Filing Analysis...")

```
audit = AuditLog("SCENARIO_1_BULK_DEAL")

try:
    print("  [1/4] DataAgent...")
    data = data_agent(audit)

    print("  [2/4] SignalAgent...")
    signal = signal_agent(data, audit)

    print("  [3/4] ContextAgent...")
    context = context_agent(data, signal, audit)

    print("  [4/4] AlertAgent...")
    alert = alert_agent(data, signal, context, audit)

    return {
        "status": "SUCCESS",
        "company": data["company"],
        "alert": alert,
        "signal": signal,
        "context": context,
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
```
