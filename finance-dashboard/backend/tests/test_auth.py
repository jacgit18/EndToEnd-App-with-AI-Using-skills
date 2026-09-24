"""Login, session cookie, CSRF, logout and rate limiting through the real app (ADR-0010, ADR-0016).

Integration tests: they drive `app.main.app` over FastAPI's TestClient against
a real Postgres, because login inserts a `sessions` row and every protected
request looks that row up. Point DATABASE_URL at a migrated database (the
Compose db on host port 5433 by default); if none is reachable these fail
loudly rather than skip.

Env is set before `app` is imported, since config.py builds `settings` at import
time. `setdefault` means a real environment (CI) still wins over these values.
"""

import os

from argon2 import PasswordHasher

TEST_EMAIL = "test-owner@example.com"
TEST_PASSWORD = "test-password"

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://finance:finance@localhost:5433/finance")
os.environ.setdefault("AUTH_EMAIL", TEST_EMAIL)
os.environ.setdefault("AUTH_PASSWORD_HASH", PasswordHasher().hash(TEST_PASSWORD))
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.session import AuthSession  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh rate-limit counters, and delete only the sessions this test created
    (never the whole table — that would log out a real dev browser)."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        before = set(db.scalars(select(AuthSession.id)))
    yield
    with SessionLocal() as db:
        after = set(db.scalars(select(AuthSession.id)))
        db.execute(delete(AuthSession).where(AuthSession.id.in_(after - before)))
        db.commit()


@pytest.fixture
def client():
    return TestClient(app)


def login(client, password=None):
    return client.post(
        "/api/auth/login",
        json={
            "email": settings.auth_email,
            "password": TEST_PASSWORD if password is None else password,
        },
    )


def test_login_sets_httponly_cookie_and_returns_csrf_token(client):
    response = login(client)

    assert response.status_code == 200
    assert response.json()["csrf_token"]
    set_cookie = response.headers["set-cookie"]
    assert set_cookie.startswith(f"{SESSION_COOKIE_NAME}=")
    assert "HttpOnly" in set_cookie


def test_wrong_password_and_wrong_email_get_the_same_401(client):
    wrong_password = login(client, password="nope")
    wrong_email = client.post(
        "/api/auth/login", json={"email": "someone@else.com", "password": TEST_PASSWORD}
    )

    assert wrong_password.status_code == wrong_email.status_code == 401
    assert wrong_password.json() == wrong_email.json()


def test_protected_route_without_a_session_is_401(client):
    assert client.get("/api/accounts").status_code == 401


def test_protected_route_with_a_session_is_200(client):
    login(client)

    assert client.get("/api/accounts").status_code == 200


def test_tampered_cookie_is_401(client):
    login(client)
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-signed-value")

    assert client.get("/api/accounts").status_code == 401


def test_write_without_csrf_token_is_403(client):
    login(client)

    assert client.post("/api/accounts", json={}).status_code == 403


def test_write_with_csrf_token_gets_past_the_csrf_check(client):
    csrf_token = login(client).json()["csrf_token"]

    response = client.post(
        "/api/accounts", json={}, headers={CSRF_HEADER_NAME: csrf_token}
    )

    # Empty body fails validation (422), which only happens after auth + CSRF pass.
    assert response.status_code == 422


def test_me_reissues_a_working_csrf_token_and_requires_a_session(client):
    assert client.get("/api/auth/me").status_code == 401

    login(client)
    token = client.get("/api/auth/me").json()["csrf_token"]
    response = client.post("/api/accounts", json={}, headers={CSRF_HEADER_NAME: token})

    assert response.status_code == 422  # past auth + CSRF, fails on the empty body


def test_logout_invalidates_the_session_server_side(client):
    csrf_token = login(client).json()["csrf_token"]
    cookie = client.cookies.get(SESSION_COOKIE_NAME)

    assert client.post("/api/auth/logout").status_code == 204

    # Replay the old cookie by hand: the row is gone, so it must not work.
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    assert client.get("/api/accounts").status_code == 401


def test_login_is_rate_limited_after_max_attempts(client):
    codes = [login(client, password="nope").status_code for _ in range(rate_limit.MAX_ATTEMPTS)]
    blocked = login(client)

    assert set(codes) == {401}
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
