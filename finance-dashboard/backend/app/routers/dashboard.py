"""GET /api/dashboard?month= — spec S7 (docs/phase7-spec.md).

Read-only aggregation over the ledger. The definitions live in the spec; the one
invariant everything is built to keep is `net == SUM(amount)` for the month, so the
dashboard can never disagree with the transactions list.

Aggregations are raw SQL (the spec's choice); the recent list reuses the ORM.
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.transaction import Transaction
from app.routers.transactions import _month_range
from app.schemas.budget import MONTH_PATTERN
from app.schemas.dashboard import Dashboard, DashboardCategory

router = APIRouter()

RECENT_LIMIT = 10
ZERO = Decimal("0.00")


def _range_sql(end) -> str:
    # 9999-12 has no "first of next month" a date can hold, so its upper bound is dropped.
    return "t.date >= :start" + (" AND t.date < :end" if end is not None else "")


@router.get("", response_model=Dashboard)
def dashboard(
    month: Annotated[str, Query(pattern=MONTH_PATTERN)],
    db: Session = Depends(get_db),
) -> Dashboard:
    start, end = _month_range(month)
    params: dict = {"start": start, "month": month}
    if end is not None:
        params["end"] = end
    in_range = _range_sql(end)

    # Sum of amounts per category kind; category-less rows come back as kind NULL.
    kind_sums: dict[str | None, Decimal] = {
        kind: total
        for kind, total in db.execute(
            text(
                "SELECT c.kind, SUM(t.amount) FROM transactions t "
                "LEFT JOIN categories c ON c.id = t.category_id "
                f"WHERE {in_range} GROUP BY c.kind"
            ),
            params,
        )
    }
    income_sum = kind_sums.get("income", ZERO)
    expense_sum = kind_sums.get("expense", ZERO)
    uncategorized = kind_sums.get(None, ZERO)

    # Uncategorized rows are summed, then placed by the sign of the net: netting first
    # keeps a void in the same column as its original.
    income = income_sum + (uncategorized if uncategorized > 0 else ZERO)
    expense = -expense_sum + (-uncategorized if uncategorized < 0 else ZERO)

    rows = db.execute(
        text(
            "WITH spend AS ("
            " SELECT t.category_id, -SUM(t.amount) AS actual FROM transactions t"
            f" WHERE {in_range} AND t.category_id IS NOT NULL GROUP BY t.category_id) "
            "SELECT c.id, c.name, COALESCE(s.actual, 0) AS actual, b.amount AS budget "
            "FROM categories c "
            "LEFT JOIN spend s ON s.category_id = c.id "
            "LEFT JOIN budgets b ON b.category_id = c.id AND b.month = :month "
            "WHERE c.kind = 'expense' AND (b.amount IS NOT NULL OR COALESCE(s.actual, 0) <> 0) "
            "ORDER BY actual DESC, c.id"
        ),
        params,
    )
    # quantize: COALESCE(..., 0) yields an integer 0 for a budget-only row, and money
    # leaves the API with exactly two decimals.
    categories = [
        DashboardCategory(
            category_id=cid, name=name, actual=actual.quantize(ZERO), budget=budget
        )
        for cid, name, actual, budget in rows
    ]
    if uncategorized < 0:
        categories.append(
            DashboardCategory(
                category_id=None, name="Uncategorized", actual=-uncategorized, budget=None
            )
        )

    stmt = select(Transaction).where(Transaction.date >= start)
    if end is not None:
        stmt = stmt.where(Transaction.date < end)
    stmt = stmt.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(RECENT_LIMIT)

    return Dashboard(
        month=month,
        income=income,
        expense=expense,
        net=income - expense,
        categories=categories,
        recent=list(db.scalars(stmt)),
    )
