"""
utils/llm.py

AWS Bedrock Llama 3 client.

Fixes vs original:
  1. maxTokens hardcoded at 500 — too small for complex JSON, causes truncation
     and json.loads failures. Now 1500 for COMPLEX, 600 for SIMPLE.
  2. No retry on throttle — transient Bedrock errors killed the whole pipeline.
     Now retries twice with back-off.
  3. Bare boto3 client at module level crashed on import without AWS credentials.
     Moved to lazy get_client().
  4. complexity param was accepted but ignored — no actual routing.
     Now routes to different token budgets (model swap hook included).
"""

import time
import boto3
from botocore.exceptions import ClientError
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE  = "simple"
    COMPLEX = "complex"

MODEL_MAP = {
    TaskComplexity.SIMPLE:  "us.meta.llama3-3-70b-instruct-v1:0",
    TaskComplexity.COMPLEX: "us.meta.llama3-3-70b-instruct-v1:0",
}

TOKEN_MAP = {
    TaskComplexity.SIMPLE:   600,
    TaskComplexity.COMPLEX: 1500,
}

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name="us-east-1")
    return _client


def call_llm(
    system_prompt: str,
    user_prompt: str,
    complexity: TaskComplexity = TaskComplexity.COMPLEX,
    max_tokens: int = None,
    retries: int = 2,
) -> str:
    """
    Call Bedrock Llama via the converse API.
    Returns raw text. Raises RuntimeError after all retries exhausted.
    """
    model_id = MODEL_MAP[complexity]
    n_tokens = max_tokens or TOKEN_MAP[complexity]
    prompt   = f"{system_prompt}\n\n{user_prompt}"

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = get_client().converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={
                    "maxTokens":   n_tokens,
                    "temperature": 0.3,
                    "topP":        0.9,
                },
            )
            return response["output"]["message"]["content"][0]["text"]

        except ClientError as e:
            last_error = e
            code = e.response["Error"]["Code"]
            if code in ("ThrottlingException", "ServiceUnavailableException") and attempt < retries:
                time.sleep(3 * attempt)
                continue
            break

        except Exception as e:
            last_error = e
            break

    raise RuntimeError(f"call_llm failed after {retries} attempt(s): {last_error}")
