"""
utils/llm_parser.py

Single source of truth for all LLM output parsing across the project.
Handles every malformed shape Bedrock/Llama can return:
  - raw string
  - JSON string of a list or dict
  - markdown-fenced: ```json ... ```
  - double-encoded JSON (string inside a string)
  - fallback dict: {"fallback": True, "raw_output": "..."}
  - list containing strings instead of dicts
  - Python repr: True/False/None instead of true/false/null

Public API
----------
parse_to_list(raw)              -> list[dict]
parse_to_dict(raw, fallback={}) -> dict
safe_float(value, default=0.0)  -> float
"""

import json
import re
from typing import Any


# ── internal helpers ─────────────────────────────────────────────────────────

def _clean_string(s: str) -> str:
    s = s.strip()
    # Strip markdown fences: ```json ... ``` or ``` ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$",          "", s)
    s = s.strip()
    # Fix Python repr booleans/None that Llama sometimes echoes
    s = s.replace(": True,",  ": true,")
    s = s.replace(": True}",  ": true}")
    s = s.replace(": False,", ": false,")
    s = s.replace(": False}", ": false}")
    s = s.replace(": None,",  ": null,")
    s = s.replace(": None}",  ": null}")
    return s


def _try_parse(s: str) -> Any:
    """json.loads first; fall back to regex-extracting first array or object."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        pass
    # Greedy search for array
    m = re.search(r"\[.*\]", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # Greedy search for object
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _unwrap(value: Any, depth: int = 0) -> Any:
    """Recursively unwrap until we reach a dict or list (max 3 levels)."""
    if depth > 3:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        cleaned = _clean_string(value)
        parsed  = _try_parse(cleaned)
        if parsed is None:
            return None
        if isinstance(parsed, str):          # double-encoded — recurse
            return _unwrap(parsed, depth + 1)
        return parsed
    return None


# ── public API ───────────────────────────────────────────────────────────────

def parse_to_list(raw: Any) -> list:
    """
    Convert any LLM output into List[dict].
    Every element is guaranteed to be a dict — never a string.
    Returns [] on total failure, never raises.
    """
    # Unwrap fallback wrapper from old safe_json_parse
    if isinstance(raw, dict) and "raw_output" in raw:
        raw = raw["raw_output"]

    obj = _unwrap(raw)

    if obj is None:
        return []

    if isinstance(obj, dict):
        # Single dict — could be one result or a wrapper
        if "raw_output" in obj:
            return parse_to_list(obj["raw_output"])
        return [obj]

    if isinstance(obj, list):
        result = []
        for item in obj:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                parsed = _unwrap(item)
                if isinstance(parsed, dict):
                    result.append(parsed)
                elif isinstance(parsed, list):
                    result.extend(i for i in parsed if isinstance(i, dict))
        return result

    return []


def parse_to_dict(raw: Any, fallback: dict = None) -> dict:
    """
    Convert any LLM output into a single dict.
    Returns fallback (or {}) on failure — never raises.
    """
    if fallback is None:
        fallback = {}

    # Already a clean dict (not a fallback wrapper)
    if isinstance(raw, dict) and "raw_output" not in raw and raw:
        return raw

    obj = _unwrap(raw)

    if isinstance(obj, dict) and "raw_output" not in obj and obj:
        return obj

    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj[0]

    return fallback


def safe_float(value: Any, default: float = 0.0) -> float:
    """Cast anything to float, return default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
