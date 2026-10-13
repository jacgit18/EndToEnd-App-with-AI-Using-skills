FROM python:3.14-slim

# uv is a single static binary — copying it from its own published image is
# the fastest way to get it into this one, no pip/curl install step needed.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

# Run as an unprivileged user (uid 10001): an RCE in a dependency should not be root in a
# container that holds the database password. /app is owned by it so dev's bind-mounted
# `uv run --reload` can still sync into /app/.venv; prod never writes here (read_only).
RUN useradd --system --uid 10001 --create-home --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir /app && chown app:app /app
WORKDIR /app
USER app

# uvicorn's import-string loader ("app.main:app") quietly adds the current
# working directory to sys.path itself, so `app.*` resolves without this.
# Alembic's env.py does no such thing — `from app.config import settings`
# there fails with ModuleNotFoundError unless `app` is actually importable,
# and pyproject.toml deliberately has no [build-system] (ADR-0011: this is
# an application, not an installable package). Setting PYTHONPATH here once
# fixes it for every command run in this image, not just uvicorn's.
ENV PYTHONPATH=/app
# Run the environment built below directly: no `uv run` at container start, so nothing is
# resolved, synced or downloaded at runtime (startup needs no network) and the filesystem
# can be read-only. No .pyc files for the same reason.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency files first so this layer is cached across builds that only
# change application code, not dependencies.
COPY --chown=app:app pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen --no-install-project

# Now the actual application code.
COPY --chown=app:app app ./app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations

EXPOSE 8000

# uvicorn comes from /app/.venv/bin (PATH above): the environment built above, no dev group,
# never re-synced from PyPI at container start.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
