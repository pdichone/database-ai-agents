# Hotfix notes: models and APIs

OpenAI shut down `gpt-3.5-turbo` and the **Assistants API**. Every lesson in this repo used one or
both, so the code no longer ran. This hotfix moves the course to `gpt-6-luna` and ports the
Assistants lesson to the **Responses API**. The teaching goal of every lesson is unchanged.

Run `pip install -r requirements.txt` (or `uv pip install -r requirements.txt`) in a fresh
virtual environment before you start. The old pins (LangChain 0.1.x) cannot talk to the new model.

## What the video shows vs what the code does now

| File | In the video | In the code now |
|---|---|---|
| `first_agent.py` | `llm_name = "gpt-3.5-turbo"` | `llm_name = "gpt-6-luna"`, and `ChatOpenAI(..., reasoning_effort="none")` |
| `csv_agent.py` | `gpt-3.5-turbo`, pandas agent with the default text (ReAct) agent | `gpt-6-luna` + `reasoning_effort="none"`. The agent now needs `allow_dangerous_code=True` (it runs Python on your machine) and `agent_type="tool-calling"`. The verbose log shows `Invoking: python_repl_ast ...` instead of `Thought / Action / Observation` lines |
| `fun_calling.py` | `gpt-4o` in both `chat.completions.create` calls | `model=llm_name` (`gpt-6-luna`) plus `reasoning_effort="none"`. `gpt-4o` shuts down Jan 14 2027 |
| `fun_call_db_agent.py` | `gpt-3.5-turbo` | `gpt-6-luna`, plus `reasoning_effort="none"` on both `chat.completions.create` calls |
| `sql_db_agent.py` | `gpt-3.5-turbo`, SQL agent with the text (ReAct) format | `gpt-6-luna` + `reasoning_effort="none"`, and `agent_type="tool-calling"`. Your `MSSQL_AGENT_PREFIX` is still used; `MSSQL_AGENT_FORMAT_INSTRUCTIONS` is ignored in this mode. The log shows `Invoking: sql_db_query ...` instead of `Thought / Action` lines |
| `assis_api_sql_db.py` | Assistants API: `assistants.create`, `threads.create`, `runs.create`, a polling loop, `submit_tool_outputs` | **Rewritten on the Responses API** (see below). **Re-record candidate** |
| `requirements.txt` | LangChain 0.1.x, openai 1.56 | LangChain 0.3.x, openai 1.109.1 (see below) |

## Why `reasoning_effort="none"` and `agent_type="tool-calling"`

- `gpt-6-luna` is a reasoning model. On Chat Completions it rejects function tools and
  `temperature` unless you pass `reasoning_effort="none"`.
- It also rejects the `stop` parameter. The old LangChain text agents (ReAct) depend on `stop`
  to halt at `Observation:`, so they fail with `Unsupported parameter: 'stop'`. Native tool calling
  (`agent_type="tool-calling"`) does the same job without it.

## The Assistants API to Responses API port (`assis_api_sql_db.py`)

Same database, same five helper functions in `helpers.py`, same question. The concepts map 1:1:

| Assistants API (video) | Responses API (code now) |
|---|---|
| `client.beta.assistants.create(name, model, tools)` | A plain `assistant` dict (`model`, `instructions`, `tools`) sent with every request |
| Nested tool schema `{"type": "function", "function": {...}}` | Flat schema `{"type": "function", "name": ..., "parameters": ...}`. We unwrap `helpers.tools_sql` in one line |
| `client.beta.threads.create()` | `client.conversations.create()` |
| `threads.messages.create(...)` + `runs.create(...)` | One `client.responses.create(..., conversation=..., input=[...])` call |
| Polling loop on `run.status` | Gone. The call returns when the model is done |
| `status == "requires_action"` / `tool_call.function.name` | `function_call` items in `response.output` / `tool_call.name`, `tool_call.arguments` |
| `runs.submit_tool_outputs(tool_call_id=..., output=...)` | Send `{"type": "function_call_output", "call_id": ..., "output": ...}` back to `responses.create` in the same conversation |
| `threads.messages.list(...)` | `client.conversations.items.list(...)`, and `response.output_text` for the final answer |

## Requirements pins (lessons run on Python 3.12; install also checked on 3.13)

`openai==1.109.1` (has the Responses and Conversations APIs, and keeps the student PR's fix for the
`proxies` error), `langchain==0.3.24`, `langchain-core==0.3.56`, `langchain-community==0.3.22`,
`langchain-experimental==0.3.4`, `langchain-openai==0.3.14`, `pandas==2.2.3`,
`pyodbc==5.2.0`, `streamlit==1.45.0`. The duplicate `pandas` line is gone.

You will see a `LangChainDeprecationWarning` for `from langchain.agents import create_sql_agent`.
It is only a warning; the import still works.

## Housekeeping

`__pycache__/` and `.DS_Store` are no longer tracked and are now in `.gitignore`.
