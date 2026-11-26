# Build context is the repository root, so one pyproject/uv.lock serves the CLI
# and the collector. uv installs only the collector's runtime needs via the
# `collector` extra.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra collector --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra collector

EXPOSE 4000

CMD ["uvicorn", "artex_gym.collector.app:app", "--host", "0.0.0.0", "--port", "4000", "--no-access-log", "--timeout-graceful-shutdown", "5"]
