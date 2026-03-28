import boto3
import json
from enum import Enum

class TaskComplexity(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

client = boto3.client("bedrock-runtime", region_name="us-east-1")


def call_llm(system_prompt, user_prompt, complexity=TaskComplexity.COMPLEX):

    model_id = "meta.llama3-70b-instruct-v1:0"

    prompt = f"{system_prompt}\n\n{user_prompt}"

    body = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_gen_len": 500,
        "temperature": 0.5
    }

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    
    return result["generation"]
