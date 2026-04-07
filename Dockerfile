FROM python:3.13-slim

WORKDIR /app

COPY .venv/ .venv/
COPY backend/ backend/
COPY frontend/ frontend/

ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages"

EXPOSE 8000 8501
