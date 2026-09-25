"""Transactions API (S4: add + void + list filters) through the real app.

Same setup as test_accounts.py: `app.main.app` over TestClient against a real,
migrated Postgres (the Compose db on host port 5433 by default). Every money
outcome is verified by effect, with a direct SQL read of the account row and its
ledger, against ADR-0005's invariant:

    balance == starting_balance + SUM(transactions.amount)

The ledger is append-only (ADR-0005): a void posts a reversal row and leaves the
original untouched, so the tests check both rows, not just the response.

Every account and category made here is named `__t_<...>`; the autouse fixture
deletes exactly the transactions (reversals first: they point at their originals
through a FK), accounts, categories and login sessions that appeared during the
test, so the dev database is never left dirty and nothing pre-existing is touched.

Env is set before `app` is imported (config.py builds `settings` at import time),
with the same values as test_auth.py so any test file can be imported first.
"""

import os

from argon2 import PasswordHasher

TEST_EMAIL = "test-owner@example.com"
TEST_PASSWORD = "test-password"

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://finance:finance@localhost:5433/finance")
os.environ.setdefault("AUTH_EMAIL", TEST_EMAIL)
os.environ.setdefault("AUTH_PASSWORD_HASH", PasswordHasher().hash(TEST_PASSWORD))
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

import threading  # noqa: E402
import uuid  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, func, or_, select, text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from app import rate_limit, reconcile  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.session import AuthSession  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402

PREFIX = "__t_"


