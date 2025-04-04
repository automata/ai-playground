import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, ValidationError
from pprint import pprint as pp
load_dotenv()

model = "deepseek/deepseek-chat-v3-0324:free"

p1 = """
Use the following tools to answer the user's question:

{
    "tools": [  
        {
            "tool_name": "add",
            "description": "Add two numbers, `a` and `b`, and returns their sum.",
            "parameters": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            }
        },
   ]
}

Instead of answering a question that requires a tool call, DO NOT ANSWER THE QUESTION
but list the required tool calls in your response.

Example:

User: What is 2 + 3?
Assistant:
{
    "tools": [
        {
            "tool_name": "add",
            "parameters": {
                "a": 2,
                "b": 3
            }
        }
    ]
}
"""

p2 = """
You are an assistant that can answer questions based on previous results from tool calls.

You're going to receive a list of tool calls and the results of the tool calls.

They will have this format:

{
    "tools": [
        {
            "tool_name": "tool_name",
            "parameters": {
                "arg1": "arg1",
                "arg2": "arg2",
            },
            "result": "result"
        }
    ]
}

Example:

{
    "tools": [
        {
            "tool_name": "add",
            "parameters": {
                "a": 2,
                "b": 3
            },
            "result": 5
        },
    ]
}

Question:
What is 2 + 3?

Answer the user's question based on the results of the tool calls.
"""

def tool_add_call(a, b):
    res = requests.post(f"http://localhost:3030/tools/add", json={"a": a, "b": b})
    return res.json()["result"]

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
                            # print(delta['content'], end="")
                            whole_response += delta['content']

                        if 'usage' in chunk:
                            usage = chunk['usage']
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue
        # print("")
        return {"content": whole_response, "usage": usage}
    except Exception as e:
        return {"content": "", "reasoning": ""}

if __name__ == "__main__":
    query = """
    What are the books wrote by Dickens?
    """

    m1 = [
        {"role": "system", "content": p1},
        {"role": "user", "content": query}
    ]
    response = send_to_llm(m1, model)
    print("Response 1:", response["content"])

    tool_calls = response["content"]

    tool_calls_json = json.loads(tool_calls)

    tool_calls_results = {}
    for tool_call in tool_calls_json["tools"]:
        if tool_call["tool_name"] == "add":
            result = tool_add_call(tool_call["parameters"]["a"], tool_call["parameters"]["b"])
            tool_calls_results[tool_call["tool_name"]] = result
        else:
            raise ValueError(f"Unknown tool call: {tool_call['tool_name']}")

    pp(tool_calls_results)

    query = f"""
    Tool calls:
    {json.dumps(tool_calls_results)}

    Question:
    {query}
    """

    m2 = [
        {"role": "system", "content": p2},
        {"role": "user", "content": query}
    ]
    response = send_to_llm(m2, model)
    print("Response 2:", response["content"])