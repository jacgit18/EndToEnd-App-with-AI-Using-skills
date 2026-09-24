"""Sentry is inert without a DSN and privacy-tight with one (ADR-0013).

Each case imports the app in a fresh subprocess: the SDK is initialised at import
time from settings, and a global Sentry client would leak between tests.
"""

import os
import subprocess
import sys

BASE_ENV = {
    "DATABASE_URL": "postgresql+psycopg://x:x@localhost/x",
    "AUTH_EMAIL": "a@b.c",
    # A real argon2 hash of "pw" — config validates the format at startup.
    "AUTH_PASSWORD_HASH": "$argon2id$v=19$m=65536,t=3,p=4$YWJjZGVmZ2hpamts$Zm9vYmFyYmF6cXV4Zm9vYmFyYmF6cXV4Zm9vYg",
    "SESSION_SECRET": "s",
}


def sentry_state(extra_env: dict[str, str]) -> str:
    code = (
        "import sentry_sdk, app.main;"
        "c = sentry_sdk.get_client();"
        "o = c.options;"
        "print(c.is_active(), o.get('send_default_pii'),"
        " o.get('max_request_body_size'), o.get('traces_sample_rate'))"
    )
    env = {**os.environ, **BASE_ENV, **extra_env}
    env.pop("SENTRY_DSN", None) if "SENTRY_DSN" not in extra_env else None
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def test_without_a_dsn_sentry_never_starts():
    assert sentry_state({}).startswith("False")


def test_with_a_dsn_it_starts_with_finance_safe_options():
    state = sentry_state({"SENTRY_DSN": "https://key@o0.ingest.sentry.io/1"})

    # active, no PII, request bodies never sent, no performance tracing
    assert state == "True False never 0.0"
