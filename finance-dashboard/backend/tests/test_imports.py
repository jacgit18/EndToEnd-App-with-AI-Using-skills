"""CSV import API (S5a) through the real app.

Same setup as test_transactions.py: `app.main.app` over TestClient against a real,
migrated Postgres (the Compose db on host port 5433 by default). Every money
outcome is verified by effect, with direct SQL reads, against ADR-0005's invariant:

    balance == starting_balance + SUM(transactions.amount)

Every CSV is a synthetic string built here (`*.csv` is gitignored; real exports
are personal data). Every account is named `__t_<...>`; the autouse fixture deletes
exactly the transactions, import batches, accounts and login sessions that appeared
during the test (reversals first, then rows, then batches, then accounts: that is
the FK order), so the dev database is never left dirty.
"""

import os

from argon2 import PasswordHasher

TEST_EMAIL = "test-owner@example.com"
TEST_PASSWORD = "test-password"

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://finance:finance@localhost:5433/finance")
os.environ.setdefault("AUTH_EMAIL", TEST_EMAIL)
os.environ.setdefault("AUTH_PASSWORD_HASH", PasswordHasher().hash(TEST_PASSWORD))
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

import json  # noqa: E402
import threading  # noqa: E402
import uuid  # noqa: E402
from decimal import Decimal  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, func, select  # noqa: E402

from app import importer, rate_limit, reconcile  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.import_batch import ImportBatch  # noqa: E402
from app.models.session import AuthSession  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402
from app.routers import imports  # noqa: E402

PREFIX = "__t_"


def _is_test_row(column):
    # autoescape: `_` is a LIKE wildcard (see test_categories.py).
    return column.startswith(PREFIX, autoescape=True)


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def clean_state():
    """Delete only what this test created. Transactions and batches are found through
    the new `__t_` accounts (every import here targets one), so nothing that existed
    before the test, or belongs to a real account, is touched."""
    rate_limit._attempts.clear()
    with SessionLocal() as db:
        accounts_before = set(db.scalars(select(Account.id)))
        batches_before = set(db.scalars(select(ImportBatch.id)))
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
            if new_accounts:
                ours = Transaction.account_id.in_(new_accounts)
                db.execute(
                    delete(Transaction).where(ours, Transaction.reverses_transaction_id.is_not(None))
                )
                db.execute(delete(Transaction).where(ours))
                db.execute(
                    delete(ImportBatch).where(
                        ImportBatch.account_id.in_(new_accounts),
                        ImportBatch.id.not_in(batches_before),
                    )
                )
                db.execute(delete(Account).where(Account.id.in_(new_accounts)))
            new_sessions = set(db.scalars(select(AuthSession.id))) - sessions_before
            if new_sessions:
                db.execute(delete(AuthSession).where(AuthSession.id.in_(new_sessions)))
            db.commit()


@pytest.fixture
def auth():
    login_client = TestClient(app)
    response = login_client.post(
        "/api/auth/login", json={"email": settings.auth_email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return login_client.cookies.get(SESSION_COOKIE_NAME), response.json()["csrf_token"]


def make_client(auth) -> TestClient:
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


MAPPING = {
    "date_column": "Date",
    "amount_column": "Amount",
    "description_column": "Description",
    "date_format": "iso",
}


def csv_text(*rows: tuple[str, str, str], header: str = "Date,Amount,Description") -> str:
    return header + "\n" + "".join(f"{d},{a},{desc}\n" for d, a, desc in rows)


def preview(client, content: str | bytes):
    if isinstance(content, str):
        content = content.encode()
    return client.post(
        "/api/imports/preview", files={"file": ("stmt.csv", content, "text/csv")}
    )


def do_import(client, account_id, content: str | bytes, mapping=None, filename="stmt.csv"):
    if isinstance(content, str):
        content = content.encode()
    raw_mapping = mapping if isinstance(mapping, str) else json.dumps(mapping or MAPPING)
    return client.post(
        "/api/imports",
        files={"file": (filename, content, "text/csv")},
        data={"account_id": str(account_id), "mapping": raw_mapping},
    )


def imported(client, account_id, content, mapping=None) -> dict:
    response = do_import(client, account_id, content, mapping)
    assert response.status_code == 201, response.text
    return response.json()


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


def batches_for(account_id: int) -> list[ImportBatch]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(ImportBatch).where(ImportBatch.account_id == account_id).order_by(ImportBatch.id)
            )
        )


