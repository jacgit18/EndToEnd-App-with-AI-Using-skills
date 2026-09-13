"""Budget — a planned amount for one category in one month."""

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("category_id", "month", name="uq_budget_category_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    # "YYYY-MM" — the same string the dashboard endpoint takes as ?month=.
    month: Mapped[str] = mapped_column(String(7))

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    # Set/edit + copy-forward is built in Phase 6 (S6).
