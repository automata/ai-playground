"""Validate the output of a LLM against a JSON schema.

Usage:
python validate_output.py
"""

import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, ValidationError

load_dotenv()

deepseek_model = "deepseek/deepseek-chat-v3-0324:free"

SYSTEMN_PROMPT_TEMPLATE = """
{query}

Output using the following JSON schema:

{schema}

IMPORTANT:
- Do not add any other text than the JSON output.
- Do not add ```json at the beginning of the output.
- Do not add ``` at the end of the output.
"""

class Measurement(BaseModel):
    timestamp: datetime
    original_value: float
    original_unit: str
    converted_value: float
    converted_unit: str

def send_to_llm(messages, model):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 10000,
            "stream": True
        }

        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        whole_response = ""
        usage = None
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    if line == 'data: [DONE]':
                        break
                    line = line[6:]
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get('choices', [{}])[0].get('delta', {})

                        if 'content' in delta and delta['content'] is not None:
                            print(delta['content'], end="")
                            whole_response += delta['content']

                        if 'usage' in chunk:
                            usage = chunk['usage']
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue
        print("")
        return {"content": whole_response, "usage": usage}
    except Exception as e:
        return {"content": "", "reasoning": ""}

if __name__ == "__main__":
    query = """
    You are a generic conversor of measurements.
    You will receive a message with a measurement and you will need to convert it to the desired unit.
    """

    system_prompt = SYSTEMN_PROMPT_TEMPLATE.format(
        query=query,
        schema=Measurement.model_json_schema()
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "1000 meters to kilometers"}
    ]
    response = send_to_llm(messages, deepseek_model)

    try:
        # Validate
        m = Measurement(**json.loads(response["content"]))
        print("Valid JSON output:")
        print(m)
    except ValidationError as e:
        print("Invalid JSON output:", e)

