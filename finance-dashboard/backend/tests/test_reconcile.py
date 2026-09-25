"""Reconciliation job (app/reconcile.py) against ADR-0005's invariant.

    balance == starting_balance + SUM(transactions.amount)

Integration tests like test_accounts.py: accounts and transactions are made through
the real app over TestClient against a real, migrated Postgres (the Compose db on
host port 5433 by default). Drift is manufactured the only way it can happen in
practice, by writing `accounts.balance` directly in SQL behind the API's back.

Every account made here is named `__t_<...>`; the autouse fixture deletes exactly
the transactions, accounts and login sessions that appeared during the test, so
the dev database is never left dirty and nothing that existed before is touched.
Other (real) accounts may exist, so drift assertions filter find_drift's output by
the test's own account ids; main()'s exit code is asserted on the assumption that
every pre-existing account is clean (checked up front by `pre_existing_clean`).

The "no accounts" and "DB unreachable" paths are driven by monkeypatching, never by
deleting real rows.

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

import logging  # noqa: E402
import uuid  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, func, select, update  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from app import rate_limit, reconcile  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.session import AuthSession  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402

PREFIX = "__t_"


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def clean_state():
    """Delete only what this test created: new `__t_` accounts (their transactions
    first, for the FK), and new login sessions. try/finally so a failing test, or a
    failure in one cleanup step, still cleans up."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        accounts_before = set(db.scalars(select(Account.id)))
        sessions_before = set(db.scalars(select(AuthSession.id)))
    try:
        yield
    finally:
        with SessionLocal() as db:
            new_accounts = [
                a.id
                for a in db.scalars(select(Account).where(Account.name.startswith(PREFIX)))
                if a.id not in accounts_before
            ]
            if new_accounts:
                db.execute(delete(Transaction).where(Transaction.account_id.in_(new_accounts)))
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


@pytest.fixture
def client(auth):
    cookie, csrf = auth
    client = TestClient(app, headers={CSRF_HEADER_NAME: csrf})
    client.cookies.set(SESSION_COOKIE_NAME, cookie)
    return client


@pytest.fixture
def pre_existing_clean():
    """main()'s exit code covers every account, not just ours. Asserting 0 or 1 from
    it is only meaningful if nothing that existed before this test already drifts;
    fail loudly (rather than mis-attribute) if the dev DB itself is dirty."""
    with SessionLocal() as db:
        _, drifted = reconcile.find_drift(db)
    foreign = [d for d in drifted if not d[1].startswith(PREFIX)]
    assert foreign == [], f"dev DB already drifts outside this test: {foreign}"


@pytest.fixture
def reconcile_log(caplog):
    caplog.set_level(logging.INFO, logger="reconcile")
    return caplog


# --------------------------------------------------------------------------- helpers


def unique_name(label: str = "acct") -> str:
    return f"{PREFIX}{label}_{uuid.uuid4().hex[:10]}"


def create_account(client, **body):
    body.setdefault("name", unique_name())
    return client.post("/api/accounts", json=body)


def post_tx(client, account_id: int, amount: str):
    return client.post(
        "/api/transactions",
        json={
            "account_id": account_id,
            "date": "2026-09-01",
            "amount": amount,
            "description": f"{PREFIX}tx",
        },
    )


def db_state(account_id: int) -> tuple[Decimal, Decimal, Decimal, int]:
    """(starting_balance, balance, SUM(amount), row count) read straight from Postgres."""
    with SessionLocal() as db:
        account = db.get(Account, account_id)
        total, count = db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0), func.count(Transaction.id))
            .where(Transaction.account_id == account_id)
        ).one()
        return account.starting_balance, account.balance, Decimal(total), count


def make_account(client, starting: str, amounts: list[str], archive: bool = False) -> dict:
    """Create a `__t_` account via the API, post `amounts`, optionally archive it
    (after posting: archived accounts refuse new transactions)."""
    response = create_account(client, type="checking", starting_balance=starting)
    assert response.status_code == 201, response.text
    account = response.json()
    for amount in amounts:
        assert post_tx(client, account["id"], amount).status_code == 201
    if archive:
        response = client.patch(f"/api/accounts/{account['id']}", json={"is_archived": True})
        assert response.status_code == 200, response.text
    return account


def corrupt_balance(account_id: int, balance: str) -> None:
    """Write `balance` behind the API's back: the only way drift can appear."""
    with SessionLocal() as db:
        db.execute(update(Account).where(Account.id == account_id).values(balance=Decimal(balance)))
        db.commit()


def drift_for(ids) -> dict[int, tuple[str, Decimal, Decimal]]:
    """find_drift restricted to `ids`: {id: (name, stored, expected)}."""
    ids = set(ids)
    with SessionLocal() as db:
        _, drifted = reconcile.find_drift(db)
    return {i: (n, s, e) for i, n, s, e in drifted if i in ids}


def account_count() -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Account))


def drift_warnings(caplog) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == "reconcile" and r.levelno == logging.WARNING
        and r.getMessage().startswith("DRIFT ")
    ]


# --------------------------------------------------------------------------- 1. clean run


