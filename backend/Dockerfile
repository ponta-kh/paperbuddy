FROM ghcr.io/astral-sh/uv:0.11.19-python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY main.py ./
COPY src ./src


FROM ghcr.io/astral-sh/uv:0.11.19-python3.14-trixie-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/tmp

WORKDIR /app

COPY --from=builder --chown=10001:10001 /app /app

USER 10001:10001

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
