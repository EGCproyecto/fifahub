# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=app:create_app \
    WORKING_DIR=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        curl \
        libffi-dev \
        mariadb-client \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoints/production_entrypoint.sh \
    && chmod +x scripts/wait-for-db.sh

EXPOSE 5000

ENTRYPOINT ["/app/docker/entrypoints/production_entrypoint.sh"]