def test_clean_accounts_report_ok(client, pre_existing_clean, reconcile_log):
    with_tx = make_account(client, "100.00", ["-25.50", "10.25", "0.01"])
    no_tx = make_account(client, "42.00", [])  # LEFT JOIN + COALESCE: sums to 0, not NULL
    negative = make_account(client, "-50.25", ["-1.00"])
    ids = [with_tx["id"], no_tx["id"], negative["id"]]
    assert db_state(with_tx["id"])[1] == Decimal("84.76")

    with SessionLocal() as db:
        checked, drifted = reconcile.find_drift(db)
    assert checked == account_count()
    assert [d for d in drifted if d[0] in ids] == []

    assert reconcile.main() == 0
    assert drift_warnings(reconcile_log) == []
    ok = [r for r in reconcile_log.records if r.name == "reconcile" and r.levelno == logging.INFO]
    assert [r.getMessage() for r in ok] == [f"ok: {checked} accounts match the ledger"]


# --------------------------------------------------------------------------- 2. drift


def test_drift_both_directions_zero_tx_and_archived(client, pre_existing_clean, reconcile_log):
    too_high = make_account(client, "100.00", ["-30.00", "5.00"])  # true balance 75.00
    too_low = make_account(client, "0.00", ["19.99"])  # true balance 19.99
    zero_tx = make_account(client, "500.00", [])  # true balance 500.00, no ledger rows
    archived = make_account(client, "10.00", ["-2.50"], archive=True)  # true balance 7.50
    untouched = make_account(client, "1.00", ["1.00"])  # stays clean

    corrupt_balance(too_high["id"], "75.01")
    corrupt_balance(too_low["id"], "-19.99")
    corrupt_balance(zero_tx["id"], "0.00")  # balance != starting_balance, SUM is 0
    corrupt_balance(archived["id"], "7.00")

    expected = {
        too_high["id"]: (too_high["name"], Decimal("75.01"), Decimal("75.00")),
        too_low["id"]: (too_low["name"], Decimal("-19.99"), Decimal("19.99")),
        zero_tx["id"]: (zero_tx["name"], Decimal("0.00"), Decimal("500.00")),
        archived["id"]: (archived["name"], Decimal("7.00"), Decimal("7.50")),
    }
    ours = list(expected) + [untouched["id"]]
    assert drift_for(ours) == expected  # untouched is absent

    before = {i: db_state(i) for i in ours}

    assert reconcile.main() == 1

    warnings = drift_warnings(reconcile_log)
    assert len(warnings) == len(expected)  # dev DB pre-checked clean: only ours drift
    for account_id, (name, stored, exp) in expected.items():
        line = (
            f"DRIFT account id={account_id} name={name!r} "
            f"stored={stored} expected={exp} diff={stored - exp}"
        )
        assert line in warnings, (line, warnings)
    assert not any(f"id={untouched['id']} " in w for w in warnings)
    errors = [r.getMessage() for r in reconcile_log.records
              if r.name == "reconcile" and r.levelno == logging.ERROR]
    assert errors == [f"4 of {account_count()} accounts drifted"]

    # 4. read-only: reconcile reported the drift and repaired nothing.
    assert {i: db_state(i) for i in ours} == before
    assert db_state(too_high["id"])[1] == Decimal("75.01")
    assert db_state(zero_tx["id"])[1] == Decimal("0.00")


def test_single_cent_drift_is_caught(client, pre_existing_clean, reconcile_log):
    account = make_account(client, "0.00", ["0.10", "0.20"])  # 0.30 exactly, no float
    corrupt_balance(account["id"], "0.31")

    assert drift_for([account["id"]]) == {
        account["id"]: (account["name"], Decimal("0.31"), Decimal("0.30"))
    }
    assert reconcile.main() == 1
    assert any(f"id={account['id']} " in w for w in drift_warnings(reconcile_log))


def test_drift_fixed_by_hand_goes_back_to_ok(client, pre_existing_clean, reconcile_log):
    account = make_account(client, "20.00", ["-5.00"])
    corrupt_balance(account["id"], "99.00")
    assert reconcile.main() == 1

    corrupt_balance(account["id"], "15.00")  # the human repair
    reconcile_log.clear()
    assert reconcile.main() == 0
    assert drift_warnings(reconcile_log) == []


# --------------------------------------------------------------------------- 3. could not run


def test_zero_accounts_is_2_not_ok(monkeypatch, reconcile_log):
    """An empty result means the wrong database, never "all clear". Driven by
    monkeypatch: real rows are never deleted to get here."""
    monkeypatch.setattr(reconcile, "find_drift", lambda db: (0, []))

    assert reconcile.main() == 2
    messages = [(r.levelno, r.getMessage()) for r in reconcile_log.records if r.name == "reconcile"]
    assert (
        logging.ERROR,
        "no accounts found: wrong or empty database? refusing to report ok",
    ) in messages
    assert not any(m.startswith("ok:") for _, m in messages)


def test_database_unreachable_is_2(monkeypatch, reconcile_log):
    def unreachable():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(reconcile, "SessionLocal", unreachable)

    assert reconcile.main() == 2
    failures = [r for r in reconcile_log.records
                if r.name == "reconcile" and r.getMessage() == "reconcile could not run"]
    assert len(failures) == 1
    assert failures[0].levelno == logging.ERROR
    assert failures[0].exc_info is not None  # log.exception keeps the traceback


def test_query_failure_is_2(monkeypatch, reconcile_log):
    def broken(db):
        raise OperationalError("SELECT ...", {}, Exception("server closed the connection"))

    monkeypatch.setattr(reconcile, "find_drift", broken)

    assert reconcile.main() == 2
    assert any(r.getMessage() == "reconcile could not run" for r in reconcile_log.records)
