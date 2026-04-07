FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY frontend/ frontend/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000 8501
