"""
data/market_data.py
Simulated market data matching the 3 official scenario packs.
In production: replace fetch_* functions with real NSE/BSE API calls.

Fix vs original:
  - fetch_market_events() used key "title" but scenario3_portfolio.py and
    llm_parser.py both expect "event_title". Standardised to "event_title"
    everywhere so downstream .get("event_title") never returns None.
"""

from datetime import datetime


# ─────────────────────────────────────────────────────────────
# SCENARIO 1 — Bulk Deal Filing
# ─────────────────────────────────────────────────────────────

def fetch_bulk_deal_data() -> dict:
    return {
        "source":                    "NSE Bulk Deal Filing",
        "timestamp":                 datetime.now().isoformat(),
        "company":                   "ABC FMCG Ltd",
        "ticker":                    "ABCFMCG",
        "sector":                    "FMCG",
        "promoter_name":             "Rajesh Kumar (Promoter)",
        "stake_sold_pct":            4.2,
        "deal_price":                940.0,
        "market_price":              1000.0,
        "discount_pct":              6.0,
        "filing_date":               "2026-03-27",
        "recent_earnings_growth_pct": -2.1,
        "management_commentary":     "neutral",
        "promoter_holding_before_pct": 54.2,
        "promoter_holding_after_pct":  50.0,
        "historical_bulk_deals":     [],
        "avg_volume_30d":            250000,
        "deal_volume":               840000,
        "fii_holding_change_pct":    -0.8,
        "citation": "https://www.nseindia.com/companies-listing/corporate-filings-bulk-deals",
    }


def fetch_earnings_history(ticker: str) -> dict:
    return {
        "ticker": ticker,
        "quarters": [
            {"q": "Q3FY26", "revenue_growth_pct": -2.1, "pat_growth_pct": -4.5, "guidance": "cautious"},
            {"q": "Q2FY26", "revenue_growth_pct":  1.2, "pat_growth_pct":  0.8, "guidance": "stable"},
            {"q": "Q1FY26", "revenue_growth_pct":  3.4, "pat_growth_pct":  2.1, "guidance": "positive"},
        ],
        "trend": "deteriorating",
    }


# ─────────────────────────────────────────────────────────────
# SCENARIO 2 — Technical Breakout + Conflicting Signals
# ─────────────────────────────────────────────────────────────

def fetch_technical_data() -> dict:
    return {
        "source":                            "NSE Technical Feed",
        "timestamp":                         datetime.now().isoformat(),
        "stock":                             "XYZ Tech Ltd",
        "ticker":                            "XYZTECH",
        "sector":                            "IT",
        "cmp":                               3450.0,
        "week_52_high":                      3448.0,
        "week_52_low":                       2100.0,
        "breakout_confirmed":                True,
        "breakout_volume_multiplier":        2.3,
        "rsi_14":                            78,
        "macd_signal":                       "bullish_crossover",
        "support_level":                     3200.0,
        "resistance_level":                  3600.0,
        "fii_last_filing_change_pct":        -1.2,
        "dii_last_filing_change_pct":        +0.4,
        "pe_ratio":                          32.4,
        "sector_pe":                         28.0,
        "historical_breakout_success_rate_pct": 62,
        "analyst_consensus":                 "HOLD",
        "citation":                          "NSE Historical Data + Filing as of 2026-03-27",
    }


# ─────────────────────────────────────────────────────────────
# SCENARIO 3 — Portfolio-Aware News Prioritisation
# ─────────────────────────────────────────────────────────────

def fetch_user_portfolio() -> dict:
    return {
        "user_id":       "retail_investor_001",
        "total_invested": 500000,
        "holdings": [
            {"name": "HDFC Bank",    "ticker": "HDFCBANK",   "sector": "Banking",  "invested": 80000, "current_value": 88000, "qty": 50},
            {"name": "Infosys",      "ticker": "INFY",       "sector": "IT",       "invested": 60000, "current_value": 65000, "qty": 40},
            {"name": "Tata Motors",  "ticker": "TATAMOTORS", "sector": "Auto",     "invested": 40000, "current_value": 38000, "qty": 100},
            {"name": "SBI",          "ticker": "SBIN",       "sector": "Banking",  "invested": 50000, "current_value": 54000, "qty": 200},
            {"name": "Reliance",     "ticker": "RELIANCE",   "sector": "Energy",   "invested": 70000, "current_value": 75000, "qty": 30},
            {"name": "Wipro",        "ticker": "WIPRO",      "sector": "IT",       "invested": 45000, "current_value": 43000, "qty": 150},
            {"name": "Asian Paints", "ticker": "ASIANPAINT", "sector": "Consumer", "invested": 55000, "current_value": 58000, "qty": 25},
            {"name": "ITC",          "ticker": "ITC",        "sector": "FMCG",     "invested": 50000, "current_value": 52000, "qty": 300},
        ],
    }


def fetch_market_events() -> list:
    """
    Two simultaneous events — exact scenario pack requirement.

    FIX: key was "title" in original; changed to "event_title" to match
    what every downstream agent and the parser expect via .get("event_title").
    """
    return [
        {
            "event_id":                  "EVT001",
            "event_title":               "RBI Repo Rate Cut by 25bps",   # was "title"
            "category":                  "Macro",
            "affected_sectors":          ["Banking", "NBFC", "Real Estate"],
            "estimated_sector_impact_pct": +3.0,
            "rationale":                 "Rate cuts improve NIM for banks, boost loan demand",
            "source":                    "RBI Monetary Policy Committee - March 2026",
            "citation":                  "https://rbi.org.in/monetary-policy-2026-03",
        },
        {
            "event_id":                  "EVT002",
            "event_title":               "MeitY Issues New Data Localisation Directive for IT Firms",
            "category":                  "Regulatory",
            "affected_sectors":          ["IT"],
            "estimated_sector_impact_pct": -2.5,
            "rationale":                 "Compliance costs 8-12% of operating margins for IT firms",
            "source":                    "MeitY Circular No. 2026/DL/47",
            "citation":                  "https://meity.gov.in/circular-2026-dl-47",
        },
    ]