def rows_for(account_id: int) -> list[Transaction]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(Transaction).where(Transaction.account_id == account_id).order_by(Transaction.id)
            )
        )


def table_counts() -> tuple[int, int]:
    with SessionLocal() as db:
        return (
            db.scalar(select(func.count(Transaction.id))),
            db.scalar(select(func.count(ImportBatch.id))),
        )


STATEMENT = csv_text(
    ("2026-09-01", "-12.34", "Groceries"),
    ("2026-09-02", "2500.00", "Salary"),
    ("2026-09-03", "(40.00)", "Utilities"),
    ("2026-09-04", '"$1,000.01"', "Transfer in"),
)
STATEMENT_SUM = Decimal("-12.34") + Decimal("2500.00") - Decimal("40.00") + Decimal("1000.01")


# --------------------------------------------------------------------------- 1. preview


def test_preview_returns_header_and_first_rows_and_writes_nothing(client):
    make_account(client)  # something to not change
    before = table_counts()
    rows = [(f"2026-01-{i:02d}", f"-{i}.00", f"row {i}") for i in range(1, 16)]
    text = csv_text(*rows).replace("row 3\n", "row 3,extra\n")  # a ragged row

    response = preview(client, "﻿" + text)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["headers"] == ["Date", "Amount", "Description"]
    assert body["row_count"] == 15
    assert body["delimiter"] == ","
    assert len(body["rows"]) == 10
    assert body["rows"][0] == ["2026-01-01", "-1.00", "row 1"]
    assert body["rows"][2] == ["2026-01-03", "-3.00", "row 3", "extra"]
    assert table_counts() == before


def test_preview_sniffs_semicolons(client):
    body = preview(client, "Date;Amount;Description\n2026-01-01;1,50;x\n").json()
    assert body["delimiter"] == ";"
    assert body["rows"] == [["2026-01-01", "1,50", "x"]]


@pytest.mark.parametrize(
    "content, status, message",
    [
        (b"", 422, "empty"),
        (b"Date,Amount,Description\n", 422, "no data rows"),
        ("Date,Amount,Description\n2026-01-01,1,Café\n".encode("latin-1"), 422, "UTF-8"),
        (b"Date,Amount,Description\n" + b"2026-01-01,1,x\n" * 5001, 422, "5000"),
        (b"x" * (importer.MAX_FILE_BYTES + 1), 413, "larger"),
    ],
)
def test_preview_refuses_unusable_files(client, content, status, message):
    before = table_counts()
    response = preview(client, content)
    assert response.status_code == status
    assert message in response.json()["detail"]
    assert table_counts() == before


def test_preview_requires_a_session():
    assert preview(TestClient(app), STATEMENT).status_code == 401


def test_preview_without_csrf_token_is_403(client):
    del client.headers[CSRF_HEADER_NAME]
    assert preview(client, STATEMENT).status_code == 403


# --------------------------------------------------------------------------- 2. import: happy path


