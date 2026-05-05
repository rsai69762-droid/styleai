# syntax=docker/dockerfile:1.7
 
FROM python:3.11-slim AS builder
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
 
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*
 
WORKDIR /app
 
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .
 
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
 
 
FROM python:3.11-slim AS runtime
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"
 
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home /app app
 
WORKDIR /app
 
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
 
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*
 
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
 
USER app
 
EXPOSE 8000
 
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1
 
CMD ["/app/entrypoint.sh"]
 
 