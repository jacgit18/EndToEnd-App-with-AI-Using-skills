"""Account — a place money lives (checking, savings, credit card)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


# The allowed account types (backlog S2). One list, used by the CHECK below and by
# the API schema, so the database and the API can't disagree about what's valid.
ACCOUNT_TYPES = ("checking", "savings", "credit_card", "cash")


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        # Mirrors migration 0002's constraint (same name) so Alembic autogenerate
        # sees the model and the table as matching. A CHECK, not a Postgres ENUM.
        CheckConstraint(
            "type IN (" + ", ".join(f"'{t}'" for t in ACCOUNT_TYPES) + ")",
            name="ck_accounts_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

    type: Mapped[str] = mapped_column(String(20))

    # Where the account began, before any ledger row. ADR-0005's invariant is
    #   balance == starting_balance + SUM(transactions.amount)
    # so this is what the reconciliation job adds the ledger sum to. No default:
    # the API must say what it is (creating an account also sets balance to it).
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    # Maintained balance (ADR-0005 hybrid). A cached figure, written in the same
    # DB transaction as each ledger insert and checked by the reconciliation job.
    # The sum of the account's transaction rows is the real source of truth.
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))

    # Archived accounts are hidden from pickers but keep their history (S2).
    is_archived: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
