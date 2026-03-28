"""
data/market_data.py
Simulated market data matching the 3 official scenario packs.
In production: replace fetch_* functions with real NSE/BSE API calls.
"""

from datetime import datetime


# ─────────────────────────────────────────────
# SCENARIO 1 — Bulk Deal Filing
# ─────────────────────────────────────────────

def fetch_bulk_deal_data() -> dict:
    """
    Simulates a promoter bulk deal filing.
    Real version: scrape NSE bulk deal page or use BSE API.
    """
    return {
        "source": "NSE Bulk Deal Filing",
        "timestamp": datetime.now().isoformat(),
        "company": "ABC FMCG Ltd",
        "ticker": "ABCFMCG",
        "sector": "FMCG",
        "promoter_name": "Rajesh Kumar (Promoter)",
        "stake_sold_pct": 4.2,           # % of total shares
        "deal_price": 940.0,             # ₹ per share
        "market_price": 1000.0,          # ₹ CMP
        "discount_pct": 6.0,             # % below market
        "filing_date": "2026-03-27",
        "recent_earnings_growth_pct": -2.1,    # YoY
        "management_commentary": "neutral",    # positive/neutral/negative
        "promoter_holding_before_pct": 54.2,
        "promoter_holding_after_pct": 50.0,
        "historical_bulk_deals": [],           # no prior deals → unusual
        "avg_volume_30d": 250000,
        "deal_volume": 840000,                 # 3.4x avg volume
        "fii_holding_change_pct": -0.8,        # FIIs also reducing
        "citation": "https://www.nseindia.com/companies-listing/corporate-filings-bulk-deals"
    }


def fetch_earnings_history(ticker: str) -> dict:
    """Quarterly earnings for context enrichment."""
    return {
        "ticker": ticker,
        "quarters": [
            {"q": "Q3FY26", "revenue_growth_pct": -2.1, "pat_growth_pct": -4.5, "guidance": "cautious"},
            {"q": "Q2FY26", "revenue_growth_pct":  1.2, "pat_growth_pct":  0.8, "guidance": "stable"},
            {"q": "Q1FY26", "revenue_growth_pct":  3.4, "pat_growth_pct":  2.1, "guidance": "positive"},
        ],
        "trend": "deteriorating"
    }


# ─────────────────────────────────────────────
# SCENARIO 2 — Technical Breakout + Conflicting Signals
# ─────────────────────────────────────────────

def fetch_technical_data() -> dict:
    """
    Large-cap IT stock: 52-week high breakout + overbought RSI + FII selling.
    Real version: use yfinance or NSE historical data API.
    """
    return {
        "source": "NSE Technical Feed",
        "timestamp": datetime.now().isoformat(),
        "stock": "XYZ Tech Ltd",
        "ticker": "XYZTECH",
        "sector": "IT",
        "cmp": 3450.0,
        "week_52_high": 3448.0,          # just broke out
        "week_52_low": 2100.0,
        "breakout_confirmed": True,
        "breakout_volume_multiplier": 2.3,  # 2.3x avg volume on breakout day
        "rsi_14": 78,                    # overbought (>70)
        "macd_signal": "bullish_crossover",
        "support_level": 3200.0,
        "resistance_level": 3600.0,
        "fii_last_filing_change_pct": -1.2,    # FII reduced by 1.2%
        "dii_last_filing_change_pct": +0.4,    # DII slightly buying
        "pe_ratio": 32.4,
        "sector_pe": 28.0,
        "historical_breakout_success_rate_pct": 62,  # back-tested for this stock
        "analyst_consensus": "HOLD",
        "citation": "NSE Historical Data + Filing as of 2026-03-27"
    }


# ─────────────────────────────────────────────
# SCENARIO 3 — Portfolio-Aware News Prioritisation
# ─────────────────────────────────────────────

def fetch_user_portfolio() -> dict:
    """User's actual portfolio — 8 stocks as per scenario pack."""
    return {
        "user_id": "retail_investor_001",
        "total_invested": 500000,
        "holdings": [
            {"name": "HDFC Bank",     "ticker": "HDFCBANK",  "sector": "Banking",    "invested": 80000,  "current_value": 88000,  "qty": 50},
            {"name": "Infosys",       "ticker": "INFY",      "sector": "IT",         "invested": 60000,  "current_value": 65000,  "qty": 40},
            {"name": "Tata Motors",   "ticker": "TATAMOTORS","sector": "Auto",       "invested": 40000,  "current_value": 38000,  "qty": 100},
            {"name": "SBI",           "ticker": "SBIN",      "sector": "Banking",    "invested": 50000,  "current_value": 54000,  "qty": 200},
            {"name": "Reliance",      "ticker": "RELIANCE",  "sector": "Energy",     "invested": 70000,  "current_value": 75000,  "qty": 30},
            {"name": "Wipro",         "ticker": "WIPRO",     "sector": "IT",         "invested": 45000,  "current_value": 43000,  "qty": 150},
            {"name": "Asian Paints",  "ticker": "ASIANPAINT","sector": "Consumer",   "invested": 55000,  "current_value": 58000,  "qty": 25},
            {"name": "ITC",           "ticker": "ITC",       "sector": "FMCG",       "invested": 50000,  "current_value": 52000,  "qty": 300},
        ]
    }


def fetch_market_events() -> list:
    """Two simultaneous news events — exact scenario pack requirement."""
    return [
        {
            "event_id": "EVT001",
            "title": "RBI Repo Rate Cut by 25bps",
            "category": "Macro",
            "affected_sectors": ["Banking", "NBFC", "Real Estate"],
            "estimated_sector_impact_pct": +3.0,
            "rationale": "Rate cuts improve NIM for banks short-term, boost loan demand",
            "source": "RBI Monetary Policy Committee - March 2026",
            "citation": "https://rbi.org.in/monetary-policy-2026-03"
        },
        {
            "event_id": "EVT002",
            "title": "MeitY Issues New Data Localisation Directive for IT Firms",
            "category": "Regulatory",
            "affected_sectors": ["IT"],
            "estimated_sector_impact_pct": -2.5,
            "rationale": "Compliance costs estimated at 8-12% of operating margins for mid-large IT firms",
            "source": "MeitY Circular No. 2026/DL/47",
            "citation": "https://meity.gov.in/circular-2026-dl-47"
        }
    ]
