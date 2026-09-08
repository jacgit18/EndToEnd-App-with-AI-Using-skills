from __future__ import annotations

from datetime import date as date_, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    date: Mapped[date_] = mapped_column(Date)
    # Negative = money out, positive = money in.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str] = mapped_column(String(255), default="")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id"), nullable=True
    )
    import_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_batch.id"), nullable=True
    )
    dedupe_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
