"""Fail fast and clearly when the integration tests have no usable Postgres.

Modules that import `app.db.SessionLocal` are the DB-backed integration tests
(TestClient + a real, migrated Postgres). If the database is unreachable, or
reachable but not migrated, they are skipped with one actionable reason instead
of erroring in setup one by one. Pure unit tests (money, config, importer, ...)
never need it and keep running.

CI=1 or REQUIRE_DB=1 turns the skip into a hard failure, so CI can never
silently skip the integration suite.
"""

import os
import socket

import psycopg
import pytest
from sqlalchemy.engine import make_url

DEFAULT_URL = "postgresql+psycopg://finance:finance@localhost:5433/finance"
HINT = (
    "start it: docker compose -f finance-dashboard/compose.yaml up -d db && "
    "(cd finance-dashboard/backend && PYTHONPATH=. uv run alembic upgrade head)"
)

# App settings are read at import time (app.config), so any test module that imports app code
# needs these set before collection. Set once here instead of relying on whichever DB test
# module happens to be imported first (test_money.py failed alone without them). setdefault: a
# real environment still wins. The email/password match the constants the DB test modules use.
from argon2 import PasswordHasher  # noqa: E402

os.environ.setdefault("DATABASE_URL", DEFAULT_URL)
os.environ.setdefault("AUTH_EMAIL", "test-owner@example.com")
os.environ.setdefault("AUTH_PASSWORD_HASH", PasswordHasher().hash("test-password"))
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

_problem: str | None = None  # set in pytest_configure; None = DB is usable


def _check_db() -> str | None:
    """Return a reason string if the DB is unusable, else None. Never runs migrations."""
    url = make_url(os.environ.get("DATABASE_URL", DEFAULT_URL))
    host, port = url.host or "localhost", url.port or 5432
    try:
        socket.create_connection((host, port), timeout=1).close()
    except OSError:
        return f"Postgres not reachable at {host}:{port} — {HINT}"
    try:
        dsn = url.set(drivername="postgresql").render_as_string(hide_password=False)
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            row = conn.execute("select to_regclass('public.alembic_version')").fetchone()
            if row[0] is None:
                return (
                    f"Postgres at {host}:{port} has no migrated schema — run: "
                    "cd finance-dashboard/backend && PYTHONPATH=. uv run alembic upgrade head"
                )
    except psycopg.Error as e:
        return f"Postgres at {host}:{port} refused the connection ({str(e).strip()}) — {HINT}"
    return None


def pytest_configure(config):
    global _problem  # probe the same default the test modules use
    _problem = _check_db()


def pytest_report_header(config):
    return f"postgres reachable and migrated: {'no - ' + _problem if _problem else 'yes'}"


def pytest_collection_modifyitems(config, items):
    if _problem is None:
        return
    db_items = [i for i in items if hasattr(i.module, "SessionLocal")]
    if db_items and (os.environ.get("CI") or os.environ.get("REQUIRE_DB")):
        pytest.exit(f"{_problem}\n(CI/REQUIRE_DB set: refusing to skip the integration suite)", returncode=1)
    skip = pytest.mark.skip(reason=_problem)
    for item in db_items:
        item.add_marker(skip)
