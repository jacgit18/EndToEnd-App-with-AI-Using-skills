#!/usr/bin/env bash
# Run the backend test suite against a throwaway Postgres, so the DB tests can never
# silently skip.
#
#   scripts/test-db.sh                                     # whole suite
#   scripts/test-db.sh tests/test_reconcile.py -k drift    # extra args go to pytest
#
# Why this exists: conftest.py skips every DB-backed test when it can't reach the
# configured Postgres. If another project's Postgres already owns host port 5433, the
# connection fails for the wrong reason and most of the suite skips quietly. This
# starts its own container on a random high port, migrates it, and sets REQUIRE_DB=1 so
# a missing DB is a failure, not a skip. The container is removed on exit.
set -euo pipefail

cd "$(dirname "$0")/../backend"

command -v docker >/dev/null || { echo "docker is required" >&2; exit 2; }

NAME="finance-test-db-$$-$RANDOM"
PORT=""

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# A random 55xxx port can collide with something else, so retry with a new one if
# docker refuses to bind it.
for _ in 1 2 3 4 5; do
  PORT=$((55000 + RANDOM % 1000))
  if docker run -d --name "$NAME" -p "127.0.0.1:${PORT}:5432" \
      -e POSTGRES_USER=finance -e POSTGRES_PASSWORD=finance -e POSTGRES_DB=finance \
      postgres:16-alpine >/dev/null 2>&1; then
    break
  fi
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  PORT=""
done
[ -n "$PORT" ] || { echo "could not start a postgres container on a free port" >&2; exit 2; }

echo "waiting for postgres on localhost:${PORT} ..."
ready=""
for _ in $(seq 1 60); do
  # The image's init phase runs a temporary server that also answers pg_isready, then
  # restarts. A real query over TCP only succeeds once the final server is up.
  if docker exec "$NAME" pg_isready -U finance -d finance -h 127.0.0.1 >/dev/null 2>&1 \
      && docker exec "$NAME" psql -U finance -d finance -h 127.0.0.1 -c 'select 1' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
[ -n "$ready" ] || { echo "postgres did not become ready in 60s" >&2; exit 2; }

export DATABASE_URL="postgresql+psycopg://finance:finance@localhost:${PORT}/finance"
export REQUIRE_DB=1

# app.config demands the auth settings at import time, and alembic's env.py imports it.
# Placeholders for this one command only (migrations never use them); exporting them
# would stop conftest.py's setdefault from supplying a hash that matches its test password.
AUTH_EMAIL="${AUTH_EMAIL:-migrate@example.com}" \
AUTH_PASSWORD_HASH="${AUTH_PASSWORD_HASH:-$(uv run python -c 'from argon2 import PasswordHasher; print(PasswordHasher().hash("x"))')}" \
SESSION_SECRET="${SESSION_SECRET:-unused-by-migrations}" \
PYTHONPATH=. uv run alembic upgrade head

# No `exec`: the EXIT trap has to run after pytest to remove the container.
rc=0
uv run pytest -q "$@" || rc=$?
exit "$rc"
