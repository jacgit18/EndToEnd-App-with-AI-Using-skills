"""GET/POST /api/transactions, POST /api/transactions/{id}/void — spec S4.

Append-only (ADR-0005): there is no PUT/PATCH/DELETE here, and there never will
be. A correction is a void: a second, reversing row (`type="reversal"`, pointing
back through `reverses_transaction_id`) that cancels the first. The original is
never touched, so the ledger always shows what happened and when it was undone.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead

router = APIRouter()

ONE_REVERSAL_INDEX = "uq_transaction_one_reversal"  # migration 0004's partial unique index

# YYYY-MM with a real month (01-12). ASCII digits only ([0-9], not \d, which also
# matches other scripts' digits), and no year 0000 (Python's date can't hold it).
MONTH_PATTERN = r"^[1-9][0-9]{3}-(0[1-9]|1[0-2])$"


def _out_of_range() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="resulting balance is out of range for NUMERIC(14,2)",
    )


def _is_second_reversal(exc: IntegrityError) -> bool:
    """True only for the one-reversal-per-row violation; any other integrity error
    is a bug and must not be reported to the client as "already voided"."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == ONE_REVERSAL_INDEX


def _month_range(month: str) -> tuple[date, date | None]:
    """[first of month, first of next month). The upper bound is exclusive, so the
    last day of the month is in and the 1st of the next is out whatever the month's
    length. None for 9999-12, which has no next month a `date` can hold."""
    year, mon = int(month[:4]), int(month[5:])
    start = date(year, mon, 1)
    if mon == 12:
        return start, (date(year + 1, 1, 1) if year < 9999 else None)
    return start, date(year, mon + 1, 1)


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    month: Annotated[str | None, Query(pattern=MONTH_PATTERN)] = None,
    account_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Transaction]:
    """Newest first. `?month=YYYY-MM` and `?account_id=` narrow it (S4's list
    filters); both together are ANDed. A malformed month (2026-13, 2026-1) is a 422
    from the Query pattern, never an empty list that looks like "no spending"."""
    stmt = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
    if month is not None:
        start, end = _month_range(month)
        stmt = stmt.where(Transaction.date >= start)
        if end is not None:
            stmt = stmt.where(Transaction.date < end)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    return list(db.scalars(stmt))


@router.post("", response_model=TransactionRead, status_code=201)
def create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db)
) -> Transaction:
    # FOR UPDATE: `balance += amount` below is read-modify-write, so two writers of
    # the same account (two transactions, or an account edit that moves the starting
    # balance) must take turns. Unlocked, one silently overwrote the other (measured:
    # 26 of 60 edit-vs-post races left the balance off by the lost amount).
    account = db.get(Account, payload.account_id, with_for_update=True)
    if account is None:
        raise HTTPException(status_code=404, detail="account not found")
    if account.is_archived:
        # Archived means closed: history stays visible, no new activity posts to it.
        raise HTTPException(status_code=409, detail="account is archived")

    if payload.category_id is not None:
        # Checked here rather than left to the FK: a missing id used to surface as an
        # IntegrityError at commit, i.e. a 500. FOR SHARE (read=True) holds the row so
        # a concurrent archive can't commit between this check and our insert; it
        # doesn't block other posts that file under the same category.
        category = db.get(Category, payload.category_id, with_for_update={"read": True})
        if category is None:
            raise HTTPException(status_code=404, detail="category not found")
        if category.is_archived:
            # Archived categories keep their history but take no new transactions (S3).
            raise HTTPException(status_code=409, detail="category is archived")

    transaction = Transaction(
        account_id=payload.account_id,
        category_id=payload.category_id,
        date=payload.date,
        amount=payload.amount,
        description=payload.description,
    )
    db.add(transaction)

    # Maintained balance (ADR-0005 hybrid): updated here, in the same DB
    # transaction as the ledger insert — not recomputed from a SUM() on every
    # read. The reconciliation job (Phase 2) is what catches this ever drifting.
    account.balance += payload.amount

    try:
        db.commit()
    except DataError:
        db.rollback()  # balance + amount overflowed NUMERIC(14,2); nothing saved
        raise _out_of_range()
    db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/void", response_model=TransactionRead, status_code=201)
def void_transaction(transaction_id: int, db: Session = Depends(get_db)) -> Transaction:
    """Void a row by posting its reversal (ADR-0005). No body: everything the
    reversal carries is copied from the original, so there is nothing to choose.

    Returns the new reversal row. The original is left exactly as it was."""
    # A plain read is safe: ledger rows are never updated, so nothing about the
    # original can change under us. What can change is the account (archive,
    # another post) and whether a reversal exists — both handled below.
    original = db.get(Transaction, transaction_id)
    if original is None:
        raise HTTPException(status_code=404, detail="transaction not found")

    # Same lock, same order, as create_transaction and the account PATCH: every
    # writer of `balance` queues on the account row. It is also what makes the
    # already-voided pre-check below reliable — a second void waits here until the
    # first commits, then its pre-check (a new statement, so a fresh snapshot under
    # READ COMMITTED) sees the first reversal.
    account = db.get(Account, original.account_id, with_for_update=True)

    if original.type == "reversal":
        # Voiding a void would re-post the original's effect as a third row; the
        # right move for "I voided the wrong one" is to post the entry again.
        raise HTTPException(status_code=409, detail="transaction is a reversal")
    if account.is_archived:
        # Closed accounts take no new activity, and a reversal is new activity.
        raise HTTPException(status_code=409, detail="account is archived")

    already = db.scalar(
        select(Transaction.id).where(Transaction.reverses_transaction_id == original.id)
    )
    if already is not None:
        raise HTTPException(status_code=409, detail="transaction already voided")

    # No category check: an archived category refuses NEW transactions (S3), but a
    # void undoes an old one. History is history, and the reversal files under the
    # same category so category totals net to zero.
    reversal = Transaction(
        account_id=original.account_id,
        category_id=original.category_id,
        # The original's date, not today: the void cancels the entry in the month it
        # counted, so that month's totals come out as if it never happened.
        date=original.date,
        amount=-original.amount,
        description=f"Void: {original.description}"[:255],
        type="reversal",
        reverses_transaction_id=original.id,
    )
    db.add(reversal)
    account.balance += reversal.amount  # same DB transaction as the insert

    try:
        db.commit()
    except DataError:
        db.rollback()  # balance - amount overflowed NUMERIC(14,2); nothing saved
        raise _out_of_range()
    except IntegrityError as exc:
        # The race-safe backstop for the pre-check above: if a second reversal
        # of this row ever reaches the insert, migration 0004's partial unique
        # index refuses it and nothing (row or balance) is saved.
        db.rollback()
        if not _is_second_reversal(exc):
            raise
        raise HTTPException(status_code=409, detail="transaction already voided")
    db.refresh(reversal)
    return reversal
