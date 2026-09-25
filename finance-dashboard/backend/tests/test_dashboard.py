"""Dashboard API (S7) through the real app, against a real migrated Postgres.

Same setup as test_transactions.py. Every account and category made here is named
`__t_<...>`; the autouse fixture deletes exactly what the test created. All rows sit
in a far-future month (2031) so real data can never leak into a total.

The headline test is the reconciliation one: the dashboard's net must equal the plain
sum of the same month's transactions list (spec S7: "every figure reconciles").
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
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, or_, select  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.dependencies import CSRF_HEADER_NAME, SESSION_COOKIE_NAME  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.budget import Budget  # noqa: E402
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
                db.execute(delete(Budget).where(Budget.category_id.in_(new_categories)))
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


M = "2031-05"
D = "2031-05-10"


# --------------------------------------------------------------------------- helpers


def unique_name(label: str = "acct") -> str:
    return f"{PREFIX}{label}_{uuid.uuid4().hex[:10]}"


def make_account(client) -> int:
    response = client.post(
        "/api/accounts",
        json={"name": unique_name(), "type": "checking", "starting_balance": "0.00"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def make_category(client, kind="expense", archived=False) -> int:
    response = client.post("/api/categories", json={"name": unique_name("cat"), "kind": kind})
    assert response.status_code == 201, response.text
    cid = response.json()["id"]
    if archived:
        assert client.patch(f"/api/categories/{cid}", json={"is_archived": True}).status_code == 200
    return cid


def post(client, account_id, amount, category_id=None, date=D) -> dict:
    body = {
        "account_id": account_id,
        "date": date,
        "amount": amount,
        "description": f"{PREFIX}tx",
    }
    if category_id is not None:
        body["category_id"] = category_id
    response = client.post("/api/transactions", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def budget(client, cid, amount, month=M):
    assert client.put(f"/api/budgets/{month}/{cid}", json={"amount": amount}).status_code == 200


def dash(client, month=M) -> dict:
    response = client.get("/api/dashboard", params={"month": month})
    assert response.status_code == 200, response.text
    return response.json()


def by_id(data) -> dict:
    return {c["category_id"]: c for c in data["categories"]}


# --------------------------------------------------------------------------- totals


def test_empty_month_is_all_zero(client):
    data = dash(client, "2031-07")
    assert data == {
        "month": "2031-07",
        "income": "0.00",
        "expense": "0.00",
        "net": "0.00",
        "categories": [],
        "recent": [],
    }


def test_income_and_expense_come_from_category_kind(client):
    acct, groceries, salary = make_account(client), make_category(client), make_category(client, "income")
    post(client, acct, "-40.00", groceries)
    post(client, acct, "-10.50", groceries)
    post(client, acct, "1000.00", salary)
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("1000.00", "50.50", "949.50")


def test_refund_on_an_expense_category_reduces_expense_not_income(client):
    acct, cat = make_account(client), make_category(client)
    post(client, acct, "-40.00", cat)
    post(client, acct, "15.00", cat)  # refund
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("0.00", "25.00", "-25.00")
    assert by_id(data)[cat]["actual"] == "25.00"


def test_void_nets_the_original_to_zero(client):
    acct, cat = make_account(client), make_category(client)
    tx = post(client, acct, "-40.00", cat)
    assert client.post(f"/api/transactions/{tx['id']}/void").status_code == 201
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("0.00", "0.00", "0.00")
    assert data["categories"] == []  # nets to zero, no budget: no row


def test_other_months_are_excluded_and_month_edges_are_in(client):
    acct, cat = make_account(client), make_category(client)
    post(client, acct, "-1.00", cat, date="2031-04-30")  # before
    post(client, acct, "-2.00", cat, date="2031-05-01")  # first day: in
    post(client, acct, "-4.00", cat, date="2031-05-31")  # last day: in
    post(client, acct, "-8.00", cat, date="2031-06-01")  # after
    assert dash(client)["expense"] == "6.00"


# --------------------------------------------------------------------------- reconciliation


def test_net_equals_the_plain_sum_of_the_transactions_list(client):
    acct, groceries, rent, salary = (
        make_account(client),
        make_category(client),
        make_category(client),
        make_category(client, "income"),
    )
    voided = post(client, acct, "-33.33", groceries)
    client.post(f"/api/transactions/{voided['id']}/void")
    post(client, acct, "-12.10", groceries)
    post(client, acct, "-900.00", rent)
    post(client, acct, "2500.00", salary)
    post(client, acct, "-7.77")  # uncategorized spend
    post(client, acct, "3.00", groceries)  # refund
    listed = client.get("/api/transactions", params={"month": M}).json()
    mine = [t for t in listed if t["account_id"] == acct]  # the void's description differs
    assert len(mine) == 7  # 6 postings + 1 reversal
    data = dash(client)
    assert Decimal(data["net"]) == sum(Decimal(t["amount"]) for t in mine)
    assert Decimal(data["net"]) == Decimal(data["income"]) - Decimal(data["expense"])


def test_expense_equals_the_sum_of_the_category_rows(client):
    acct, a, b = make_account(client), make_category(client), make_category(client)
    post(client, acct, "-10.00", a)
    post(client, acct, "-20.25", b)
    post(client, acct, "-5.00")  # uncategorized
    data = dash(client)
    assert Decimal(data["expense"]) == sum(Decimal(c["actual"]) for c in data["categories"])
    assert data["expense"] == "35.25"


# --------------------------------------------------------------------------- uncategorized


def test_uncategorized_spend_counts_as_expense_with_its_own_line(client):
    acct = make_account(client)
    post(client, acct, "-5.00")
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("0.00", "5.00", "-5.00")
    assert data["categories"] == [
        {"category_id": None, "name": "Uncategorized", "actual": "5.00", "budget": None}
    ]


def test_uncategorized_money_in_counts_as_income_and_has_no_expense_line(client):
    acct = make_account(client)
    post(client, acct, "9.00")
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("9.00", "0.00", "9.00")
    assert data["categories"] == []


def test_a_voided_uncategorized_deposit_does_not_move_into_expense(client):
    acct = make_account(client)
    tx = post(client, acct, "9.00")
    client.post(f"/api/transactions/{tx['id']}/void")
    data = dash(client)
    assert (data["income"], data["expense"], data["net"]) == ("0.00", "0.00", "0.00")


# --------------------------------------------------------------------------- category rows


def test_budget_only_and_spend_only_rows_both_appear(client):
    acct, budgeted, unbudgeted = make_account(client), make_category(client), make_category(client)
    budget(client, budgeted, "100.00")
    post(client, acct, "-30.00", unbudgeted)
    rows = by_id(dash(client))
    assert rows[budgeted]["actual"] == "0.00" and rows[budgeted]["budget"] == "100.00"
    assert rows[unbudgeted]["actual"] == "30.00" and rows[unbudgeted]["budget"] is None


def test_budget_and_spend_together(client):
    acct, cat = make_account(client), make_category(client)
    budget(client, cat, "100.00")
    post(client, acct, "-130.00", cat)
    assert by_id(dash(client))[cat] == {
        "category_id": cat,
        "name": by_id(dash(client))[cat]["name"],
        "actual": "130.00",
        "budget": "100.00",
    }


def test_budget_of_another_month_does_not_show(client):
    cat = make_category(client)
    budget(client, cat, "100.00", month="2031-06")
    assert cat not in by_id(dash(client))


def test_archived_category_with_spend_is_still_listed(client):
    acct, cat = make_account(client), make_category(client)
    post(client, acct, "-12.00", cat)
    client.patch(f"/api/categories/{cat}", json={"is_archived": True})
    assert by_id(dash(client))[cat]["actual"] == "12.00"


def test_income_categories_are_not_in_the_category_rows(client):
    acct, salary = make_account(client), make_category(client, "income")
    post(client, acct, "500.00", salary)
    assert salary not in by_id(dash(client))


def test_rows_are_biggest_spend_first(client):
    acct, small, big = make_account(client), make_category(client), make_category(client)
    post(client, acct, "-1.00", small)
    post(client, acct, "-99.00", big)
    ids = [c["category_id"] for c in dash(client)["categories"]]
    assert ids == [big, small]


# --------------------------------------------------------------------------- recent


def test_recent_is_the_last_ten_newest_first_and_includes_reversals(client):
    acct, cat = make_account(client), make_category(client)
    made = [post(client, acct, "-1.00", cat, date=f"2031-05-{day:02d}") for day in range(1, 13)]
    client.post(f"/api/transactions/{made[0]['id']}/void")  # reversal dated 2031-05-01
    recent = dash(client)["recent"]
    assert len(recent) == 10
    dates = [t["date"] for t in recent]
    assert dates == sorted(dates, reverse=True)
    assert dates[0] == "2031-05-12"
    # 13 rows in the month; the three oldest (two on 05-01 plus 05-02) are cut off
    assert "2031-05-02" not in dates
    assert all(t["amount"] == "-1.00" or t["type"] == "reversal" for t in recent)


# --------------------------------------------------------------------------- validation


@pytest.mark.parametrize("month", ["2031-13", "2031-5", "2031-05-01", "0000-01", "abc", ""])
def test_bad_month_is_422(client, month):
    assert client.get("/api/dashboard", params={"month": month}).status_code == 422


def test_month_is_required(client):
    assert client.get("/api/dashboard").status_code == 422


def test_needs_a_session():
    assert TestClient(app).get("/api/dashboard", params={"month": M}).status_code == 401


# --------------------------------------------------------------------------- trend


def trend(client, month=M) -> dict:
    response = client.get("/api/dashboard/trend", params={"month": month})
    assert response.status_code == 200, response.text
    return response.json()


def test_trend_is_six_months_oldest_first_ending_at_month_empty_are_zero(client):
    data = trend(client, "2031-07")
    assert data["month"] == "2031-07"
    assert [p["month"] for p in data["points"]] == [
        "2031-02", "2031-03", "2031-04", "2031-05", "2031-06", "2031-07",
    ]
    assert all(p["net"] == "0.00" for p in data["points"])


def test_trend_window_crosses_a_year_boundary(client):
    data = trend(client, "2031-02")
    assert [p["month"] for p in data["points"]] == [
        "2030-09", "2030-10", "2030-11", "2030-12", "2031-01", "2031-02",
    ]


def test_trend_net_per_month_is_the_plain_sum_and_matches_dashboard(client):
    acct, cat, salary = make_account(client), make_category(client), make_category(client, "income")
    post(client, acct, "-40.00", cat, date="2031-03-31")
    post(client, acct, "-10.25", None, date="2031-03-01")
    post(client, acct, "1000.00", salary, date="2031-05-01")
    post(client, acct, "-5.00", cat, date="2031-05-31")
    post(client, acct, "-99.00", cat, date="2031-08-01")  # after the window
    post(client, acct, "-77.00", cat, date="2030-12-31")  # before the window
    points = {p["month"]: p["net"] for p in trend(client, "2031-07")["points"]}
    assert points == {
        "2031-02": "0.00", "2031-03": "-50.25", "2031-04": "0.00",
        "2031-05": "995.00", "2031-06": "0.00", "2031-07": "0.00",
    }
    for m in ("2031-03", "2031-05"):
        assert dash(client, m)["net"] == points[m]


def test_trend_void_nets_to_zero(client):
    acct, cat = make_account(client), make_category(client)
    tx = post(client, acct, "-40.00", cat, date="2031-04-10")
    assert client.post(f"/api/transactions/{tx['id']}/void").status_code == 201
    points = {p["month"]: p["net"] for p in trend(client, "2031-04")["points"]}
    assert points["2031-04"] == "0.00"


def test_trend_at_the_earliest_month_drops_months_before_year_1000(client):
    data = trend(client, "1000-02")
    assert [p["month"] for p in data["points"]] == ["1000-01", "1000-02"]


def test_trend_at_the_last_month_works(client):
    data = trend(client, "9999-12")
    assert data["points"][-1]["month"] == "9999-12"
    assert len(data["points"]) == 6


@pytest.mark.parametrize("month", ["2031-13", "2031-1", "", "abc"])
def test_trend_bad_month_is_422(client, month):
    assert client.get("/api/dashboard/trend", params={"month": month}).status_code == 422


def test_trend_month_is_required(client):
    assert client.get("/api/dashboard/trend").status_code == 422


def test_trend_needs_a_session():
    assert TestClient(app).get("/api/dashboard/trend", params={"month": M}).status_code == 401
