"""Account — a place money lives (checking, savings, credit card)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

    # Maintained balance (ADR-0005 hybrid). A cached figure, written in the same
    # DB transaction as each ledger insert and checked by the reconciliation job.
    # The sum of the account's transaction rows is the real source of truth.
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))

    # S2 can archive an account: hidden from pickers, history kept. Column ships
    # now with the schema; the behaviour lands in Phase 2.
    is_archived: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