def test_import_posts_rows_uncategorized_and_moves_the_balance(client):
    account_id = make_account(client, "100.00")

    body = imported(client, account_id, STATEMENT)

    assert body["imported_count"] == 4
    assert body["skipped_count"] == 0
    assert body["rejected_count"] == 0
    assert body["rejected"] == []
    starting, balance, total, count = assert_invariant(account_id)
    assert (total, count) == (STATEMENT_SUM, 4)
    assert balance == Decimal("100.00") + STATEMENT_SUM

    rows = rows_for(account_id)
    assert [(r.date.isoformat(), r.amount, r.description) for r in rows] == [
        ("2026-09-01", Decimal("-12.34"), "Groceries"),
        ("2026-09-02", Decimal("2500.00"), "Salary"),
        ("2026-09-03", Decimal("-40.00"), "Utilities"),
        ("2026-09-04", Decimal("1000.01"), "Transfer in"),
    ]
    assert all(r.category_id is None for r in rows)
    assert all(r.type == "normal" and r.reverses_transaction_id is None for r in rows)
    assert all(r.import_batch_id == body["batch_id"] for r in rows)
    assert len({r.content_hash for r in rows}) == 4

    [batch] = batches_for(account_id)
    assert (batch.id, batch.filename, batch.imported_count, batch.skipped_count,
            batch.rejected_count) == (body["batch_id"], "stmt.csv", 4, 0, 0)


def test_import_with_mdy_and_invert_sign(client):
    account_id = make_account(client, "0.00")
    text = csv_text(("09/01/2026", "25.00", "Card spend"), ("09/02/2026", "(5.00)", "Card refund"),
                    header="Posted,Value,Memo")
    mapping = {"date_column": "Posted", "amount_column": "Value", "description_column": "Memo",
               "date_format": "mdy", "invert_sign": True}

    assert imported(client, account_id, text, mapping)["imported_count"] == 2

    rows = rows_for(account_id)
    assert [(r.date.isoformat(), r.amount) for r in rows] == [
        ("2026-09-01", Decimal("-25.00")),
        ("2026-09-02", Decimal("5.00")),
    ]
    assert assert_invariant(account_id)[1] == Decimal("-20.00")


def test_list_imports_newest_first(client):
    a = make_account(client)
    first = imported(client, a, STATEMENT)["batch_id"]
    second = imported(client, a, STATEMENT)["batch_id"]

    response = client.get("/api/imports")

    assert response.status_code == 200
    ours = [b for b in response.json() if b["account_id"] == a]
    assert [b["id"] for b in ours] == [second, first]
    assert ours[1] | {"created_at": None} == {
        "id": first, "filename": "stmt.csv", "account_id": a, "imported_count": 4,
        "skipped_count": 0, "rejected_count": 0, "created_at": None,
    }
    assert (ours[0]["imported_count"], ours[0]["skipped_count"]) == (0, 4)


def test_list_imports_requires_a_session():
    assert TestClient(app).get("/api/imports").status_code == 401


# --------------------------------------------------------------------------- 3. dedupe


def test_reimporting_the_same_file_skips_every_row(client):
    account_id = make_account(client, "100.00")
    imported(client, account_id, STATEMENT)
    after_first = db_state(account_id)

    body = imported(client, account_id, STATEMENT)

    assert (body["imported_count"], body["skipped_count"], body["rejected_count"]) == (0, 4, 0)
    assert db_state(account_id) == after_first  # no rows, balance unchanged
    # The empty second batch is still recorded (audit trail).
    assert [(b.imported_count, b.skipped_count) for b in batches_for(account_id)] == [(4, 0), (0, 4)]


def test_two_identical_rows_in_one_file_both_import_and_both_skip_on_reimport(client):
    account_id = make_account(client, "0.00")
    text = csv_text(("2026-09-01", "-3.50", "Coffee"), ("2026-09-01", "-3.50", "Coffee"))

    first = imported(client, account_id, text)
    second = imported(client, account_id, text)

    assert (first["imported_count"], first["skipped_count"]) == (2, 0)
    assert (second["imported_count"], second["skipped_count"]) == (0, 2)
    assert assert_invariant(account_id)[1:] == (Decimal("-7.00"), Decimal("-7.00"), 2)


def test_overlapping_file_imports_only_the_new_rows(client):
    account_id = make_account(client, "0.00")
    days = [(f"2026-08-{d:02d}", f"-{d}.00", f"Shop {d}") for d in range(1, 11)]
    imported(client, account_id, csv_text(*days[:6]))  # days 1-6

    body = imported(client, account_id, csv_text(*days[3:]))  # days 4-10: 3 old, 4 new

    assert (body["imported_count"], body["skipped_count"]) == (4, 3)
    _, balance, total, count = assert_invariant(account_id)
    assert count == 10
    assert total == -sum(Decimal(d) for d in range(1, 11))