def _is_test_row(column):
    # autoescape: `_` is a LIKE wildcard, so a bare startswith("__t_") also matches
    # real names whose third letter is "t" (see test_categories.py).
    return column.startswith(PREFIX, autoescape=True)


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def clean_state():
    """Delete only what this test created: transactions on new `__t_` accounts or
    categories (reversals before originals, for the self-referencing FK), then the
    categories, accounts and login sessions. try/finally so a failing test still
    cleans up."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        accounts_before = set(db.scalars(select(Account.id)))
        categories_before = set(db.scalars(select(Category.id)))
        sessions_before = set(db.scalars(select(AuthSession.id)))
    try:
        yield
    finally:
        with SessionLocal() as db:
            new_accounts = [
                a.id
                for a in db.scalars(select(Account).where(_is_test_row(Account.name)))
                if a.id not in accounts_before
            ]
            new_categories = [
                c.id
                for c in db.scalars(select(Category).where(_is_test_row(Category.name)))
                if c.id not in categories_before
            ]
            if new_accounts or new_categories:
                ours = or_(
                    Transaction.account_id.in_(new_accounts),
                    Transaction.category_id.in_(new_categories),
                )
                db.execute(
                    delete(Transaction).where(ours, Transaction.reverses_transaction_id.is_not(None))
                )
                db.execute(delete(Transaction).where(ours))
            if new_categories:
                db.execute(delete(Category).where(Category.id.in_(new_categories)))
            if new_accounts:
                db.execute(delete(Account).where(Account.id.in_(new_accounts)))
            new_sessions = set(db.scalars(select(AuthSession.id))) - sessions_before
            if new_sessions:
                db.execute(delete(AuthSession).where(AuthSession.id.in_(new_sessions)))
            db.commit()


@pytest.fixture
def auth():
    """Log in once through the real app; returns (session cookie value, csrf token)."""
    login_client = TestClient(app)
    response = login_client.post(
        "/api/auth/login", json={"email": settings.auth_email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return login_client.cookies.get(SESSION_COOKIE_NAME), response.json()["csrf_token"]


def make_client(auth) -> TestClient:
    """A fresh TestClient carrying the shared session + CSRF header. One per thread
    in the concurrency tests: a TestClient is not safe to share across threads."""
    cookie, csrf = auth
    client = TestClient(app, headers={CSRF_HEADER_NAME: csrf})
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    return client


@pytest.fixture
def client(auth):
    return make_client(auth)


# --------------------------------------------------------------------------- helpers


def unique_name(label: str = "acct") -> str:
    return f"{PREFIX}{label}_{uuid.uuid4().hex[:10]}"


def make_account(client, starting: str = "100.00") -> int:
    response = client.post(
        "/api/accounts",
        json={"name": unique_name(), "type": "checking", "starting_balance": starting},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def post_tx(client, account_id: int, amount="-10.00", **overrides):
    body = {
        "account_id": account_id,
        "date": "2026-09-01",
        "amount": amount,
        "description": f"{PREFIX}tx",
    }
    body.update(overrides)
    return client.post("/api/transactions", json=body)


def posted(client, account_id: int, amount="-10.00", **overrides) -> dict:
    response = post_tx(client, account_id, amount, **overrides)
    assert response.status_code == 201, response.text
    return response.json()


def void(client, transaction_id: int):
    return client.post(f"/api/transactions/{transaction_id}/void")


def db_state(account_id: int) -> tuple[Decimal, Decimal, Decimal, int]:
    """(starting_balance, balance, SUM(amount), row count) read straight from Postgres."""
    with SessionLocal() as db:
        account = db.get(Account, account_id)
        total, count = db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0), func.count(Transaction.id))
            .where(Transaction.account_id == account_id)
        ).one()
        return account.starting_balance, account.balance, Decimal(total), count


def assert_invariant(account_id: int) -> tuple[Decimal, Decimal, Decimal, int]:
    starting, balance, total, count = db_state(account_id)
    assert balance == starting + total, (
        f"invariant broken: balance {balance} != starting {starting} + SUM {total}"
    )
    return starting, balance, total, count


def db_row(transaction_id: int) -> dict:
    with SessionLocal() as db:
        t = db.get(Transaction, transaction_id)
        return {
            "account_id": t.account_id,
            "category_id": t.category_id,
            "date": t.date.isoformat(),
            "amount": t.amount,
            "description": t.description,
            "type": t.type,
            "reverses_transaction_id": t.reverses_transaction_id,
        }


def reversals_of(transaction_id: int) -> int:
    with SessionLocal() as db:
        return db.scalar(
            select(func.count()).where(Transaction.reverses_transaction_id == transaction_id)
        )


def missing_transaction_id() -> int:
    with SessionLocal() as db:
        return (db.scalar(select(func.max(Transaction.id))) or 0) + 1000


def listed_ids(client, **params) -> list[int]:
    response = client.get("/api/transactions", params=params)
    assert response.status_code == 200, response.text
    return [t["id"] for t in response.json()]


# --------------------------------------------------------------------------- 1. create validation


@pytest.mark.parametrize(
    "description",
    # Prefixed where the value allows it, so a regression that lets one through
    # still lands on a `__t_` account the cleanup fixture removes anyway.
    [
        "",
        "   ",
        None,
        f"{PREFIX}a\x00b",
        f"{PREFIX}tab\there",
        f"{PREFIX}new\nline",
        f"{PREFIX}zero​width",
        f"{PREFIX}﻿bom",
        PREFIX + "x" * 252,  # 256 characters
    ],
)
def test_bad_description_is_422_and_nothing_posts(client, description):
    account_id = make_account(client)

    response = post_tx(client, account_id, description=description)

    assert response.status_code == 422
    assert db_state(account_id) == (Decimal("100.00"), Decimal("100.00"), 0, 0)


def test_description_is_trimmed_and_255_chars_is_accepted(client):
    account_id = make_account(client)
    long = (PREFIX + "x" * 255)[:255]

    trimmed = posted(client, account_id, description=f"  {PREFIX}coffee  ")
    at_limit = posted(client, account_id, description=long)

    assert db_row(trimmed["id"])["description"] == f"{PREFIX}coffee"  # stored trimmed
    assert db_row(at_limit["id"])["description"] == long


@pytest.mark.parametrize("amount", ["0", "0.00", "-0", "-0.00", 0])
def test_zero_amount_is_422_and_nothing_posts(client, amount):
    account_id = make_account(client)

    response = post_tx(client, account_id, amount)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list) and detail[0]["loc"][-1] == "amount", detail
    assert db_state(account_id) == (Decimal("100.00"), Decimal("100.00"), 0, 0)


@pytest.mark.parametrize(
    "extra",
    [
        {"type": "reversal"},
        {"reverses_transaction_id": 1},
        {"balance": "5.00"},
        {"categoryId": 1},  # a typo must not be silently dropped
    ],
)
def test_unknown_field_is_422_and_nothing_posts(client, extra):
    account_id = make_account(client)

    response = post_tx(client, account_id, **extra)

    assert response.status_code == 422
    assert db_state(account_id) == (Decimal("100.00"), Decimal("100.00"), 0, 0)


@pytest.mark.parametrize("amount", [12.5, -1.0, 0.1])
def test_float_amount_is_422_and_nothing_posts(client, amount):
    account_id = make_account(client)

    assert post_tx(client, account_id, amount).status_code == 422
    assert db_state(account_id) == (Decimal("100.00"), Decimal("100.00"), 0, 0)


# --------------------------------------------------------------------------- 2. void


def test_void_posts_an_exact_reversal_and_leaves_the_original_alone(client):
    account_id = make_account(client, "100.00")
    category = client.post(
        "/api/categories", json={"name": unique_name("cat"), "kind": "expense"}
    ).json()
    original = posted(
        client,
        account_id,
        "-42.17",
        date="2026-03-15",
        description=f"{PREFIX}groceries",
        category_id=category["id"],
    )
    original_row = db_row(original["id"])
    assert assert_invariant(account_id)[1] == Decimal("57.83")

    response = void(client, original["id"])

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["amount"] == "42.17"  # money leaves as a string
    assert db_row(body["id"]) == {
        "account_id": account_id,
        "category_id": category["id"],
        "date": "2026-03-15",  # the original's date, not today
        "amount": Decimal("42.17"),
        "description": f"Void: {PREFIX}groceries",
        "type": "reversal",
        "reverses_transaction_id": original["id"],
    }
    assert db_row(original["id"]) == original_row  # append-only: untouched
    starting, balance, total, count = assert_invariant(account_id)
    assert (starting, balance, total, count) == (Decimal("100.00"), Decimal("100.00"), 0, 2)


def test_void_of_money_in_takes_it_back_out(client):
    account_id = make_account(client, "0.00")
    original = posted(client, account_id, "250.00")

    body = void(client, original["id"]).json()

    assert db_row(body["id"])["amount"] == Decimal("-250.00")
    assert assert_invariant(account_id)[1] == Decimal("0.00")


def test_void_description_is_truncated_to_the_column(client):
    account_id = make_account(client)
    long = (PREFIX + "y" * 255)[:255]
    original = posted(client, account_id, description=long)

    body = void(client, original["id"]).json()

    stored = db_row(body["id"])["description"]
    assert stored == f"Void: {long}"[:255]
    assert len(stored) == 255


def test_double_void_is_409_and_only_one_reversal_exists(client):
    account_id = make_account(client)
    original = posted(client, account_id, "-10.00")
    assert void(client, original["id"]).status_code == 201
    after_first = db_state(account_id)

    response = void(client, original["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "transaction already voided"
    assert reversals_of(original["id"]) == 1
    assert db_state(account_id) == after_first
    assert_invariant(account_id)


def test_voiding_a_reversal_is_409(client):
    account_id = make_account(client)
    original = posted(client, account_id, "-10.00")
    reversal = void(client, original["id"]).json()
    before = db_state(account_id)

    response = void(client, reversal["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "transaction is a reversal"
    assert reversals_of(reversal["id"]) == 0
    assert db_state(account_id) == before


def test_void_unknown_transaction_is_404(client):
    response = void(client, missing_transaction_id())

    assert response.status_code == 404
    assert response.json()["detail"] == "transaction not found"


def test_void_on_an_archived_account_is_409_and_changes_nothing(client):
    account_id = make_account(client, "40.00")
    original = posted(client, account_id, "-5.00")
    assert client.patch(f"/api/accounts/{account_id}", json={"is_archived": True}).status_code == 200
    before = db_state(account_id)
    assert before == (Decimal("40.00"), Decimal("35.00"), Decimal("-5.00"), 1)

    response = void(client, original["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "account is archived"
    assert db_state(account_id) == before  # no reversal row, balance untouched
    assert reversals_of(original["id"]) == 0


def test_void_still_works_when_the_category_is_archived(client):
    """An archived category refuses new transactions (S3), but a void undoes an
    old one: history is history. The reversal keeps the (archived) category."""
    account_id = make_account(client, "20.00")
    category = client.post(
        "/api/categories", json={"name": unique_name("cat"), "kind": "expense"}
    ).json()
    original = posted(client, account_id, "-7.50", category_id=category["id"])
    assert client.patch(
        f"/api/categories/{category['id']}", json={"is_archived": True}
    ).status_code == 200

    response = void(client, original["id"])

    assert response.status_code == 201, response.text
    assert db_row(response.json()["id"])["category_id"] == category["id"]
    assert assert_invariant(account_id)[1] == Decimal("20.00")


def test_void_that_would_overflow_the_balance_is_422_and_changes_nothing(client):
    account_id = make_account(client, "-999999999999.00")
    small_in = posted(client, account_id, "1.00")
    posted(client, account_id, "-1.99")  # balance now -999999999999.99
    before = db_state(account_id)

    # Voiding the +1.00 would take the balance to -1000000000000.99: past NUMERIC(14,2).
    response = void(client, small_in["id"])

    assert response.status_code == 422
    assert db_state(account_id) == before
    assert reversals_of(small_in["id"]) == 0


def test_void_requires_a_session():
    response = TestClient(app).post(f"/api/transactions/{missing_transaction_id()}/void")
    assert response.status_code == 401


def test_void_without_csrf_token_is_403_and_changes_nothing(client):
    account_id = make_account(client)
    original = posted(client, account_id, "-10.00")
    before = db_state(account_id)
    del client.headers[CSRF_HEADER_NAME]

    assert void(client, original["id"]).status_code == 403
    assert db_state(account_id) == before
    assert reversals_of(original["id"]) == 0


def test_no_edit_or_delete_endpoint(client):
    account_id = make_account(client)
    original = posted(client, account_id)

    for method in ("put", "patch", "delete"):
        response = getattr(client, method)(f"/api/transactions/{original['id']}")
        # 404: no route exists at /{id} for any method (only /{id}/void does).
        assert response.status_code in (404, 405), (method, response.status_code)
    assert db_row(original["id"])["amount"] == Decimal("-10.00")


# --------------------------------------------------------------------------- 3. list filters


@pytest.fixture
def dated(client):
    """Two accounts; rows either side of both January boundaries and December's."""
    a = make_account(client)
    b = make_account(client)
    rows = {
        name: posted(client, acct, "-1.00", date=day)["id"]
        for name, acct, day in [
            ("a_dec31", a, "2025-12-31"),
            ("a_jan01", a, "2026-01-01"),
            ("a_jan31", a, "2026-01-31"),
            ("a_feb01", a, "2026-02-01"),
            ("b_jan15", b, "2026-01-15"),
            ("a_dec2026", a, "2026-12-31"),
            ("a_jan2027", a, "2027-01-01"),
        ]
    }
    return a, b, rows


