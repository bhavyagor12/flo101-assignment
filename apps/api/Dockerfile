FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# System packages: curl for healthchecks, build tools for any wheels that need them
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /usr/local/bin/

WORKDIR /app

# Dependency layer (cached)
COPY apps/api/pyproject.toml apps/api/uv.lock* ./
RUN uv sync --no-install-project --frozen 2>/dev/null || uv sync --no-install-project

# Source
COPY apps/api/src ./src
RUN uv sync --frozen 2>/dev/null || uv sync

ENV PATH="/opt/venv/bin:${PATH}"

# Runtime data dirs
RUN mkdir -p /data /corpora

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["uv", "run", "uvicorn", "flo101_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
