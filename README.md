# Vietnam Stock Filter

A web app that filters Vietnamese stocks (HOSE / HNX / UPCOM) using trading metrics, with a built-in AI chat assistant for analysis.

- **Backend**: FastAPI + PostgreSQL + APScheduler, structured as Clean Architecture
- **Frontend**: Next.js 15 (App Router, React 19, TypeScript) served by Bun
- **Data source**: `vnstock_data` 3.2.1 (sponsored) — daily crawler + on-demand live API
- **AI agents**: Claude, Gemini, and Qwen (selectable per chat request)

---

## Quick start

Prereqs: Docker, [uv](https://github.com/astral-sh/uv) (Python), [Bun](https://bun.sh/), and a working `~/.venv` containing `vnstock_data` (see CLAUDE.md → "Environment & Installation").

1. **Create `backend/.env`** (see [Environment](#environment) below).
2. **Start the database**:
   ```bash
   make db_start
   make migrate
   ```
3. **Backend** (in one terminal):
   ```bash
   make backend
   # → http://localhost:8000  (docs at /docs)
   ```
4. **Frontend** (in another):
   ```bash
   make frontend_install   # first time only
   make frontend
   # → http://localhost:3000
   ```

For production: `docker compose up -d --build`.

---

## Repository layout

```
stock-filter/
├── backend/
│   ├── main.py                    # FastAPI entrypoint, lifespan wires DB + scheduler + MCP tools
│   ├── domain/                    # Entities, repository interfaces, value objects
│   ├── application/               # Use cases, DTOs, mappers, stock filter service
│   ├── infrastructure/
│   │   ├── container.py           # DI composition root
│   │   ├── persistence/           # PG repositories + live vnstock repository, shared stock_metrics
│   │   ├── market_data/           # vnstock API wrappers with rate limiting
│   │   ├── agents/                # claude_agent.py, gemini_agent.py, qwen_agent.py, factory.py
│   │   ├── scheduler/             # APScheduler (daily crawl @ 16:00 VN)
│   │   ├── scrapers/              # Discussion/forum scrapers
│   │   ├── tools/                 # MCP tool registry
│   │   ├── mcp/                   # In-process MCP server bits
│   │   └── tradingagents/         # Trading-agent experimental code
│   ├── presentation/api/routes/   # FastAPI routers (see "API surface")
│   ├── db/
│   │   ├── connection.py          # asyncpg pool
│   │   └── migrations/            # yoyo SQL migrations
│   └── Dockerfile
├── frontend/                      # Next.js + Bun
│   └── src/
│       ├── app/                   # App Router pages
│       ├── components/chat/       # ChatComposer, ChatThread, ChartBlock, Markdown,
│       │                          #   ModelPicker, ProviderPicker, modelCatalog
│       └── lib/
│           ├── store.ts           # Zustand store (persists lastStocks for chat context)
│           ├── scoring.ts         # Verbatim port of Streamlit recompute_scores — parity required
│           └── types.ts
├── docs/                          # vnstock library docs + project notes (filter.md, chart.md)
├── docker-compose.yml
├── Makefile
├── CLAUDE.md                      # Project rules for AI agents (READ THIS)
└── .claude/CLAUDE.md              # Environment-specific rules (READ THIS)
```

---

## Architecture

Clean Architecture, four layers:

| Layer          | Path                          | Contains                                                                            |
| -------------- | ----------------------------- | ----------------------------------------------------------------------------------- |
| Domain         | `backend/domain/`             | `Stock` entity, `Layer1StockRepository`, `CrawlRepository`, `MarketRegime`          |
| Application    | `backend/application/`        | `Layer1UseCase`, `CrawlUseCase`, DTOs, mappers, stock filter service                |
| Infrastructure | `backend/infrastructure/`     | Repository implementations, vnstock wrappers, AI agents, scheduler, MCP tools       |
| Presentation   | `backend/presentation/api/`   | FastAPI routes                                                                      |

The composition root is `backend/infrastructure/container.py`. The lifespan in `backend/main.py` initializes the DB pool, MCP tool registry, and APScheduler in that order — and tears them down in reverse on shutdown.

### Data flow

- **Cached (default)**: Next.js → `GET /layer1` → `Layer1UseCase` → `Layer1StockRepositoryDB` → PostgreSQL
- **Live (stream)**: Next.js (EventSource) → `GET /layer1/stream` → `Layer1UseCase` → `Layer1StockRepositoryImpl` → vnstock API
- **Daily crawl**: APScheduler (16:00 VN) → `CrawlUseCase` → `CrawlRepositoryImpl` → vnstock API → PostgreSQL
- **Chat**: Next.js → `POST /chat` → `ChatUseCase` → `AgentProvider` (Claude/Gemini/Qwen) → LLM + tools

---

## API surface

Routes are registered in `backend/main.py`. The notable endpoints:

| Method | Path                | Source                          | Notes                                       |
| ------ | ------------------- | ------------------------------- | ------------------------------------------- |
| GET    | `/layer1`           | `routes/layer1.py`              | Cached results from PostgreSQL              |
| GET    | `/layer1/stream`    | `routes/layer1.py`              | Live SSE — recomputes from vnstock          |
| GET    | `/layer2`           | `routes/layer2.py`              | Weighted scoring (also recomputed client-side in `scoring.ts`) |
| GET    | `/smart-money`      | `routes/smart_money.py`         | Foreign + proprietary flow signals          |
| POST   | `/chat`             | `routes/chat.py`                | Provider selected via `ChatRequest.provider` |
| ...    | `/trading-agent/*`  | `routes/trading_agent.py`       | Multi-step trading agent experiments        |
| GET    | `/symbols`          | `routes/symbols.py`             | Symbol metadata                             |
| GET    | `/discussions`      | `routes/discussions.py`         | Crawled forum posts                         |
| POST   | `/crawl/trigger`    | (see route files)               | Manual crawl                                |
| GET    | `/crawl/status`     | (see route files)               | Last crawl status                           |

OpenAPI docs: `http://localhost:8000/docs`.

---

## AI agent architecture

Chat flow: **frontend → `POST /chat` → `ChatUseCase` → `AgentProvider` → LLM + tools**

Provider is chosen per-request via `ChatRequest.provider` (default `"claude"`). The factory at `backend/infrastructure/agents/factory.py` resolves the name to an implementation.

| Provider | File                                    | Mechanism                                                                          |
| -------- | --------------------------------------- | ---------------------------------------------------------------------------------- |
| Claude   | `infrastructure/agents/claude_agent.py` | `claude_agent_sdk` with in-process MCP server (`create_sdk_mcp_server`)            |
| Gemini   | `infrastructure/agents/gemini_agent.py` | Gemini function calling, agentic loop (guard `fc.name or ""` and `fc.args or {}`)  |
| Qwen     | `infrastructure/agents/qwen_agent.py`   | DashScope-based Qwen                                                               |

Tool definitions for Claude live in `infrastructure/agents/stock_tools.py`. Model catalog (what shows up in the picker) is the frontend file `src/components/chat/modelCatalog.ts` — keep it in sync with backend support.

---

## Database

PostgreSQL, database `stock_data`. Tables:

- `stock_metrics` — crawled per-symbol metrics (PK `symbol`)
- `crawl_log` — crawl run history
- `discussion_posts`, `scraper_cursor`, `discussion_crawl_log` — forum scraper state

Connection pool: `backend/db/connection.py` (asyncpg). Migrations are managed by `yoyo`:

```bash
make migrate            # apply locally
make migrate_rollback   # roll back last migration locally
make migrate_prod       # apply inside the running backend container
```

Quick health checks:

```bash
make db_check           # stock metrics + last 5 crawl logs
make discussion_check   # discussion crawler state
```

---

## Environment

`backend/.env` must contain:

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-proj-...
DASHSCOPE_API_KEY=sk-...          # Qwen
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_data
# Optional:
CORS_ALLOW_ORIGINS=http://localhost:3000
```

Important: when running uvicorn on the host, `DATABASE_URL` host MUST be `localhost`, not `db` — see `.claude/CLAUDE.md`. The `db-stock-data` hostname only resolves inside the Docker Compose network.

Frontend reads `NEXT_PUBLIC_BACKEND_URL` (defaults to `http://localhost:8000`).

---

## Conventions (please read before editing)

These come from `CLAUDE.md` and `.claude/CLAUDE.md` — they are not optional:

1. **Run Python from inside the venv**: `uv run python3 -B main.py`. Always `python3`, never `python`.
2. **Never write bytecode**: pass `-B`, and run `make remove_pycache` if `__pycache__` directories appear.
3. **Install packages with uv**: `uv add <pkg>` or `uv pip install <pkg>`, never bare `pip install`.
4. **Backend imports are rooted at `backend/`** (that's the uvicorn working directory):
   - ✅ `from infrastructure.market_data.provider import get_all_symbols`
   - ❌ `from market_data.provider import ...`
   - ❌ `from crawler.crawler import ...` — `backend/crawler/` exists but is empty
5. **`scoring.ts` must stay numerically identical to the Streamlit `recompute_scores`** — Layer 2 weights are recomputed client-side and need exact parity.
6. **Use Unified UI for `vnstock_data`** (v3.0.0+): `Market().equity(symbol).ohlcv(...)` etc. `show_api()` lists only the abbreviated tree — many methods are hidden; use `dir(Market().equity("VCB"))` to see the full surface.
7. **Intraday `time` column is a `datetime`** — convert before writing: `df["time"] = df["time"].dt.time`.
8. **TCBS source is deprecated**. Prefer VCI or KBS.

---

## Common tasks

- **Add a new AI provider**: implement an `AgentProvider` under `backend/infrastructure/agents/`, register it in `factory.py`, add its models to `frontend/src/components/chat/modelCatalog.ts`, and surface it in `ProviderPicker.tsx`.
- **Add a new metric**:
  1. Write a SQL migration in `backend/db/migrations/`.
  2. Add the column to `Stock` (`domain/`) and the mappers (`application/`).
  3. Compute it in `infrastructure/persistence/stock_metrics.py` (shared by live + DB paths).
  4. Surface it in the relevant route + the frontend table.
- **Trigger a manual crawl**: `POST /crawl/trigger`, then watch `GET /crawl/status` or `make db_check`.
- **Reset the DB**: `make db_stop && make db_start && make migrate`.

---

## Pointers for picking up the project

- Start in `backend/main.py` — the lifespan tells you the full startup order.
- Then read `backend/infrastructure/container.py` to see how use cases are wired.
- For the chat side, `backend/presentation/api/routes/chat.py` → `application/` → `infrastructure/agents/factory.py`.
- For the data side, `backend/presentation/api/routes/layer1.py` → `Layer1UseCase` → either `Layer1StockRepositoryDB` or `Layer1StockRepositoryImpl`.
- Frontend entry: `frontend/src/app/` (App Router). Chat lives under `components/chat/`. Persistent state in `lib/store.ts`.
- Project-specific docs and screenshots are in `docs/`. `docs/filter.md` is the long-form filter spec.
