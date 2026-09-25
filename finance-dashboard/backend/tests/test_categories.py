"""Categories API (S3) through the real app, against a real migrated Postgres.

Same setup as test_accounts.py: `app.main.app` over TestClient, the Compose db on
host port 5433 by default, results verified by a direct read of the rows as well as
by the HTTP response.

Every category and account made here is named `__t_<...>`; the autouse fixture
deletes exactly the transactions, categories, accounts and login sessions that
appeared during the test. The ~15 seeded categories are never written to, and one
test checks that they come through a full create/rename/archive run unchanged.

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
from sqlalchemy import delete, func, or_, select, text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.category import CATEGORY_KINDS, Category  # noqa: E402
from app.models.session import AuthSession  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402

PREFIX = "__t_"


def _is_test_row(column):
    # autoescape: `_` is a LIKE wildcard, so a bare startswith("__t_") also matches
    # seeded names like "Entertainment" (any name whose third letter is "t").
    return column.startswith(PREFIX, autoescape=True)


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def clean_state():
    """Delete only what this test created: new `__t_` categories and accounts (the
    transactions that reference either go first, for the FKs), and new login
    sessions. try/finally so a failing test still cleans up."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        categories_before = set(db.scalars(select(Category.id)))
        accounts_before = set(db.scalars(select(Account.id)))
        sessions_before = set(db.scalars(select(AuthSession.id)))
    try:
        yield
    finally:
        with SessionLocal() as db:
            new_categories = [
                c.id
                for c in db.scalars(select(Category).where(_is_test_row(Category.name)))
                if c.id not in categories_before
            ]
            new_accounts = [
                a.id
                for a in db.scalars(select(Account).where(_is_test_row(Account.name)))
                if a.id not in accounts_before
            ]
            if new_categories or new_accounts:
                db.execute(
                    delete(Transaction).where(
                        or_(
                            Transaction.account_id.in_(new_accounts),
                            Transaction.category_id.in_(new_categories),
                        )
                    )
                )
            if new_categories:
                db.execute(delete(Category).where(Category.id.in_(new_categories)))
            if new_accounts:
                db.execute(delete(Account).where(Account.id.in_(new_accounts)))
            new_sessions = set(db.scalars(select(AuthSession.id))) - sessions_before
            if new_sessions:
                db.execute(delete(AuthSession).where(AuthSession.id.in_(new_sessions)))
            db.commit()


@pytest.fixture
def client():
    """Logged in through the real app, CSRF header set on every request."""
    c = TestClient(app)
    response = c.post(
        "/api/auth/login", json={"email": settings.auth_email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    c.headers[CSRF_HEADER_NAME] = response.json()["csrf_token"]
    return c


# --------------------------------------------------------------------------- helpers


def unique_name(label: str = "cat") -> str:
    return f"{PREFIX}{label}_{uuid.uuid4().hex[:10]}"


def create_category(client, **body):
    body.setdefault("name", unique_name())
    body.setdefault("kind", "expense")
    return client.post("/api/categories", json=body)


def db_row(category_id: int) -> tuple[str, str, bool]:
    with SessionLocal() as db:
        row = db.get(Category, category_id)
        return row.name, row.kind, row.is_archived


def count_named(name: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).where(Category.name == name))


def seeded_snapshot() -> list[tuple]:
    """Every category that isn't a test row, as it sits in the database."""
    with SessionLocal() as db:
        return [
            (c.id, c.name, c.kind, c.is_archived, c.created_at)
            for c in db.scalars(
                select(Category).where(~_is_test_row(Category.name)).order_by(Category.id)
            )
        ]


def make_account(client) -> int:
    response = client.post("/api/accounts", json={"name": unique_name("acct"), "type": "cash"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def post_tx(client, account_id: int, category_id: int | None, amount: str = "-5.00"):
    return client.post(
        "/api/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "date": "2026-09-01",
            "amount": amount,
            "description": f"{PREFIX}tx",
        },
    )


def tx_count(account_id: int) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).where(Transaction.account_id == account_id))


def missing_category_id() -> int:
    with SessionLocal() as db:
        return (db.scalar(select(func.max(Category.id))) or 0) + 1000


# --------------------------------------------------------------------------- 1. auth


def test_list_without_a_session_is_401():
    assert TestClient(app).get("/api/categories").status_code == 401


def test_writes_without_csrf_token_are_403_and_nothing_changes(client):
    category = create_category(client).json()
    del client.headers[CSRF_HEADER_NAME]
    name = unique_name()

    assert client.post("/api/categories", json={"name": name, "kind": "expense"}).status_code == 403
    assert client.patch(
        f"/api/categories/{category['id']}", json={"is_archived": True}
    ).status_code == 403
    assert count_named(name) == 0
    assert db_row(category["id"])[2] is False


