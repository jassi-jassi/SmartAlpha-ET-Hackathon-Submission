"""
main.py — SmartAlpha AI: Unified Orchestrator

Entry point for the hackathon submission.
Routes inputs to the correct agent pipeline and returns structured output.

Usage (local / Colab):
    from main import SmartAlpha
    agent = SmartAlpha()
    result = agent.run("bulk_deal")
    result = agent.run("technical")
    result = agent.run("portfolio")
"""

import json
import os
from datetime import datetime

from scenarios.scenario1_bulk_deal import run_scenario1
from scenarios.scenario2_technical import run_scenario2
from scenarios.scenario3_portfolio import run_scenario3


VALID_SCENARIOS = {
    "bulk_deal": run_scenario1,
    "technical":  run_scenario2,
    "portfolio":  run_scenario3,
}

BANNER = """
╔══════════════════════════════════════════════════════╗
║         SmartAlpha AI — ET Hackathon 2026            ║
║         Track 6: AI for the Indian Investor          ║
╚══════════════════════════════════════════════════════╝
"""


class SmartAlpha:
    """
    Unified multi-agent system for Indian retail investor intelligence.

    Architecture:
    - 3 specialised scenario pipelines (bulk deal / technical / portfolio)
    - 4 agents per pipeline (data → signal → context/conflict → alert)
    - Smart model routing: Haiku for simple steps, Sonnet for reasoning
    - Immutable audit trail on every agent decision
    - SEBI-compliant output with disclaimers
    """

    def __init__(self):
        print(BANNER)


    def run(self, scenario: str, save_output: bool = True) -> dict:
        """
        Run a complete agent pipeline for the given scenario.

        Args:
            scenario: "bulk_deal" | "technical" | "portfolio"
            save_output: if True, saves JSON result to outputs/

        Returns:
            Full result dict including alert, analysis, and audit trail
        """
        if scenario not in VALID_SCENARIOS:
            return {
                "status": "ERROR",
                "error": f"Unknown scenario '{scenario}'. Valid: {list(VALID_SCENARIOS.keys())}"
            }

        runner = VALID_SCENARIOS[scenario]
        result = runner()

        if save_output and result.get("status") == "SUCCESS":
            self._save_output(scenario, result)

        return result

    def run_all(self) -> dict:
        """Run all 3 scenario packs. Useful for full demo."""
        results = {}
        for scenario in VALID_SCENARIOS:
            print(f"\n{'─'*55}")
            results[scenario] = self.run(scenario)
        return results

    def print_report(self, result: dict) -> None:
        """Pretty-print a result for demo/presentation."""
        if result.get("status") == "ERROR":
            print(f"\n❌ Error: {result['error']}")
            return

        scenario = result.get("scenario", "Unknown")
        print(f"\n{'═'*60}")
        print(f"  SMARTALPHA REPORT — {scenario.upper()}")
        print(f"{'═'*60}")

        alert = result.get("alert") or result.get("recommendation")
        if alert:
            # Print key fields in readable format
            for key, value in alert.items():
                if key == "disclaimer":
                    continue
                if isinstance(value, list):
                    print(f"\n  {key.replace('_', ' ').title()}:")
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                print(f"    {k}: {v}")
                        else:
                            print(f"    • {item}")
                elif isinstance(value, dict):
                    print(f"\n  {key.replace('_', ' ').title()}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"\n  {key.replace('_', ' ').title()}: {value}")

        print(f"\n  ⚠️  {alert.get('disclaimer', 'Consult a SEBI-registered advisor.')}")

        # Print audit trail
        audit = result.get("audit_trail", {})
        if audit:
            print(f"\n{'─'*60}")
            print(f"  AUDIT TRAIL ({audit.get('total_steps', 0)} steps)")
            print(f"{'─'*60}")
            for entry in audit.get("trail", []):
                print(f"\n  Step {entry['step']} [{entry['agent']}]")
                print(f"    Action : {entry['action']}")
                print(f"    Output : {entry['output_summary']}")
                if entry.get("citations") and entry["citations"][0]:
                    print(f"    Source : {entry['citations'][0][:80]}")
        print()

    def _save_output(self, scenario: str, result: dict) -> None:
        os.makedirs("outputs", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"outputs/{scenario}_{ts}.json"
        with open(path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  💾 Output saved: {path}")


# ─────────────────────────────────────────────────────────────
# DIRECT RUN — python main.py
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    agent = SmartAlpha()

    # Run all 3 scenario packs
    for scenario in ["bulk_deal", "technical", "portfolio"]:
        result = agent.run(scenario)
        agent.print_report(result)
