from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Account
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)) -> list[Account]:
    return list(db.scalars(select(Account).order_by(Account.name)))


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
