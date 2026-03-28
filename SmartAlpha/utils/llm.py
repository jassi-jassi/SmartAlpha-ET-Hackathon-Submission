import boto3
from enum import Enum

class TaskComplexity(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

client = boto3.client("bedrock-runtime", region_name="us-east-1")


def call_llm(system_prompt, user_prompt, complexity=TaskComplexity.COMPLEX):

    model_id = "us.meta.llama3-3-70b-instruct-v1:0"

    prompt = f"{system_prompt}\n\n{user_prompt}"

    response = client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0.5,
            "topP": 0.9
        }
    )

    return response["output"]["message"]["content"][0]["text"]