def test_month_filter_includes_first_and_last_day_only(client, dated):
    a, _, rows = dated

    assert listed_ids(client, month="2026-01", account_id=a) == [rows["a_jan31"], rows["a_jan01"]]
    assert listed_ids(client, month="2026-02", account_id=a) == [rows["a_feb01"]]
    assert listed_ids(client, month="2025-12", account_id=a) == [rows["a_dec31"]]
    assert listed_ids(client, month="2026-12", account_id=a) == [rows["a_dec2026"]]


def test_month_filter_alone_spans_accounts(client, dated):
    _, _, rows = dated

    ids = set(listed_ids(client, month="2026-01"))

    assert {rows["a_jan01"], rows["a_jan31"], rows["b_jan15"]} <= ids
    assert not ids & {rows["a_dec31"], rows["a_feb01"], rows["a_jan2027"]}


def test_account_filter_alone(client, dated):
    a, b, rows = dated

    assert listed_ids(client, account_id=b) == [rows["b_jan15"]]
    assert set(listed_ids(client, account_id=a)) == set(rows.values()) - {rows["b_jan15"]}


def test_combined_filters_and(client, dated):
    _, b, rows = dated

    assert listed_ids(client, month="2026-01", account_id=b) == [rows["b_jan15"]]
    assert listed_ids(client, month="2026-02", account_id=b) == []


