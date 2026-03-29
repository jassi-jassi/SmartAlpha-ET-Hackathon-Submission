# 🚀 SmartAlpha AI — ET Hackathon 2026

### Track 6: AI for the Indian Investor

---

## 🧠 Problem

India has 14+ crore demat accounts, yet most retail investors:

* React to tips instead of signals
* Miss critical filings and market events
* Cannot interpret technical indicators
* Make decisions without portfolio context

---

## 💡 Solution — SmartAlpha

**SmartAlpha is a multi-agent AI system that converts raw market data into actionable, portfolio-aware investment intelligence.**

> 🚀 Not a chatbot — a decision engine.

---

## ⚡ What Makes It Different

* ✅ Multi-agent reasoning (not a single LLM call)
* ✅ Portfolio-aware decisions (₹ impact, not generic advice)
* ✅ Full audit trail (every decision is traceable)
* ✅ Fault-tolerant system (handles malformed LLM output)
* ✅ Real-time extensible (NSE / broker APIs ready)

---

## 🎯 Scenario Coverage

### 🔍 Scenario 1 — Bulk Deal Intelligence

* Detects promoter stake sales
* Classifies **Distress vs Routine selling**
* Generates **SEBI-compliant alerts**

---

### 📈 Scenario 2 — Technical Pattern Intelligence

* Detects breakout patterns
* Identifies **conflicting signals (RSI, FII flows)**
* Generates **balanced trading strategy (entry, SL, target)**

---

### 📊 Scenario 3 — Portfolio-Aware Intelligence (CORE FEATURE)

* Handles multiple simultaneous events
* Calculates **exact ₹ impact on YOUR portfolio**
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
Signal Agent      → Detect signals / classify events
        │
        ▼
Context Agent     → Resolve conflicts / enrich reasoning
        │
        ▼
Alert Agent       → Generate actionable insights
        │
        ▼
Audit Log         → Immutable decision trace
```

---

## 🤖 Tech Stack

| Component     | Technology                      |
| ------------- | ------------------------------- |
| LLM           | AWS Bedrock (Meta Llama 3)      |
| Orchestration | Custom Python agent pipeline    |
| Data          | Simulated NSE-style (API-ready) |
| Logging       | Custom audit system             |
| Runtime       | Python / Google Colab           |

---

## ⚙️ How to Run

### 🔹 Google Colab

```python
import os

os.environ["AWS_ACCESS_KEY_ID"] = "YOUR_KEY"
os.environ["AWS_SECRET_ACCESS_KEY"] = "YOUR_SECRET"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

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
├── utils/
├── data/
├── outputs/              # Sample outputs included
├── SmartAlpha_Colab.ipynb
├── requirements.txt
└── README.md
```

---

## 📊 Sample Output

```json
{
  "status": "SUCCESS",
  "alert": {
    "headline": "RBI Repo Rate Cut impacts your banking holdings",
    "impact_rupees": 4260,
    "affected_stocks": ["HDFC Bank", "SBI"]
  },
  "audit_trail": {
    "total_steps": 4
  }
}
```

---

## 🧪 Judge Criteria Alignment

| Criteria               | Implementation                     |
| ---------------------- | ---------------------------------- |
| Multi-agent system     | 4 agents per scenario              |
| Autonomy               | Fully automated (no human input)   |
| Error handling         | Safe JSON parsing + fallback logic |
| Enterprise readiness   | Audit logs + structured outputs    |
| Financial intelligence | ₹ impact-based prioritisation      |

---

## 🔐 Reliability & Robustness

* Handles malformed LLM outputs
* Recovers nested JSON errors
* Guarantees zero pipeline failure
* Includes full audit trace for every decision

---

## ⚠️ Disclaimer

This project is built for ET Hackathon 2026.
It does not constitute financial advice.
Consult a SEBI-registered advisor before investing.

---

## 🏁 Final Note

SmartAlpha shows how **AI agents — not chatbots — will power the future of financial decision-making.**
