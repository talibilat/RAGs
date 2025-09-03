# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN adduser --disabled-password --gecos "" app && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY README.md /app/README.md
COPY examples /app/examples

# Default data filename, can be overridden with -v or ENV
COPY financial_data.json /app/financial_data.json

ENV PYTHONPATH=/app/src \
    DATA_PATH=/app/financial_data.json \
    OPENAI_MODEL=gpt-4.1-mini \
    AGENT_OFFLINE_MODE=false \
    FEATURE_AGENT_ENABLED=false

USER app

ENTRYPOINT ["python", "-m", "agent.chat_cli", "chat"]
