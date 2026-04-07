# Setup & Running

## Prerequisites

- Python 3.13+
- `uv` package manager
- `vnstock_data` installed in project `.venv` (private/sponsored package — copy `.venv` manually)

## Environment

Create `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-proj-...
```

## Local Development

```bash
# Backend (from repo root)
cd backend && uv run uvicorn main:app --reload
# http://localhost:8000 — docs at /docs

# Frontend (from repo root)
cd frontend && uv run streamlit run app.py --server.headless true
# http://localhost:8501
```

## Docker (VPS / Production)

All services run via Docker Compose. The `.venv` must be present in the repo root before building (it contains `vnstock_data` which is not on PyPI).

```bash
# Copy .venv to VPS first
rsync -az --progress .venv/ user@your-vps:/path/to/stock-filter/.venv/

# Copy .env to VPS
scp backend/.env user@your-vps:/path/to/stock-filter/backend/.env

# On VPS — build and start in background
docker compose up -d --build

# Logs
docker compose logs -f

# Stop
docker compose down
```

Services:
- **backend** → `http://your-vps:8000`
- **frontend** → `http://your-vps:8501`

## Useful Commands

```bash
make remove_pycache   # Clean __pycache__ directories
```
