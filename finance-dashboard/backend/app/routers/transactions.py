from __future__ import annotations

import hashlib
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Account, Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def dedupe_hash(date_iso: str, amount: Decimal | str, description: str) -> str:
    """Stable key for detecting an already-imported row (see ADR 0001)."""
    amount_2dp = f"{Decimal(amount):.2f}"
    raw = f"{date_iso}|{amount_2dp}|{description.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


@router.get("", response_model=list[TransactionRead])
def list_transactions(db: Session = Depends(get_db)) -> list[Transaction]:
    return list(
        db.scalars(
            select(Transaction).order_by(
                Transaction.date.desc(), Transaction.id.desc()
            )
        )
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db)
) -> Transaction:
    if db.get(Account, payload.account_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"account {payload.account_id} does not exist",
        )
    txn = Transaction(
        **payload.model_dump(),
        dedupe_hash=dedupe_hash(
            payload.date.isoformat(), payload.amount, payload.description
        ),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn
