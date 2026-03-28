# SmartAlpha AI — ET Hackathon 2026

**Track 6: AI for the Indian Investor**  
Avataar.ai × Economic Times Hackathon 2026

---

## What This Is

SmartAlpha is a multi-agent AI system that gives Indian retail investors the same signal intelligence previously available only to institutional desks — in under 5 minutes, for free, inside ET Markets.

It handles all 3 official scenario packs:

| Scenario | What it does |
|----------|-------------|
| Bulk Deal | Detects promoter stake sales, classifies distress vs routine, generates a cited alert |
| Technical | Identifies breakout patterns, surfaces conflicting signals (RSI, FII), gives balanced recommendation |
| Portfolio | Ranks simultaneous news events by actual rupee impact on your specific holdings |

---

## Architecture

```
User Input / Market Event
        │
        ▼
  Data Agent          ← Fetch + validate (Haiku — fast, cheap)
        │
        ▼
  Signal Agent        ← Classify / detect pattern (Sonnet — deep reasoning)
        │
        ▼
  Context Agent       ← Enrich with fundamentals / resolve conflicts (Sonnet)
        │
        ▼
  Alert Agent         ← Generate cited, portfolio-aware alert (Sonnet)
        │
        ▼
  Audit Log           ← Immutable trail of every agent decision
```

**Model routing:** Simple data tasks → `claude-haiku` (cost-efficient). Complex reasoning → `claude-sonnet`. This delivers the judges' cost-efficiency bonus while maintaining accuracy.

---

## Quickstart — Google Colab

```python
# 1. Install
!pip install anthropic langgraph langchain-anthropic rich -q

# 2. Set API key
import os
os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-...'

# 3. Run
from main import SmartAlpha
agent = SmartAlpha()

result = agent.run('bulk_deal')    # Scenario 1
result = agent.run('technical')   # Scenario 2
result = agent.run('portfolio')   # Scenario 3

agent.print_report(result)
```

Open `SmartAlpha_Colab.ipynb` for the full annotated notebook.

---

## Quickstart — Local

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/smartalpha-ai.git
cd smartalpha-ai

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run all 3 scenario packs
python main.py
```

---

## Project Structure

```
smartalpha/
├── main.py                        # Unified orchestrator + CLI
├── requirements.txt
├── SmartAlpha_Colab.ipynb         # Colab notebook (demo-ready)
├── IMPACT_MODEL.py                # Quantified business case
│
├── agents/                        # (shared agent utilities)
├── data/
│   └── market_data.py             # Simulated scenario data
│       (swap fetch_* functions for real NSE/BSE API calls)
│
├── scenarios/
│   ├── scenario1_bulk_deal.py     # 4-agent bulk deal pipeline
│   ├── scenario2_technical.py     # 4-agent technical pipeline
│   └── scenario3_portfolio.py     # 4-agent portfolio pipeline
│
├── utils/
│   ├── audit.py                   # Immutable audit trail
│   └── llm.py                     # Anthropic API + model routing
│
└── outputs/                       # JSON results saved here
```

---

## Evaluation Criteria Coverage

| Criterion | Weight | How We Address It |
|-----------|--------|-------------------|
| Autonomy depth | 30% | 4 sequential agent steps, zero human input. Error recovery with audit trail. |
| Multi-agent design | 20% | 4 distinct agents per scenario (Data → Signal → Context → Alert) with explicit handoffs |
| Technical creativity | 20% | Smart model routing (Haiku for simple tasks, Sonnet for reasoning) = cost efficiency bonus |
| Enterprise readiness | 20% | Immutable audit trail, SEBI disclaimers, graceful error handling, JSON outputs |
| Impact quantification | 10% | See `IMPACT_MODEL.py` — specific assumptions, back-of-envelope math |

---

## Replacing Mock Data with Real APIs

The `data/market_data.py` file uses simulated data matching the exact scenario packs. To connect real data:

```python
# Bulk deal: replace fetch_bulk_deal_data() with:
import requests
r = requests.get('https://www.nseindia.com/api/bulk-deals')  # NSE bulk deal API

# Technical: replace fetch_technical_data() with:
import yfinance as yf
ticker = yf.Ticker("INFY.NS")
hist = ticker.history(period="1y")

# Portfolio: fetch from broker API (Zerodha Kite, Groww, etc.)
```

---

## Output Format

Every pipeline run returns:

```json
{
  "status": "SUCCESS",
  "scenario": "Bulk Deal Filing Analysis",
  "alert": {
    "alert_title": "...",
    "severity_label": "HIGH ALERT",
    "plain_english_summary": "...",
    "recommended_action": "...",
    "filing_reference": "NSE Bulk Deal Filing — https://nseindia.com/...",
    "disclaimer": "SEBI compliance disclaimer"
  },
  "audit_trail": {
    "total_steps": 4,
    "trail": [
      { "step": 1, "agent": "DataAgent", "action": "fetch_and_validate_filing", ... },
      { "step": 2, "agent": "SignalAgent", "action": "classify_bulk_deal", ... },
      { "step": 3, "agent": "ContextAgent", "action": "enrich_with_fundamentals", ... },
      { "step": 4, "agent": "AlertAgent", "action": "generate_retail_alert", ... }
    ]
  }
}
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent framework | LangGraph |
| LLM (reasoning) | Claude Sonnet (claude-sonnet-4-6) |
| LLM (simple tasks) | Claude Haiku (claude-haiku-4-5) |
| Data | NSE simulated (yfinance-compatible for real) |
| Audit trail | Custom immutable log (utils/audit.py) |
| Runtime | Python 3.11+ / Google Colab |

---

## Disclaimer

SmartAlpha is an AI research tool built for the ET Hackathon 2026. It does not constitute SEBI-registered financial advice. All recommendations include a mandatory SEBI compliance disclaimer. Users should consult a registered investment advisor before making investment decisions.

---

*Built for ET AI Hackathon 2026 — Track 6: AI for the Indian Investor*
