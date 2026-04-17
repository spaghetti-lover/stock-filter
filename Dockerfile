FROM python:3.13-slim

WORKDIR /app

COPY .venv/ .venv/
COPY backend/ backend/
COPY frontend/ frontend/

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/
RUN curl -fsSL https://claude.ai/install.sh | bash
RUN echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && . ~/.bashrc

ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages"

EXPOSE 8000 8501