from __future__ import annotations

from datetime import date as date_
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Budget(Base):
    __tablename__ = "budget"
    __table_args__ = (
        UniqueConstraint("category_id", "month", name="uq_budget_category_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    month: Mapped[date_] = mapped_column(Date)  # first day of the month
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