def test_same_rows_into_a_different_account_are_not_duplicates(client):
    a = make_account(client, "0.00")
    b = make_account(client, "0.00")
    imported(client, a, STATEMENT)

    assert imported(client, b, STATEMENT)["imported_count"] == 4
    assert assert_invariant(b)[2] == STATEMENT_SUM


# --------------------------------------------------------------------------- 4. rejected rows


def test_rejected_rows_are_reported_by_line_and_the_rest_import(client):
    account_id = make_account(client, "0.00")
    text = (
        "Date,Amount,Description\n"  # 1
        "2026-09-01,-1.00,Good\n"  # 2
        "2026-02-30,-1.00,Bad date\n"  # 3
        "2026-09-02,0.00,Zero\n"  # 4
        "2026-09-03,1.234,Three decimals\n"  # 5
        "\n"  # 6
        "2026-09-04,-2.00,\n"  # 7 blank description
        "2026-09-05,-3.00,Also good\n"  # 8
    )

    body = imported(client, account_id, text)

    assert (body["imported_count"], body["skipped_count"], body["rejected_count"]) == (2, 0, 4)
    assert [r["line"] for r in body["rejected"]] == [3, 4, 5, 7]
    assert all(r["reason"] for r in body["rejected"])
    assert assert_invariant(account_id)[1:] == (Decimal("-4.00"), Decimal("-4.00"), 2)
    assert batches_for(account_id)[0].rejected_count == 4


def test_rejected_list_is_capped_but_the_count_is_exact(client):
    account_id = make_account(client)
    text = csv_text(*[("not-a-date", "-1.00", "x")] * 150) + "2026-09-01,-1.00,Fine\n"

    body = imported(client, account_id, text)

    assert body["rejected_count"] == 150
    assert len(body["rejected"]) == importer.REJECTED_LIST_CAP
    assert body["rejected"][0]["line"] == 2
    assert body["rejected"][-1]["line"] == 101
    assert body["imported_count"] == 1


def test_all_rows_rejected_still_records_a_batch(client):
    account_id = make_account(client)

    body = imported(client, account_id, csv_text(("bad", "-1.00", "x"), ("2026-01-01", "0", "y")))

    assert (body["imported_count"], body["skipped_count"], body["rejected_count"]) == (0, 0, 2)
    assert [(b.imported_count, b.rejected_count) for b in batches_for(account_id)] == [(0, 2)]
    assert db_state(account_id) == (Decimal("100.00"), Decimal("100.00"), 0, 0)


# --------------------------------------------------------------------------- 5. refused requests: nothing saved


def assert_nothing_saved(account_id: int, starting: str = "100.00"):
    assert db_state(account_id) == (Decimal(starting), Decimal(starting), 0, 0)
    assert batches_for(account_id) == []


@pytest.mark.parametrize(
    "mapping",
    [
        MAPPING | {"date_column": "Posted"},  # not in the header
        MAPPING | {"amount_column": "Date"},  # same column twice
        {k: v for k, v in MAPPING.items() if k != "date_format"},  # never defaulted
        MAPPING | {"date_format": "auto"},
        MAPPING | {"sign": "invert"},  # extra key
        "not json",
        "[]",
    ],
)
def test_bad_mapping_is_422_and_nothing_is_saved(client, mapping):
    account_id = make_account(client)

    response = do_import(client, account_id, STATEMENT, mapping)

    assert response.status_code == 422, response.text
    assert_nothing_saved(account_id)


def test_header_named_twice_is_422(client):
    account_id = make_account(client)
    text = "Date,Amount,Description,Amount\n2026-01-01,1,x,2\n"

    assert do_import(client, account_id, text).status_code == 422
    assert_nothing_saved(account_id)


