FROM python:3.13-slim

# uv is a single static binary — copying it from its own published image is
# the fastest way to get it into this one, no pip/curl install step needed.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app

# uvicorn's import-string loader ("app.main:app") quietly adds the current
# working directory to sys.path itself, so `app.*` resolves without this.
# Alembic's env.py does no such thing — `from app.config import settings`
# there fails with ModuleNotFoundError unless `app` is actually importable,
# and pyproject.toml deliberately has no [build-system] (ADR-0011: this is
# an application, not an installable package). Setting PYTHONPATH here once
# fixes it for every command run in this image, not just uvicorn's.
ENV PYTHONPATH=/app

# Copy dependency files first so this layer is cached across builds that only
# change application code, not dependencies.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen --no-install-project

# Now the actual application code.
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
