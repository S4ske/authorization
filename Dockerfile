ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

ENV PYTHONPATH=/app

RUN pip install uv && uv pip install --system .

CMD python -m app.main
