"""GET/POST/PATCH /api/accounts — list, create, edit/archive (spec S2)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter()

NAME_CONSTRAINT = "accounts_name_key"  # the UNIQUE(name) index, named by Postgres


def _is_name_conflict(exc: IntegrityError) -> bool:
    """True only for the unique-name violation. Any other integrity error is a bug
    or a new constraint, and must not be reported to the client as "duplicate name"."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == NAME_CONSTRAINT


def _out_of_range() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="resulting balance is out of range for NUMERIC(14,2)",
    )


@router.get("", response_model=list[AccountRead])
def list_accounts(
    include_archived: bool = False, db: Session = Depends(get_db)
) -> list[Account]:
    """Archived accounts are hidden by default (S2: hidden from pickers, history
    kept). The accounts page passes ?include_archived=true to show them."""
    stmt = select(Account).order_by(Account.name)
    if not include_archived:
        stmt = stmt.where(Account.is_archived.is_(False))
    return list(db.scalars(stmt))


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(
        name=payload.name,
        type=payload.type,
        starting_balance=payload.starting_balance,
        # ADR-0005's invariant is balance == starting_balance + SUM(transactions).
        # A new account has no transactions, so balance starts equal to the
        # starting balance. Without this line every account opened with a nonzero
        # starting balance would be wrong from its first row.
        balance=payload.starting_balance,
    )
    db.add(account)
    try:
        db.commit()
    except IntegrityError as exc:
        # name is UNIQUE. Catching the database's own refusal (not a check-then-
        # insert) is race-safe: two simultaneous creates can't both slip through.
        db.rollback()
        if not _is_name_conflict(exc):
            raise
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="an account with that name already exists",
        )
    db.refresh(account)  # pulls back the DB-assigned id and created_at
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)
) -> Account:
    """Edit name, type, starting balance, or archive/unarchive (`is_archived`).

    Only the fields the client sent change (AccountUpdate guarantees at least one,
    and that none is null or `balance`). Archiving keeps every transaction; it only
    hides the account from the default list.
    """
    # FOR UPDATE: lock this row until we commit. Without it two overlapping edits
    # each compute `delta` from the same stale starting_balance and the second one
    # adds a delta that is wrong for the row it actually lands on (measured: 58 of
    # 60 races broke the invariant). Anything else that writes `balance` (the
    # transactions router) takes the same lock, so all writers queue up.
    account = db.get(Account, account_id, with_for_update=True)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")

    changes = payload.model_dump(exclude_unset=True)

    if "starting_balance" in changes:
        # ADR-0005's invariant: balance == starting_balance + SUM(transactions).
        # Moving the starting balance by `delta` must move balance by the same
        # `delta`, in the same database transaction, or the invariant breaks and
        # reconciliation reports drift the owner never caused.
        #
        # `Account.balance + delta` is a SQL expression, so the database does the
        # addition (UPDATE ... SET balance = balance + :delta). A Python
        # `account.balance += delta` would read, add and write back, and a
        # transaction posted in between would be silently overwritten.
        delta = changes["starting_balance"] - account.starting_balance
        if delta:
            account.balance = Account.balance + delta

    for field, value in changes.items():
        setattr(account, field, value)

    try:
        db.commit()
    except DataError:
        db.rollback()  # e.g. balance + delta overflowed NUMERIC(14,2); nothing saved
        raise _out_of_range()
    except IntegrityError as exc:
        db.rollback()  # nothing was saved
        if not _is_name_conflict(exc):
            raise
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="an account with that name already exists",
        )
    db.refresh(account)  # balance was a SQL expression: re-read the real value
    return account