@pytest.mark.parametrize(
    "content, status",
    [
        (b"", 422),
        (b"Date,Amount,Description\n", 422),
        ("Date,Amount,Description\n2026-01-01,1,Café\n".encode("latin-1"), 422),
        (b"Date,Amount,Description\n" + b"2026-01-01,-1.00,x\n" * 5001, 422),
        (b"Date,Amount,Description\n" + b"x" * importer.MAX_FILE_BYTES, 413),
    ],
)
def test_unusable_file_is_refused_and_nothing_is_saved(client, content, status):
    account_id = make_account(client)

    assert do_import(client, account_id, content).status_code == status
    assert_nothing_saved(account_id)


def test_unknown_account_is_404(client):
    with SessionLocal() as db:
        missing = (db.scalar(select(func.max(Account.id))) or 0) + 1000
    before = table_counts()

    response = do_import(client, missing, STATEMENT)

    assert response.status_code == 404
    assert response.json()["detail"] == "account not found"
    assert table_counts() == before


def test_archived_account_is_409_and_nothing_is_saved(client):
    account_id = make_account(client)
    assert client.patch(f"/api/accounts/{account_id}", json={"is_archived": True}).status_code == 200

    response = do_import(client, account_id, STATEMENT)

    assert response.status_code == 409
    assert response.json()["detail"] == "account is archived"
    assert_nothing_saved(account_id)


def test_overflowing_balance_is_422_and_nothing_is_saved(client):
    account_id = make_account(client, "-999999999999.00")
    text = csv_text(("2026-09-01", "-0.50", "a"), ("2026-09-02", "-0.50", "b"))  # -> -1e12

    response = do_import(client, account_id, text)

    assert response.status_code == 422
    assert "out of range" in response.json()["detail"]
    assert_nothing_saved(account_id, "-999999999999.00")  # no rows, no batch


def test_import_requires_a_session():
    assert do_import(TestClient(app), 1, STATEMENT).status_code == 401


def test_import_without_csrf_token_is_403_and_nothing_is_saved(client):
    account_id = make_account(client)
    del client.headers[CSRF_HEADER_NAME]

    assert do_import(client, account_id, STATEMENT).status_code == 403
    assert_nothing_saved(account_id)


def test_long_filename_is_cut_to_the_column(client):
    account_id = make_account(client)

    body = do_import(client, account_id, STATEMENT, filename="b" * 400 + ".csv").json()

    [batch] = batches_for(account_id)
    assert batch.id == body["batch_id"]
    assert batch.filename == "b" * 255


@pytest.mark.parametrize(
    "raw, stored",
    [("a\x00b\x1f.csv", "ab.csv"), ("  ", "upload.csv"), (None, "upload.csv"), ("\x00", "upload.csv")],
)
def test_filename_control_characters_are_dropped(raw, stored):
    # httpx percent-encodes control characters in a multipart filename, so a NUL
    # can't be sent through TestClient; the sanitiser is exercised directly.
    assert imports._filename(SimpleNamespace(filename=raw)) == stored


# --------------------------------------------------------------------------- 6. imported rows on the ledger


def test_voiding_an_imported_row_keeps_the_invariant(client):
    account_id = make_account(client, "100.00")
    imported(client, account_id, STATEMENT)
    salary = next(r for r in rows_for(account_id) if r.description == "Salary")

    response = client.post(f"/api/transactions/{salary.id}/void")

    assert response.status_code == 201, response.text
    _, balance, total, count = assert_invariant(account_id)
    assert count == 5
    assert balance == Decimal("100.00") + STATEMENT_SUM - Decimal("2500.00")
    # The reversal is a hand-made row: no hash, no batch. Re-importing still skips all.
    reversal = rows_for(account_id)[-1]
    assert (reversal.content_hash, reversal.import_batch_id) == (None, None)
    assert imported(client, account_id, STATEMENT)["skipped_count"] == 4


