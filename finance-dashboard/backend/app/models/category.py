"""Category — the label on a transaction (Groceries, Rent, Salary...)."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)

    # "income" or "expense" — groups categories on the dashboard and keeps
    # income rows out of expense budgets.
    kind: Mapped[str] = mapped_column(String(16), default="expense")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ~15 rows are seeded by the initial migration (spec Phase 0). Users manage
    # the list in Phase 3 (S3).