def test_order_is_newest_date_then_newest_id(client):
    a = make_account(client)
    older = posted(client, a, date="2026-05-01")["id"]
    first = posted(client, a, date="2026-05-02")["id"]
    second = posted(client, a, date="2026-05-02")["id"]

    assert listed_ids(client, account_id=a) == [second, first, older]


@pytest.mark.parametrize(
    "month",
    ["2026-13", "2026-00", "2026-1", "26-01", "2026-01-01", "2026/01", "abcd-ef",
     "0000-01", "٢٠٢٦-01", " 2026-01", ""],
)
def test_bad_month_is_422(client, month):
    assert client.get("/api/transactions", params={"month": month}).status_code == 422


# --------------------------------------------------------------------------- 4. DB rules (0004)


def test_database_refuses_a_second_reversal_and_a_broken_link(client):
    """Migration 0004's index and CHECK, hit directly (bypassing the API), so a
    future writer that skips the router still can't break them."""
    account_id = make_account(client)
    original = posted(client, account_id)
    assert void(client, original["id"]).status_code == 201

    cases = [
        (
            "uq_transaction_one_reversal",
            "INSERT INTO transactions (account_id, date, amount, description, type,"
            " reverses_transaction_id) VALUES (:a, '2026-09-01', 10, 'x', 'reversal', :r)",
        ),
        (
            "ck_transaction_reversal_link",
            "INSERT INTO transactions (account_id, date, amount, description, type)"
            " VALUES (:a, '2026-09-01', 10, 'x', 'reversal')",
        ),
        (
            "ck_transaction_reversal_link",
            "INSERT INTO transactions (account_id, date, amount, description, type,"
            " reverses_transaction_id) VALUES (:a, '2026-09-01', 10, 'x', 'normal', :r)",
        ),
    ]
    with SessionLocal() as db:
        for constraint, sql in cases:
            with pytest.raises(IntegrityError) as excinfo:
                db.execute(text(sql), {"a": account_id, "r": original["id"]})
            assert excinfo.value.orig.diag.constraint_name == constraint
            db.rollback()
    assert db_state(account_id)[3] == 2  # still just the original and its one reversal


