FROM python:3.14-slim

WORKDIR /app

COPY .venv .venv
COPY backend/ backend/
COPY frontend/ frontend/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000 8501
