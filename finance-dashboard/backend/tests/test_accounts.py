"""Accounts API through the real app, checked against ADR-0005's invariant.

    balance == starting_balance + SUM(transactions.amount)

Integration tests like test_auth.py: `app.main.app` over TestClient against a real,
migrated Postgres (the Compose db on host port 5433 by default). Balances are
verified by effect (a direct SQL read of the account row and its ledger sum), not
only by the HTTP status or the response body.

Every account made here is named `__t_<...>`; the autouse fixture deletes exactly
the transactions, accounts and login sessions that appeared during the test, so
the dev database is never left dirty and nothing that existed before is touched.

Env is set before `app` is imported (config.py builds `settings` at import time),
with the same values as test_auth.py so either file can be imported first.
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
from sqlalchemy import delete, func, select  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import ACCOUNT_TYPES, Account  # noqa: E402
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


def make_client(auth) -> TestClient:
    """A fresh TestClient carrying the shared session + CSRF header. One per thread
    in the concurrency test: a TestClient is not safe to share across threads."""
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


def assert_invariant(account_id: int) -> tuple[Decimal, Decimal, Decimal, int]:
    starting, balance, total, count = db_state(account_id)
    assert balance == starting + total, (
        f"invariant broken: balance {balance} != starting {starting} + SUM {total}"
    )
    return starting, balance, total, count


# --------------------------------------------------------------------------- 1. create


def test_create_sets_balance_to_starting_balance(client):
    response = create_account(client, type="savings", starting_balance="1234.50")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["type"] == "savings"
    assert body["starting_balance"] == "1234.50"  # money leaves as a string
    assert body["balance"] == "1234.50"
    assert body["is_archived"] is False
    starting, balance, total, count = assert_invariant(body["id"])
    assert (starting, balance, total, count) == (Decimal("1234.50"), Decimal("1234.50"), 0, 0)


def test_create_defaults_starting_balance_to_zero(client):
    response = create_account(client, type="checking")

    assert response.status_code == 201, response.text
    assert response.json()["starting_balance"] == response.json()["balance"] == "0.00"


def test_create_accepts_negative_starting_balance(client):
    # A credit card can open in debt; signed money is allowed on purpose.
    response = create_account(client, type="credit_card", starting_balance="-50.25")

    assert response.status_code == 201, response.text
    assert response.json()["balance"] == "-50.25"
    assert_invariant(response.json()["id"])


@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
def test_every_valid_type_is_accepted(client, account_type):
    response = create_account(client, type=account_type)

    assert response.status_code == 201, response.text
    assert response.json()["type"] == account_type


@pytest.mark.parametrize("bad_type", ["brokerage", "Checking", "", None])
def test_invalid_type_is_422(client, bad_type):
    name = unique_name()
    response = create_account(client, name=name, type=bad_type)

    assert response.status_code == 422
    assert_no_account_named(name)


def test_missing_type_is_422(client):
    name = unique_name()
    assert client.post("/api/accounts", json={"name": name}).status_code == 422
    assert_no_account_named(name)


def assert_no_account_named(name: str) -> None:
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).where(Account.name == name)) == 0


# --------------------------------------------------------------------------- 2. duplicate name


def test_duplicate_name_is_409_and_only_one_row_exists(client):
    name = unique_name("dup")
    assert create_account(client, name=name, type="cash").status_code == 201

    response = create_account(client, name=name, type="checking")

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).where(Account.name == name)) == 1


def test_rename_onto_an_existing_name_is_409_and_nothing_changes(client):
    taken = unique_name("taken")
    assert create_account(client, name=taken, type="cash").status_code == 201
    other = create_account(client, type="cash").json()

    response = client.patch(f"/api/accounts/{other['id']}", json={"name": taken})

    assert response.status_code == 409
    with SessionLocal() as db:
        assert db.get(Account, other["id"]).name == other["name"]


# --------------------------------------------------------------------------- 3. money input rules


@pytest.mark.parametrize(
    "starting_balance",
    [
        "1234567890123.00",  # 13 integer digits: past NUMERIC(14,2)
        "9999999999999",
        10**13,  # 14-digit JSON integer: must be 422, not a NUMERIC(14,2) overflow 500
        "1.005",  # 3 decimals: must be refused, not silently rounded
        1.5,  # a JSON float
        1.005,
        "1e3",
        "NaN",
        "abc",
    ],
)
def test_bad_starting_balance_is_422(client, starting_balance):
    name = unique_name()
    response = create_account(client, name=name, type="cash", starting_balance=starting_balance)

    assert response.status_code == 422
    assert_no_account_named(name)


def test_largest_valid_starting_balance_is_accepted(client):
    response = create_account(client, type="cash", starting_balance="999999999999.99")

    assert response.status_code == 201, response.text
    assert response.json()["balance"] == "999999999999.99"


def test_client_cannot_set_balance_on_create(client):
    name = unique_name()
    response = create_account(
        client, name=name, type="cash", starting_balance="10.00", balance="1000000.00"
    )

    assert response.status_code == 422
    assert_no_account_named(name)


def test_client_cannot_set_balance_on_patch(client):
    account = create_account(client, type="cash", starting_balance="10.00").json()

    response = client.patch(f"/api/accounts/{account['id']}", json={"balance": "999.00"})

    assert response.status_code == 422
    assert db_state(account["id"])[1] == Decimal("10.00")


@pytest.mark.parametrize("amount", ["1.005", 1.5, "1234567890123.00"])
def test_bad_transaction_amount_is_422_and_nothing_posts(client, amount):
    account = create_account(client, type="cash", starting_balance="10.00").json()

    response = post_tx(client, account["id"], amount)

    assert response.status_code == 422
    assert db_state(account["id"]) == (Decimal("10.00"), Decimal("10.00"), 0, 0)


@pytest.mark.parametrize("amount", [10**12, 10**13, -(10**13), 99999999999999])
def test_13_to_14_digit_json_integer_amount_is_422_and_nothing_posts(client, amount):
    """A bare JSON integer skips the string regex; Money must still cap it at 12
    integer digits so it is a 422, never a NUMERIC(14,2) overflow at the insert.

    The router's DataError backstop also answers 422 (with a string `detail`), so
    the list-shaped `detail` is what proves the schema, not the database, refused it."""
    account = create_account(client, type="cash", starting_balance="10.00").json()

    response = post_tx(client, account["id"], amount)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list) and detail[0]["loc"][-1] == "amount", detail
    assert db_state(account["id"]) == (Decimal("10.00"), Decimal("10.00"), 0, 0)


# --------------------------------------------------------------------------- 4. PATCH edit


def test_patch_changes_name_and_type(client):
    account = create_account(client, type="checking", starting_balance="5.00").json()
    new_name = unique_name("renamed")

    response = client.patch(
        f"/api/accounts/{account['id']}", json={"name": new_name, "type": "savings"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == new_name
    assert response.json()["type"] == "savings"
    assert response.json()["balance"] == "5.00"  # untouched by a non-money edit
    with SessionLocal() as db:
        row = db.get(Account, account["id"])
        assert (row.name, row.type, row.balance) == (new_name, "savings", Decimal("5.00"))


def test_patch_starting_balance_moves_balance_by_the_delta(client):
    account = create_account(client, type="checking", starting_balance="100.00").json()
    assert post_tx(client, account["id"], "-25.50").status_code == 201
    assert post_tx(client, account["id"], "10.25").status_code == 201
    assert assert_invariant(account["id"])[1] == Decimal("84.75")

    response = client.patch(f"/api/accounts/{account['id']}", json={"starting_balance": "150.00"})

    assert response.status_code == 200, response.text
    assert response.json()["starting_balance"] == "150.00"
    assert response.json()["balance"] == "134.75"  # moved by exactly +50.00
    starting, balance, total, count = assert_invariant(account["id"])
    assert (starting, balance, total, count) == (
        Decimal("150.00"),
        Decimal("134.75"),
        Decimal("-15.25"),
        2,
    )

    # And back down, below zero: the delta is signed.
    response = client.patch(f"/api/accounts/{account['id']}", json={"starting_balance": "-20"})
    assert response.status_code == 200, response.text
    assert response.json()["balance"] == "-35.25"
    assert assert_invariant(account["id"])[1] == Decimal("-35.25")


def test_patch_same_starting_balance_is_a_no_op(client):
    account = create_account(client, type="cash", starting_balance="7.00").json()
    assert post_tx(client, account["id"], "3.00").status_code == 201

    response = client.patch(f"/api/accounts/{account['id']}", json={"starting_balance": "7"})

    assert response.status_code == 200
    assert response.json()["balance"] == "10.00"
    assert_invariant(account["id"])


def test_patch_starting_balance_overflow_is_422_and_nothing_changes(client):
    account = create_account(client, type="cash", starting_balance="0.00").json()
    assert post_tx(client, account["id"], "999999999999.00").status_code == 201

    # starting_balance itself is valid, but balance + delta would overflow NUMERIC(14,2).
    response = client.patch(
        f"/api/accounts/{account['id']}", json={"starting_balance": "1000.00"}
    )

    assert response.status_code == 422
    assert db_state(account["id"])[:2] == (Decimal("0.00"), Decimal("999999999999.00"))
    assert_invariant(account["id"])


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": None},
        {"type": None},
        {"starting_balance": None},
        {"is_archived": None},
        {"name": "  "},
        {"is_archived": "yes"},
        {"starting_balance": 2.5},
    ],
)
def test_patch_rejects_empty_and_null_bodies(client, body):
    account = create_account(client, type="cash", starting_balance="1.00").json()

    response = client.patch(f"/api/accounts/{account['id']}", json=body)

    assert response.status_code == 422
    with SessionLocal() as db:
        row = db.get(Account, account["id"])
        assert (row.name, row.type, row.starting_balance, row.balance, row.is_archived) == (
            account["name"],
            "cash",
            Decimal("1.00"),
            Decimal("1.00"),
            False,
        )


def test_patch_unknown_account_is_404(client):
    with SessionLocal() as db:
        missing = (db.scalar(select(func.max(Account.id))) or 0) + 1000
    assert client.patch(f"/api/accounts/{missing}", json={"type": "cash"}).status_code == 404


# --------------------------------------------------------------------------- 5. archive


def test_archive_hides_from_default_list_and_unarchive_restores(client):
    account = create_account(client, type="cash").json()

    response = client.patch(f"/api/accounts/{account['id']}", json={"is_archived": True})
    assert response.status_code == 200, response.text
    assert response.json()["is_archived"] is True

    default_ids = {a["id"] for a in client.get("/api/accounts").json()}
    all_ids = {a["id"] for a in client.get("/api/accounts?include_archived=true").json()}
    assert account["id"] not in default_ids
    assert account["id"] in all_ids

    response = client.patch(f"/api/accounts/{account['id']}", json={"is_archived": False})
    assert response.status_code == 200
    assert response.json()["is_archived"] is False
    assert account["id"] in {a["id"] for a in client.get("/api/accounts").json()}


# --------------------------------------------------------------------------- 6. archived blocks posting


def test_posting_to_an_archived_account_is_409_and_changes_nothing(client):
    account = create_account(client, type="checking", starting_balance="40.00").json()
    assert post_tx(client, account["id"], "-5.00").status_code == 201
    assert client.patch(f"/api/accounts/{account['id']}", json={"is_archived": True}).status_code == 200
    before = db_state(account["id"])
    assert before == (Decimal("40.00"), Decimal("35.00"), Decimal("-5.00"), 1)

    response = post_tx(client, account["id"], "-12.34")

    assert response.status_code == 409
    assert db_state(account["id"]) == before  # no row inserted, balance unchanged
    assert_invariant(account["id"])

    # Unarchiving reopens it.
    assert client.patch(f"/api/accounts/{account['id']}", json={"is_archived": False}).status_code == 200
    assert post_tx(client, account["id"], "-12.34").status_code == 201
    assert db_state(account["id"]) == (Decimal("40.00"), Decimal("22.66"), Decimal("-17.34"), 2)


# --------------------------------------------------------------------------- 7. concurrency


POSTERS = 20
ROUNDS = 3


def test_concurrent_posts_and_edits_keep_the_invariant(auth):
    """20 transaction posts plus 2 starting-balance edits to ONE account, released
    together by a barrier, for several rounds. With the FOR UPDATE row locks every
    writer queues and the invariant holds exactly; without them concurrent
    `balance += amount` writes overwrite each other and the balance comes up short.

    Each thread gets its own TestClient (sharing one across threads is unsafe) but
    the same logged-in session, so there is one login, not 22 (the rate limiter
    counts every login)."""
    setup_client = make_client(auth)
    account = create_account(setup_client, type="checking", starting_balance="0.00").json()
    account_id = account["id"]

    expected_sum = Decimal("0.00")
    for round_no in range(ROUNDS):
        amounts = [Decimal(f"{i + 1}.{round_no:02d}") for i in range(POSTERS)]
        edits = [Decimal(f"{100 * (round_no + 1)}.00"), Decimal(f"-{7 * (round_no + 1)}.50")]
        jobs = [("post", str(a)) for a in amounts] + [("patch", str(e)) for e in edits]
        barrier = threading.Barrier(len(jobs))
        results: list = [None] * len(jobs)

        def worker(index: int, kind: str, value: str) -> None:
            try:
                client = make_client(auth)
                barrier.wait(timeout=30)
                if kind == "post":
                    results[index] = post_tx(client, account_id, value).status_code
                else:
                    results[index] = client.patch(
                        f"/api/accounts/{account_id}", json={"starting_balance": value}
                    ).status_code
            except Exception as exc:  # surfaced below, not swallowed
                results[index] = exc

        threads = [
            threading.Thread(target=worker, args=(i, kind, value))
            for i, (kind, value) in enumerate(jobs)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        assert not any(t.is_alive() for t in threads), "a request hung"

        assert results == [201] * POSTERS + [200] * len(edits), results
        expected_sum += sum(amounts)

        starting, balance, total, count = assert_invariant(account_id)
        assert count == POSTERS * (round_no + 1)
        assert total == expected_sum
        assert starting in edits  # whichever edit landed last
