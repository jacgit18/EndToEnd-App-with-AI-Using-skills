"""Reconciliation job: check the maintained balance against the ledger (ADR-0005).

Invariant: accounts.balance == accounts.starting_balance + SUM(transactions.amount)

Second check: every reversal must exactly cancel the row it reverses (same account,
amounts summing to 0). The invariant above can't see a reversal with the wrong amount,
because the balance and the ledger sum are both off by the same figure.

Read-only by design: it reports drift, it never repairs it. A repair would have to
write `balance` (row lock required) and decide which side is right; that is a human
call, made after reading the WARN lines. Run from cron:

    docker compose exec backend uv run python -m app.reconcile

Exit code 0 = every account matches, 1 = at least one drifted or bad reversal, 2 = the job itself could
not run (DB unreachable, or no accounts at all, which usually means the wrong database).
Archived accounts are checked too: closed does not mean exempt.
"""

import logging
import sys
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.db import SessionLocal
from app.models.account import Account
from app.models.transaction import Transaction

log = logging.getLogger("reconcile")


def find_drift(db) -> tuple[int, list[tuple[int, str, Decimal, Decimal]]]:
    """Return (accounts checked, [(id, name, stored, expected) for each mismatch]).

    One SQL statement, so Postgres reads balance and the ledger sum from a single
    snapshot: a transaction posting mid-run can't produce a false positive. The
    LEFT JOIN + COALESCE makes an account with no transactions sum to 0, not NULL.
    """
    ledger = (
        select(
            Transaction.account_id,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by(Transaction.account_id)
        .subquery()
    )
    expected = Account.starting_balance + func.coalesce(ledger.c.total, 0)
    rows = db.execute(
        select(Account.id, Account.name, Account.balance, expected)
        .outerjoin(ledger, ledger.c.account_id == Account.id)
        .order_by(Account.id)
    ).all()
    return len(rows), [(i, n, stored, exp) for i, n, stored, exp in rows if stored != exp]


def find_bad_reversals(db) -> list[tuple[int, int, int, Decimal, Decimal]]:
    """Return [(reversal id, original id, account id, reversal amount, original amount)]
    for each reversal that does not exactly cancel its original.

    The balance invariant can't catch these: a reversal posted for the wrong amount
    moves `balance` and the ledger SUM by the same figure, so they still agree. Same
    account is part of "cancels": a reversal filed on another account leaves both
    accounts off by the original's amount in the books even though each ties out.
    """
    original = aliased(Transaction)
    rows = db.execute(
        select(
            Transaction.id,
            original.id,
            Transaction.account_id,
            Transaction.amount,
            original.amount,
        )
        .join(original, Transaction.reverses_transaction_id == original.id)
        .where(
            (Transaction.amount + original.amount != 0)
            | (Transaction.account_id != original.account_id)
        )
        .order_by(Transaction.id)
    ).all()
    return [tuple(r) for r in rows]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Dev's engine echoes SQL to stdout itself; stop it printing a second time via root.
    logging.getLogger("sqlalchemy.engine").propagate = False
    try:
        with SessionLocal() as db:
            checked, drifted = find_drift(db)
            bad_reversals = find_bad_reversals(db)
    except Exception:
        log.exception("reconcile could not run")
        return 2
    if checked == 0:
        log.error("no accounts found: wrong or empty database? refusing to report ok")
        return 2
    for account_id, name, stored, expected in drifted:
        log.warning(
            "DRIFT account id=%s name=%r stored=%s expected=%s diff=%s",
            account_id, name, stored, expected, stored - expected,
        )
    for reversal_id, original_id, account_id, amount, original_amount in bad_reversals:
        log.warning(
            "BAD REVERSAL id=%s reverses=%s account id=%s amount=%s original amount=%s",
            reversal_id, original_id, account_id, amount, original_amount,
        )
    if drifted:
        log.error("%d of %d accounts drifted", len(drifted), checked)
    if bad_reversals:
        log.error("%d reversals do not cancel their original", len(bad_reversals))
    if drifted or bad_reversals:
        return 1
    log.info("ok: %d accounts match the ledger", checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
