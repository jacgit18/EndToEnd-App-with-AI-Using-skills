"""GET/POST /api/accounts — Phase 0 slice (spec: list + create only)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter()


@router.get("", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)) -> list[Account]:
    stmt = select(Account).order_by(Account.name)
    return list(db.scalars(stmt))


@router.post("", response_model=AccountRead, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(name=payload.name)  # balance defaults to 0.00 (column default)
    db.add(account)
    db.commit()
    db.refresh(account)  # pulls back the DB-assigned id, balance, created_at
    return account
