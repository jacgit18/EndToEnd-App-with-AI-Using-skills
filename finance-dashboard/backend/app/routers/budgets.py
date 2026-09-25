"""GET /api/budgets, PUT/DELETE /api/budgets/{month}/{category_id} — spec S6.

A budget is a planned amount for one (category, month). Unlike transactions it is
plain mutable data, not ledger history: setting it again overwrites, and DELETE
removes the row ("no row = no budget line", S6). Nothing else references a budget.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import delete, func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.budget import MONTH_PATTERN, BudgetRead, BudgetSet, CopyForwardResult

router = APIRouter()


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    month: Annotated[str, Query(pattern=MONTH_PATTERN)],
    db: Session = Depends(get_db),
) -> list[Budget]:
    """The budget lines for one month, by category. `month` is required: an
    unfiltered list across all months has no use yet. A malformed month is a 422,
    never an empty list that looks like "nothing budgeted"."""
    stmt = select(Budget).where(Budget.month == month).order_by(Budget.category_id)
    return list(db.scalars(stmt))


@router.put("/{month}/{category_id}", response_model=BudgetRead)
def set_budget(
    month: Annotated[str, Path(pattern=MONTH_PATTERN)],
    category_id: int,
    payload: BudgetSet,
    db: Session = Depends(get_db),
) -> Budget:
    """Create or overwrite the budget for (category, month). Idempotent: the same
    call twice leaves one row."""
    # FOR SHARE so a concurrent archive can't commit between this check and the write
    # (same pattern as transactions); it doesn't block other budget writers.
    category = db.get(Category, category_id, with_for_update={"read": True})
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")
    if category.is_archived:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="category is archived")

    # One statement, atomic: INSERT ... ON CONFLICT on the (category_id, month)
    # unique constraint. A get-then-insert-or-update would let two racing PUTs both
    # see "no row" and one die on the constraint as a 500.
    stmt = (
        insert(Budget)
        .values(category_id=category_id, month=month, amount=payload.amount)
        .on_conflict_do_update(
            constraint="uq_budget_category_month", set_={"amount": payload.amount}
        )
        .returning(Budget)
    )
    budget = db.scalars(stmt, execution_options={"populate_existing": True}).one()
    db.commit()
    return budget


@router.delete("/{month}/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    month: Annotated[str, Path(pattern=MONTH_PATTERN)],
    category_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Remove that month's budget line. 404 if there was none, so a typo'd month
    doesn't look like a successful clear."""
    result = db.execute(
        delete(Budget).where(Budget.month == month, Budget.category_id == category_id)
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="budget not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _previous_month(month: str) -> str:
    year, mon = int(month[:4]), int(month[5:])
    if mon == 1:
        year, mon = year - 1, 12
    else:
        mon -= 1
    return f"{year:04d}-{mon:02d}"


@router.post("/{month}/copy-forward", response_model=CopyForwardResult)
def copy_forward(
    month: Annotated[str, Path(pattern=MONTH_PATTERN)], db: Session = Depends(get_db)
) -> CopyForwardResult:
    """Copy the previous month's budget lines into `month` (S6). Never overwrites:
    a category that already has a line in `month` keeps it. Archived categories are
    not copied. `skipped` counts source lines that were not copied, for either reason,
    so `copied + skipped` is always the previous month's line count."""
    if month == "1000-01":
        # The previous month would be year 0999, outside the month pattern.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="no earlier month exists"
        )
    source = _previous_month(month)
    source_count = db.scalar(select(func.count()).select_from(Budget).where(Budget.month == source))

    # One INSERT ... SELECT: atomic, and ON CONFLICT DO NOTHING makes a second call
    # (or a race with a PUT) leave existing lines alone instead of failing. A category
    # archived between this statement's read and its commit can still get a line; that
    # is harmless (the archive blocks new transactions, not a planned amount).
    stmt = (
        insert(Budget)
        .from_select(
            ["category_id", "month", "amount"],
            select(Budget.category_id, literal(month), Budget.amount)
            .join(Category, Category.id == Budget.category_id)
            .where(Budget.month == source, Category.is_archived.is_(False)),
        )
        .on_conflict_do_nothing(constraint="uq_budget_category_month")
        .returning(Budget.id)
    )
    # RETURNING, not `.rowcount`: the driver reports -1 for this statement shape.
    copied = len(db.execute(stmt).all())
    db.commit()
    return CopyForwardResult(copied=copied, skipped=(source_count or 0) - copied)
