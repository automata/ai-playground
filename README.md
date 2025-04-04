# AI Playground

Random experiments with LLM and other ML/AI models and algorithms.

# Setup

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

# Usage

## Getting structured output from LLMs

Instruct to generate JSON output and validate with Pydantic JSON schema.

```bash
python validate_output.py
```

## Faking function/tools calls in DeepSeek (through OpenRouter)

DeepSeek V3 (neither R1) has no support to function/tool calling yet, but
it seems we can hack it using a prompt to get present the tools + query to
get tools calls required and then another prompt with the tools' evaluation
results + original query. Not sure if that works for complex scenarios though.

```bash
python openrouter_deepseek_tools.py
```

## Hello SLOP

Simple example of client/server for SLOP and how to call from a hacky DeepSeek.

```bash
python slop_server_add.py
python slop_client_add.py
```

## Hello MCP through OpenRouter

Super simple hello world using MCP server through a model that supports tools
through OpenRouter.

```bash
python mcp_server_add.py
python openrouter_mcp.py
```

## Tool calling through OpenRouter

Only supported LLMs (DeepSeek V3 doesn't support through OpenRouter yet)

```bash
python openrouter_tool_calling.py
```
