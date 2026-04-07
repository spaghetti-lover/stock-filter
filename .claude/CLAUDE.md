Dont write bytecode please
For example: `python3 -B main.py`

Always use `python3` (not `python`) — the `python` command is not available in this environment.

Install packages with `uv add <package>` or `uv pip install <package>`, not `pip install`.

To run scripts inside the project's venv, prefix with `uv run`, e.g. `uv run python3 -B main.py`.

Dont create __pycache__. You can run make remove_pycache which is located at Makefile to remove __pycache__

## Import paths (backend/)

The backend runs from `backend/` as the working directory. Import accordingly:

- Market data functions: `from infrastructure.market_data.provider import get_all_symbols, get_trading_history, get_intraday`
- `backend/crawler/` exists but is **empty** — do not import from it
- Do NOT use `from crawler.crawler import ...` or `from market_data.provider import ...`

## Database

`DATABASE_URL` must use `localhost` as host, not `db`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_data
```
`db` is a Docker Compose service name and only resolves inside a Docker network. Uvicorn runs on the host, so use `localhost`.

## AI Agent architecture

Chat flow: **Streamlit UI → `POST /chat` → `ChatUseCase` → `AgentProvider` → LLM + tools**

Provider is selected per-request via `ChatRequest.provider` (default `"claude"`). Factory in `infrastructure/agents/factory.py` resolves it.

### Claude agent (`claude_agent.py`)
Uses `claude_agent_sdk` with an in-process MCP server (`create_sdk_mcp_server`). Tools defined in `infrastructure/agents/stock_tools.py`.

### Gemini agent (`gemini_agent.py`)
Uses Gemini function calling with an agentic loop (same tools, different mechanism):
- `response.function_calls` returns `list[FunctionCall]`
- `FunctionCall.name` and `FunctionCall.args` are both `Optional` — always guard: `fc.name or ""` and `fc.args or {}`
- Function response sent back via `types.Part.from_function_response(name=..., response=...)`
- Loop until `response.function_calls` is falsy (Gemini returns final text)

### OpenAI agent (`openai_agent.py`)
Uses `openai-agents` SDK (`Agent` + `Runner`). No MCP/tool integration yet.