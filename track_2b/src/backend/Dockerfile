# ── deps stage ────────────────────────────────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── dev stage ─────────────────────────────────────────────────────────
FROM deps AS dev

COPY . .
RUN uv sync --frozen --no-install-project

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── prod stage ────────────────────────────────────────────────────────
FROM deps AS prod

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