def test_reconcile_finds_no_drift_after_imports(client):
    account_id = make_account(client, "500.00")
    imported(client, account_id, STATEMENT)
    imported(client, account_id, csv_text(("2026-09-09", "-9.99", "More")))

    with SessionLocal() as db:
        _, drifted = reconcile.find_drift(db)
    assert [d for d in drifted if d[0] == account_id] == []
    assert assert_invariant(account_id)[1] == Decimal("500.00") + STATEMENT_SUM - Decimal("9.99")


def test_imported_rows_are_not_filed_under_any_category(client):
    # A seeded category exists; nothing the import does should pick one.
    account_id = make_account(client)
    imported(client, account_id, STATEMENT)
    with SessionLocal() as db:
        assert db.scalar(select(func.count(Category.id))) > 0
    assert {r.category_id for r in rows_for(account_id)} == {None}


# --------------------------------------------------------------------------- 7. concurrency


ROUNDS = 20


def run_together(auth, jobs) -> list:
    """Run each job(client) on its own thread with its own TestClient, released
    together by a barrier. Returns each job's response (or the exception)."""
    barrier = threading.Barrier(len(jobs))
    results: list = [None] * len(jobs)

    def worker(index, job):
        try:
            client = make_client(auth)
            barrier.wait(timeout=30)
            results[index] = job(client)
        except Exception as exc:  # surfaced by the caller's asserts, not swallowed
            results[index] = exc

    threads = [threading.Thread(target=worker, args=(i, j)) for i, j in enumerate(jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    assert not any(t.is_alive() for t in threads), "a request hung"
    return results


def test_two_simultaneous_imports_of_one_file_insert_each_row_once(auth):
    """Same file, same account, at the same moment. Between them every row is
    imported exactly once (the other skips it), and the balance moves by the file's
    sum exactly once."""
    setup = make_client(auth)
    account_id = make_account(setup, "0.00")
    expected = Decimal("0.00")

    for round_no in range(ROUNDS):
        rows = [(f"2026-07-{d:02d}", f"-{d}.{round_no:02d}", f"r{round_no}") for d in range(1, 6)]
        rows.append(rows[0])  # an in-file duplicate too: key|0 and key|1
        text = csv_text(*rows)

        results = run_together(auth, [lambda c: do_import(c, account_id, text)] * 2)

        assert all(not isinstance(r, Exception) and r.status_code == 201 for r in results), (
            round_no, results)
        bodies = [r.json() for r in results]
        assert sum(b["imported_count"] for b in bodies) == len(rows), (round_no, bodies)
        assert sum(b["skipped_count"] for b in bodies) == len(rows), (round_no, bodies)
        expected += sum(Decimal(a) for _, a, _ in rows)
        _, balance, total, _ = assert_invariant(account_id)
        assert total == expected, round_no


def test_simultaneous_imports_of_different_files_keep_the_invariant(auth):
    """Two different files (plus a hand-entered post) into ONE account at once. All
    rows are new, so each import really moves the balance; without the account lock
    one stale `balance +=` overwrites the other and the invariant breaks."""
    setup = make_client(auth)
    account_id = make_account(setup, "0.00")
    expected = Decimal("0.00")

    for round_no in range(ROUNDS):
        rows_a = [(f"2026-06-{d:02d}", f"-{d}.{round_no:02d}", "a") for d in range(1, 4)]
        rows_b = [(f"2026-05-{d:02d}", f"{d}0.{round_no:02d}", "b") for d in range(1, 4)]
        file_a, file_b = csv_text(*rows_a), csv_text(*rows_b)
        manual = {"account_id": account_id, "date": "2026-04-01", "amount": f"7.{round_no:02d}",
                  "description": f"{PREFIX}manual"}
        jobs = [
            lambda c: do_import(c, account_id, file_a),
            lambda c: do_import(c, account_id, file_b),
            lambda c: c.post("/api/transactions", json=manual),
        ]

        results = run_together(auth, jobs)

        assert [getattr(r, "status_code", r) for r in results] == [201, 201, 201], (round_no, results)
        expected += sum(Decimal(a) for _, a, _ in rows_a + rows_b) + Decimal(manual["amount"])
        _, balance, total, _ = assert_invariant(account_id)
        assert total == expected, round_no
