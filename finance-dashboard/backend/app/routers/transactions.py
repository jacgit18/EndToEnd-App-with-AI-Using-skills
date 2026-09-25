"""GET/POST /api/transactions — Phase 0 slice.

POST is append-only insert (ADR-0005): there is no PUT/PATCH/DELETE here, and
there never will be — a correction is a Phase 4 (S4) reversal row, not an
edit to this one.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead

router = APIRouter()


@router.get("", response_model=list[TransactionRead])
def list_transactions(db: Session = Depends(get_db)) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
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
        raise HTTPException(
            status_code=422, detail="resulting balance is out of range for NUMERIC(14,2)"
        )
    db.refresh(transaction)
    return transaction