# --------------------------------------------------------------------------- 2. create


@pytest.mark.parametrize("kind", CATEGORY_KINDS)
def test_create_returns_201_and_the_row(client, kind):
    name = unique_name()
    response = create_category(client, name=f"  {name}  ", kind=kind)

    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["name"], body["kind"], body["is_archived"]) == (name, kind, False)
    assert set(body) == {"id", "name", "kind", "is_archived", "created_at"}
    assert db_row(body["id"]) == (name, kind, False)  # stored trimmed


def test_duplicate_name_is_409_and_only_one_row_exists(client):
    name = unique_name("dup")
    assert create_category(client, name=name).status_code == 201

    response = create_category(client, name=name, kind="income")

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    assert count_named(name) == 1


@pytest.mark.parametrize("kind", ["transfer", "Income", "", None])
def test_invalid_kind_is_422(client, kind):
    name = unique_name()
    assert create_category(client, name=name, kind=kind).status_code == 422
    assert count_named(name) == 0


def test_missing_kind_is_422(client):
    name = unique_name()
    assert client.post("/api/categories", json={"name": name}).status_code == 422
    assert count_named(name) == 0


@pytest.mark.parametrize(
    "name",
    # Prefixed where the value allows it, so a regression that lets one through still
    # leaves a `__t_` row the cleanup fixture removes.
    [
        "",
        "   ",
        f"{PREFIX}a\x00b",
        f"{PREFIX}tab\there",
        f"{PREFIX}zero​width",
        f"{PREFIX}﻿bom",
        PREFIX + "x" * 77,
        None,
    ],
)
def test_bad_name_is_422(client, name):
    assert create_category(client, name=name).status_code == 422


def test_80_char_name_is_accepted(client):
    name = (PREFIX + "x" * 80)[:80]
    response = create_category(client, name=name)
    assert response.status_code == 201, response.text


def test_unknown_field_on_create_is_422(client):
    name = unique_name()
    response = create_category(client, name=name, is_archived=True)
    assert response.status_code == 422
    assert count_named(name) == 0


# --------------------------------------------------------------------------- 3. list


def test_list_hides_archived_by_default_and_orders_by_kind_then_name(client):
    active = create_category(client).json()
    archived = create_category(client).json()
    assert client.patch(
        f"/api/categories/{archived['id']}", json={"is_archived": True}
    ).status_code == 200

    default = client.get("/api/categories").json()
    everything = client.get("/api/categories?include_archived=true").json()

    default_ids = {c["id"] for c in default}
    assert active["id"] in default_ids and archived["id"] not in default_ids
    assert {active["id"], archived["id"]} <= {c["id"] for c in everything}
    assert all(c["is_archived"] is False for c in default)
    keys = [(c["kind"], c["name"]) for c in everything]
    assert keys == sorted(keys)


# --------------------------------------------------------------------------- 4. PATCH


def test_rename(client):
    category = create_category(client, kind="income").json()
    new_name = unique_name("renamed")

    response = client.patch(f"/api/categories/{category['id']}", json={"name": new_name})

    assert response.status_code == 200, response.text
    assert response.json()["name"] == new_name
    assert db_row(category["id"]) == (new_name, "income", False)


def test_rename_onto_an_existing_name_is_409_and_nothing_changes(client):
    taken = unique_name("taken")
    assert create_category(client, name=taken).status_code == 201
    other = create_category(client).json()

    response = client.patch(f"/api/categories/{other['id']}", json={"name": taken})

    assert response.status_code == 409
    assert db_row(other["id"])[0] == other["name"]


@pytest.mark.parametrize("new_kind", ["income", "expense"])
def test_kind_cannot_be_changed(client, new_kind):
    # Even sending the current value is refused: kind is not a PATCH field at all.
    category = create_category(client, kind="expense").json()

    response = client.patch(f"/api/categories/{category['id']}", json={"kind": new_kind})

    assert response.status_code == 422
    assert db_row(category["id"])[1] == "expense"


def test_kind_alongside_a_valid_field_is_still_422_and_nothing_changes(client):
    category = create_category(client, kind="expense").json()

    response = client.patch(
        f"/api/categories/{category['id']}",
        json={"name": unique_name(), "kind": "income"},
    )

    assert response.status_code == 422
    assert db_row(category["id"]) == (category["name"], "expense", False)


