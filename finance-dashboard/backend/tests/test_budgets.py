"""Budgets API (S6) through the real app, against a real migrated Postgres.

Same setup as test_accounts.py: `app.main.app` over TestClient, the Compose db on
host port 5433 by default, results verified by a direct read of the rows as well as
by the HTTP response.

Every category made here is named `__t_<...>`; the autouse fixture deletes exactly
the budgets, categories and login sessions that appeared during the test. Seeded
categories are never given a budget. Months used are far in the future (2031) so a
real budget can never collide with a test row.

Env is set before `app` is imported, with the same values as test_auth.py and
test_accounts.py so any of them can be imported first.
"""

import os

from argon2 import PasswordHasher

TEST_EMAIL = "test-owner@example.com"
TEST_PASSWORD = "test-password"

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://finance:finance@localhost:5433/finance")
os.environ.setdefault("AUTH_EMAIL", TEST_EMAIL)
os.environ.setdefault("AUTH_PASSWORD_HASH", PasswordHasher().hash(TEST_PASSWORD))
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

import uuid  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.budget import Budget  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.session import AuthSession  # noqa: E402

PREFIX = "__t_"
M = "2031-05"  # the month under test; PREV is the one before it
PREV = "2031-04"


@pytest.fixture(autouse=True)
def clean_state():
    """Delete only what this test created: new `__t_` categories (and the budgets
    that hang off them, first, for the FK) and new login sessions."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        categories_before = set(db.scalars(select(Category.id)))
        sessions_before = set(db.scalars(select(AuthSession.id)))
    try:
        yield
    finally:
        with SessionLocal() as db:
            new_categories = [
                c.id
                for c in db.scalars(select(Category).where(Category.name.startswith(PREFIX, autoescape=True)))
                if c.id not in categories_before
            ]
            if new_categories:
                db.execute(delete(Budget).where(Budget.category_id.in_(new_categories)))
                db.execute(delete(Category).where(Category.id.in_(new_categories)))
            new_sessions = set(db.scalars(select(AuthSession.id))) - sessions_before
            if new_sessions:
                db.execute(delete(AuthSession).where(AuthSession.id.in_(new_sessions)))
            db.commit()


@pytest.fixture
def client():
    c = TestClient(app)
    response = c.post(
        "/api/auth/login", json={"email": settings.auth_email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    c.headers[CSRF_HEADER_NAME] = response.json()["csrf_token"]
    return c


# --------------------------------------------------------------------------- helpers


def make_category(client, archived: bool = False) -> int:
    response = client.post(
        "/api/categories", json={"name": f"{PREFIX}b_{uuid.uuid4().hex[:10]}", "kind": "expense"}
    )
    assert response.status_code == 201, response.text
    cid = response.json()["id"]
    if archived:
        assert client.patch(f"/api/categories/{cid}", json={"is_archived": True}).status_code == 200
    return cid


def put(client, month, cid, amount):
    return client.put(f"/api/budgets/{month}/{cid}", json={"amount": amount})


def rows(cid) -> list[tuple[str, str]]:
    with SessionLocal() as db:
        return [
            (b.month, str(b.amount))
            for b in db.scalars(select(Budget).where(Budget.category_id == cid).order_by(Budget.month))
        ]


# --------------------------------------------------------------------------- set / edit


def test_set_creates_a_row(client):
    cid = make_category(client)
    r = put(client, M, cid, "250.00")
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == "250.00" and r.json()["month"] == M
    assert rows(cid) == [(M, "250.00")]


def test_set_again_overwrites_and_leaves_one_row(client):
    cid = make_category(client)
    put(client, M, cid, "250.00")
    r = put(client, M, cid, "300.50")
    assert r.status_code == 200
    assert rows(cid) == [(M, "300.50")]


def test_integer_amount_is_accepted(client):
    cid = make_category(client)
    assert put(client, M, cid, 100).status_code == 200
    assert rows(cid) == [(M, "100.00")]


@pytest.mark.parametrize(
    "amount", [100.5, "0", "0.00", "-5", "abc", "1.234", "1E+3", " 5 ", None, "1" * 13, ""]
)
def test_bad_amounts_are_422_and_save_nothing(client, amount):
    cid = make_category(client)
    assert put(client, M, cid, amount).status_code == 422
    assert rows(cid) == []


def test_extra_body_field_is_422(client):
    cid = make_category(client)
    r = client.put(f"/api/budgets/{M}/{cid}", json={"amount": "5", "ammount": "6"})
    assert r.status_code == 422
    assert rows(cid) == []


@pytest.mark.parametrize("month", ["2031-13", "2031-00", "2031-5", "2031-05-01", "0000-01", "abcd-01", "２０３１-05"])
def test_bad_month_is_422(client, month):
    cid = make_category(client)
    assert put(client, month, cid, "5").status_code == 422
    assert client.get("/api/budgets", params={"month": month}).status_code == 422
    assert rows(cid) == []


def test_unknown_category_is_404(client):
    assert put(client, M, 2_000_000_000, "5").status_code == 404


def test_archived_category_is_409(client):
    cid = make_category(client, archived=True)
    assert put(client, M, cid, "5").status_code == 409
    assert rows(cid) == []


# --------------------------------------------------------------------------- list / delete


def test_list_returns_only_that_month(client):
    a, b = make_category(client), make_category(client)
    put(client, M, a, "10")
    put(client, M, b, "20")
    put(client, PREV, a, "99")
    got = client.get("/api/budgets", params={"month": M}).json()
    mine = {(x["category_id"], x["amount"]) for x in got if x["category_id"] in (a, b)}
    assert mine == {(a, "10.00"), (b, "20.00")}
    assert all(x["month"] == M for x in got)


def test_list_requires_month(client):
    assert client.get("/api/budgets").status_code == 422


def test_delete_removes_only_that_line(client):
    cid = make_category(client)
    put(client, M, cid, "10")
    put(client, PREV, cid, "20")
    assert client.delete(f"/api/budgets/{M}/{cid}").status_code == 204
    assert rows(cid) == [(PREV, "20.00")]


def test_delete_missing_is_404(client):
    cid = make_category(client)
    assert client.delete(f"/api/budgets/{M}/{cid}").status_code == 404


# --------------------------------------------------------------------------- copy-forward


def copy(client, month=M):
    return client.post(f"/api/budgets/{month}/copy-forward")


def test_copy_forward_copies_previous_month(client):
    a, b = make_category(client), make_category(client)
    put(client, PREV, a, "10")
    put(client, PREV, b, "20.25")
    r = copy(client)
    assert r.status_code == 200, r.text
    assert r.json() == {"copied": 2, "skipped": 0}
    assert rows(a) == [(PREV, "10.00"), (M, "10.00")]
    assert rows(b) == [(PREV, "20.25"), (M, "20.25")]


def test_copy_forward_never_overwrites_and_counts_skips(client):
    a, b = make_category(client), make_category(client)
    put(client, PREV, a, "10")
    put(client, PREV, b, "20")
    put(client, M, a, "77")  # already budgeted this month: must survive
    r = copy(client)
    assert r.json() == {"copied": 1, "skipped": 1}
    assert rows(a) == [(PREV, "10.00"), (M, "77.00")]
    assert rows(b) == [(PREV, "20.00"), (M, "20.00")]


def test_copy_forward_skips_archived_categories(client):
    a, b = make_category(client), make_category(client)
    put(client, PREV, a, "10")
    put(client, PREV, b, "20")
    client.patch(f"/api/categories/{b}", json={"is_archived": True})
    r = copy(client)
    assert r.json() == {"copied": 1, "skipped": 1}
    assert rows(b) == [(PREV, "20.00")]


def test_copy_forward_twice_copies_nothing_the_second_time(client):
    a = make_category(client)
    put(client, PREV, a, "10")
    assert copy(client).json() == {"copied": 1, "skipped": 0}
    assert copy(client).json() == {"copied": 0, "skipped": 1}
    assert rows(a) == [(PREV, "10.00"), (M, "10.00")]


def test_copy_forward_from_empty_month_is_zero(client):
    assert copy(client, "2031-07").json() == {"copied": 0, "skipped": 0}


def test_copy_forward_january_reads_december_of_prior_year(client):
    a = make_category(client)
    put(client, "2030-12", a, "40")
    assert copy(client, "2031-01").json() == {"copied": 1, "skipped": 0}
    assert rows(a) == [("2030-12", "40.00"), ("2031-01", "40.00")]


def test_copy_forward_into_earliest_month_is_422(client):
    assert copy(client, "1000-01").status_code == 422


def test_copy_forward_bad_month_is_422(client):
    assert copy(client, "2031-13").status_code == 422


# --------------------------------------------------------------------------- auth


def test_unauthenticated_is_401():
    c = TestClient(app)
    assert c.get("/api/budgets", params={"month": M}).status_code == 401
    assert c.put(f"/api/budgets/{M}/1", json={"amount": "5"}).status_code == 401


def test_write_without_csrf_header_is_refused(client):
    cid = make_category(client)
    del client.headers[CSRF_HEADER_NAME]
    assert put(client, M, cid, "5").status_code == 403
    assert client.delete(f"/api/budgets/{M}/{cid}").status_code == 403
    assert copy(client).status_code == 403
    assert rows(cid) == []
