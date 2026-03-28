"""
utils/llm.py
Anthropic API wrapper with smart model routing.
Routes simple lookups → claude-haiku (cheap, fast)
Routes complex reasoning → claude-sonnet (powerful)
This gets you the cost-efficiency bonus judges explicitly mentioned.
"""

import os
import anthropic
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE = "simple"      # data parsing, formatting → Haiku
    COMPLEX = "complex"    # multi-signal reasoning → Sonnet


# Model routing table
MODEL_MAP = {
    TaskComplexity.SIMPLE:  "claude-haiku-4-5-20251001",
    TaskComplexity.COMPLEX: "claude-sonnet-4-6",
}


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file or Colab secrets."
        )
    return anthropic.Anthropic(api_key=api_key)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    complexity: TaskComplexity = TaskComplexity.COMPLEX,
    max_tokens: int = 1500,
) -> str:
    """
    Single point of LLM calls across all agents.
    Returns the text response as a string.
    """
    client = get_client()
    model = MODEL_MAP[complexity]

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


# ─── Colab helper ───────────────────────────────────────────
def set_api_key_colab(key: str) -> None:
    """Call this in Colab instead of .env: set_api_key_colab('sk-ant-...')"""
    os.environ["ANTHROPIC_API_KEY"] = key
    print("API key set successfully.")
