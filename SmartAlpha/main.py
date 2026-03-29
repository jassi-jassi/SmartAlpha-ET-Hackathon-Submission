"""
main.py — SmartAlpha AI: Unified Orchestrator

Usage:
    from main import SmartAlpha
    agent = SmartAlpha()
    result = agent.run("bulk_deal")
    result = agent.run("technical")
    result = agent.run("portfolio")

Fix vs original:
  - _validate_env was removed from __init__ but load_dotenv still referenced.
    Restored environment check with a clear message (Bedrock uses IAM roles,
    not an API key, so the check just confirms boto3 can be imported).
"""

import json
import os
from datetime import datetime

from scenarios.scenario1_bulk_deal import run_scenario1
from scenarios.scenario2_technical import run_scenario2
from scenarios.scenario3_portfolio import run_scenario3

VALID_SCENARIOS = {
    "bulk_deal": run_scenario1,
    "technical": run_scenario2,
    "portfolio": run_scenario3,
}

BANNER = """
╔══════════════════════════════════════════════════════╗
║         SmartAlpha AI - ET Hackathon 2026            ║
║         Track 6: AI for the Indian Investor          ║
╚══════════════════════════════════════════════════════╝
"""


class SmartAlpha:
    def __init__(self):
        print(BANNER)
        self._check_env()

    def _check_env(self) -> None:
        try:
            import boto3  # noqa: F401
        except ImportError:
            print("WARNING: boto3 not installed. Run: pip install boto3")
            return
        # Bedrock uses IAM roles — no explicit key needed, but region must be set
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        print(f"  AWS region : {region}")
        print(f"  Profile    : {os.environ.get('AWS_PROFILE', 'default')}\n")

    def run(self, scenario: str, save_output: bool = True) -> dict:
        if scenario not in VALID_SCENARIOS:
            return {
                "status": "ERROR",
                "error":  f"Unknown scenario '{scenario}'. Valid: {list(VALID_SCENARIOS.keys())}",
            }

        result = VALID_SCENARIOS[scenario]()

        if save_output and result.get("status") == "SUCCESS":
            self._save_output(scenario, result)

        return result

    def run_all(self) -> dict:
        results = {}
        for scenario in VALID_SCENARIOS:
            print(f"\n{'─'*55}")
            results[scenario] = self.run(scenario)
        return results

    def print_report(self, result: dict) -> None:
        if result.get("status") == "ERROR":
            print(f"\n  ERROR: {result['error']}")
            return

        scenario = result.get("scenario", "Unknown")
        print(f"\n{'='*60}")
        print(f"  SMARTALPHA REPORT - {scenario.upper()}")
        print(f"{'='*60}")

        alert = result.get("alert") or result.get("recommendation")
        if alert:
            for key, value in alert.items():
                if key == "disclaimer":
                    continue
                label = key.replace("_", " ").title()
                if isinstance(value, list):
                    print(f"\n  {label}:")
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                print(f"    {k}: {v}")
                        else:
                            print(f"    - {item}")
                elif isinstance(value, dict):
                    print(f"\n  {label}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"\n  {label}: {value}")

            disclaimer = alert.get("disclaimer", "Consult a SEBI-registered advisor.")
            print(f"\n  WARNING: {disclaimer}")

        audit = result.get("audit_trail", {})
        if audit:
            print(f"\n{'─'*60}")
            print(f"  AUDIT TRAIL ({audit.get('total_steps', 0)} autonomous steps)")
            print(f"{'─'*60}")
            for entry in audit.get("trail", []):
                print(f"\n  Step {entry['step']} [{entry['agent']}]")
                print(f"    Action : {entry['action']}")
                print(f"    Output : {entry['output_summary']}")
                cites = [c for c in entry.get("citations", []) if c]
                if cites:
                    print(f"    Source : {cites[0][:80]}")
        print()

    def _save_output(self, scenario: str, result: dict) -> None:
        os.makedirs("outputs", exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"outputs/{scenario}_{ts}.json"
        with open(path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Output saved: {path}")


if __name__ == "__main__":
    agent = SmartAlpha()
    for scenario in ["bulk_deal", "technical", "portfolio"]:
        result = agent.run(scenario)
        agent.print_report(result)
