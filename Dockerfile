FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies (without dev deps, frozen lockfile)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy app source
COPY app ./app

# Sync again to install the project itself
RUN uv sync --frozen --no-dev

ENV PORT=8080
EXPOSE 8080

CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