# --------------------------------------------------------------------------- 5. reconciliation


def test_reconcile_finds_no_drift_after_voids(client):
    account_id = make_account(client, "500.00")
    ids = [posted(client, account_id, amount)["id"] for amount in ("-12.34", "100.00", "-0.01")]
    for tx_id in ids[:2]:
        assert void(client, tx_id).status_code == 201

    with SessionLocal() as db:
        _, drifted = reconcile.find_drift(db)
    assert [d for d in drifted if d[0] == account_id] == []
    # main()'s exit code covers every account; only meaningful if nothing else drifts.
    if not drifted:
        assert reconcile.main() == 0
    assert assert_invariant(account_id)[1] == Decimal("499.99")


# --------------------------------------------------------------------------- 6. concurrency


ROUNDS = 20


def run_together(auth, jobs) -> list:
    """Run each job(client) on its own thread with its own TestClient, released
    together by a barrier. Returns each job's status code (or the exception)."""
    barrier = threading.Barrier(len(jobs))
    results: list = [None] * len(jobs)

    def worker(index, job):
        try:
            client = make_client(auth)
            barrier.wait(timeout=30)
            results[index] = job(client).status_code
        except Exception as exc:  # surfaced by the caller's asserts, not swallowed
            results[index] = exc

    threads = [threading.Thread(target=worker, args=(i, j)) for i, j in enumerate(jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    assert not any(t.is_alive() for t in threads), "a request hung"
    return results


def test_two_simultaneous_voids_of_one_row_yield_one_reversal(auth):
    """Both voids can pass the already-voided pre-check at once only if they aren't
    serialised; the account lock queues them, and migration 0004's index backs it
    up. Either way: exactly one 201, one 409, one reversal, invariant intact."""
    setup = make_client(auth)
    account_id = make_account(setup, "1000.00")

    for round_no in range(ROUNDS):
        original = posted(setup, account_id, f"-{round_no + 1}.25")

        results = run_together(auth, [lambda c: void(c, original["id"])] * 2)

        assert sorted(results, key=str) == [201, 409], (round_no, results)
        assert reversals_of(original["id"]) == 1, round_no
        assert assert_invariant(account_id)[1] == Decimal("1000.00"), round_no


def test_void_racing_new_posts_on_the_same_account_keeps_the_invariant(auth):
    """A void and several posts to ONE account at once. Every writer of `balance`
    takes the account row lock; without it on the void, its stale read-modify-write
    overwrites a post's balance change and the invariant breaks."""
    setup = make_client(auth)
    account_id = make_account(setup, "0.00")
    posters = 5
    expected = Decimal("0.00")

    for round_no in range(ROUNDS):
        original = posted(setup, account_id, "-3.00")
        expected -= Decimal("3.00")
        amounts = [Decimal(f"{i + 1}.{round_no:02d}") for i in range(posters)]
        jobs = [lambda c: void(c, original["id"])] + [
            (lambda c, a=a: post_tx(c, account_id, str(a))) for a in amounts
        ]

        results = run_together(auth, jobs)

        assert results == [201] + [201] * posters, (round_no, results)
        expected += Decimal("3.00") + sum(amounts)
        starting, balance, total, _ = assert_invariant(account_id)
        assert total == expected, round_no
