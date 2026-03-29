# 🚀 SmartAlpha AI — ET Hackathon 2026

### Track 6: AI for the Indian Investor

---

## 🧠 What This Is

**SmartAlpha** is a **multi-agent AI system** that converts raw market data into **actionable, portfolio-aware investment intelligence** for Indian retail investors.

It solves a key problem:

> Retail investors react to noise. SmartAlpha turns data into signals.

---

## ⚡ What Makes It Different

✅ Multi-agent reasoning (not a chatbot)
✅ Portfolio-aware decisions (₹ impact, not generic advice)
✅ Full audit trail (every decision is traceable)
✅ Fault-tolerant (never crashes on bad AI output)
✅ Real-time extensible (NSE / broker APIs ready)

---

## 🎯 Scenario Coverage

### 🔍 Scenario 1 — Bulk Deal Intelligence

* Detects promoter stake sales
* Classifies **Distress vs Routine selling**
* Generates **SEBI-compliant investor alerts**

---

### 📈 Scenario 2 — Technical Pattern Intelligence

* Detects breakout patterns
* Identifies **conflicting signals (RSI, FII flows)**
* Generates **balanced, non-naive recommendations**

---

### 📊 Scenario 3 — Portfolio-Aware Intelligence (CORE FEATURE)

* Handles multiple simultaneous events
* Calculates **exact ₹ impact on user portfolio**
* Ranks events by **financial materiality**
* Generates **personalized alerts**

---

## 🏗️ Architecture (Multi-Agent Pipeline)

```
Market Data / Portfolio Input
        │
        ▼
Data Agent        → Fetch + validate structured data
        │
        ▼
Signal / Pattern Agent → Detect signals / patterns
        │
        ▼
Context Agent     → Resolve conflicts / enrich reasoning
        │
        ▼
Alert Agent       → Generate actionable insight
        │
        ▼
Audit Log         → Immutable decision trace
```

---

## 🤖 Tech Stack

| Component     | Technology                             |
| ------------- | -------------------------------------- |
| LLM           | AWS Bedrock (Meta Llama 3)             |
| Orchestration | Custom Python agent pipeline           |
| Data          | Simulated NSE-style (API-ready)        |
| Logging       | Custom audit system (`utils/audit.py`) |
| Runtime       | Python / Google Colab                  |

---

## ⚙️ How to Run

### 🔹 Google Colab

```python
# Set AWS credentials
import os
os.environ["AWS_ACCESS_KEY_ID"] = "YOUR_KEY"
os.environ["AWS_SECRET_ACCESS_KEY"] = "YOUR_SECRET"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Run system
from main import SmartAlpha

agent = SmartAlpha()
result = agent.run_all()
```

---

### 🔹 Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/smartalpha
cd smartalpha

pip install -r requirements.txt

python main.py
```

---

## 📂 Project Structure

```
smartalpha/
├── main.py
├── scenarios/
│   ├── scenario1_bulk_deal.py
│   ├── scenario2_technical.py
│   └── scenario3_portfolio.py
├── utils/
│   ├── audit.py
│   └── llm.py
├── data/
│   └── market_data.py
├── outputs/              # Generated results
├── SmartAlpha_Colab.ipynb
├── requirements.txt
└── README.md
```

---

## 📊 Output Example

```json
{
  "status": "SUCCESS",
  "alert": {
    "headline": "RBI rate cut impacts your banking holdings",
    "impact_rupees": 3200,
    "affected_stocks": ["HDFC Bank", "ICICI Bank"]
  },
  "audit_trail": {
    "total_steps": 4
  }
}
```

---

## 🧪 Key Features (Judge Criteria Alignment)

| Criteria               | Implementation                     |
| ---------------------- | ---------------------------------- |
| Multi-agent system     | 4 agents per scenario              |
| Autonomy               | No human input required            |
| Error handling         | Safe JSON parsing + fallback logic |
| Enterprise readiness   | Audit logs + structured outputs    |
| Financial intelligence | ₹ impact-based prioritisation      |

---

## 🔐 Reliability & Robustness

SmartAlpha includes:

* Safe parsing for malformed LLM outputs
* Nested JSON recovery
* Fallback execution paths
* Zero pipeline failure guarantee

---

## ⚠️ Disclaimer

This project is built for **ET Hackathon 2026**.
It does not constitute financial advice.
Always consult a SEBI-registered advisor before investing.

---

## 🏁 Final Note

SmartAlpha demonstrates how **AI agents — not chatbots — will power the future of financial decision-making.**