def test_archive_and_unarchive(client):
    category = create_category(client).json()

    response = client.patch(f"/api/categories/{category['id']}", json={"is_archived": True})
    assert response.status_code == 200, response.text
    assert response.json()["is_archived"] is True
    assert db_row(category["id"])[2] is True

    response = client.patch(f"/api/categories/{category['id']}", json={"is_archived": False})
    assert response.status_code == 200
    assert response.json()["is_archived"] is False
    assert category["id"] in {c["id"] for c in client.get("/api/categories").json()}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": None},
        {"is_archived": None},
        {"name": "  "},
        {"is_archived": "yes"},
        {"id": 1},
        {"created_at": "2026-01-01T00:00:00Z"},
    ],
)
def test_patch_rejects_empty_null_and_unknown_bodies(client, body):
    category = create_category(client).json()

    response = client.patch(f"/api/categories/{category['id']}", json=body)

    assert response.status_code == 422
    assert db_row(category["id"]) == (category["name"], "expense", False)


def test_patch_unknown_category_is_404(client):
    response = client.patch(
        f"/api/categories/{missing_category_id()}", json={"name": unique_name()}
    )
    assert response.status_code == 404


def test_no_delete_endpoint(client):
    category = create_category(client).json()
    assert client.delete(f"/api/categories/{category['id']}").status_code == 405
    assert count_named(category["name"]) == 1


# --------------------------------------------------------------------------- 5. seeds


def test_seeded_categories_are_untouched(client):
    before = seeded_snapshot()
    assert len(before) >= 15  # the 0001 seed

    category = create_category(client).json()
    client.patch(f"/api/categories/{category['id']}", json={"name": unique_name()})
    client.patch(f"/api/categories/{category['id']}", json={"is_archived": True})
    create_category(client, name=before[0][1])  # 409 against a seeded name

    assert seeded_snapshot() == before
    assert all(archived is False for _, _, _, archived, _ in before)


# --------------------------------------------------------------------------- 6. transactions


def test_transaction_with_an_active_category_is_201(client):
    account_id = make_account(client)
    category = create_category(client).json()

    response = post_tx(client, account_id, category["id"])

    assert response.status_code == 201, response.text
    assert response.json()["category_id"] == category["id"]


def test_transaction_with_an_archived_category_is_409_and_nothing_posts(client):
    account_id = make_account(client)
    category = create_category(client).json()
    client.patch(f"/api/categories/{category['id']}", json={"is_archived": True})

    response = post_tx(client, account_id, category["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "category is archived"
    assert tx_count(account_id) == 0
    with SessionLocal() as db:
        assert db.get(Account, account_id).balance == 0


def test_transaction_with_a_missing_category_is_404_and_nothing_posts(client):
    # Before S3 this reached the FK at commit and came back as a 500.
    account_id = make_account(client)

    response = post_tx(client, account_id, missing_category_id())

    assert response.status_code == 404
    assert response.json()["detail"] == "category not found"
    assert tx_count(account_id) == 0


def test_transaction_without_a_category_still_posts(client):
    assert post_tx(client, make_account(client), None).status_code == 201


def test_existing_transaction_reads_fine_after_its_category_is_archived(client):
    account_id = make_account(client)
    category = create_category(client).json()
    posted = post_tx(client, account_id, category["id"]).json()

    assert client.patch(
        f"/api/categories/{category['id']}", json={"is_archived": True}
    ).status_code == 200

    listed = {t["id"]: t for t in client.get("/api/transactions").json()}
    assert listed[posted["id"]] == posted
    assert tx_count(account_id) == 1


# --------------------------------------------------------------------------- 7. DB rules (0003)


def test_database_refuses_a_bad_kind_and_defaults_is_archived_false():
    """Migration 0003's CHECK and server default, hit directly (bypassing the API),
    so a future writer that skips the schema still can't store a third kind."""
    name = unique_name("raw")
    with SessionLocal() as db:
        with pytest.raises(IntegrityError) as excinfo:
            db.execute(
                text("INSERT INTO categories (name, kind) VALUES (:n, 'transfer')"), {"n": name}
            )
        assert excinfo.value.orig.diag.constraint_name == "ck_categories_kind"
        db.rollback()

        db.execute(text("INSERT INTO categories (name, kind) VALUES (:n, 'income')"), {"n": name})
        db.commit()
    assert db_row_by_name(name) == ("income", False)


def db_row_by_name(name: str) -> tuple[str, bool]:
    with SessionLocal() as db:
        row = db.scalars(select(Category).where(Category.name == name)).one()
        return row.kind, row.is_archived
