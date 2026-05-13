FROM python:3.13-slim

WORKDIR /app

# Install system deps needed by some packages (psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv (includes sponsored vnstock packages)
COPY .venv /app/.venv

# Copy backend source
COPY backend/ /app/backend/

# Put venv on PATH so `python3` resolves to venv interpreter
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/backend

EXPOSE 8000

CMD ["python3", "-B", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
