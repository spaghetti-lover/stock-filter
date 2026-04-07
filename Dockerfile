FROM python:3.13-slim

WORKDIR /app

COPY .venv/ .venv/
COPY backend/ backend/
COPY frontend/ frontend/

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

EXPOSE 8000 8501
