# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY examples /app/examples
COPY financial_data.json /app/financial_data.json

ENV PYTHONPATH=/app/src \
    DATA_PATH=/app/financial_data.json \
    DATABASE_HOSTNAME=postgres \
    DATABASE_PORT=5432 \
    DATABASE_NAME=9fin \
    DATABASE_USERNAME=postgres \
    DATABASE_PASSWORD=password \
    OPENAI_MODEL=gpt-4o-mini \
    AGENT_OFFLINE_MODE=false \
    FEATURE_AGENT_ENABLED=false \
    LOG_LEVEL=INFO \
    DB_MAX_CONNECTIONS=10 \
    GIT_PYTHON_REFRESH=quiet

# Default command runs interactive chat CLI
CMD ["python", "-m", "agent.chat_cli", "chat"]
