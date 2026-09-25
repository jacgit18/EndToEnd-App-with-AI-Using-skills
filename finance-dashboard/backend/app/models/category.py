"""Category — the label on a transaction (Groceries, Rent, Salary...)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


# The allowed category kinds (backlog S3). One list, used by the CHECK below and
# by the API schema, so the database and the API can't disagree about what's valid.
CATEGORY_KINDS = ("income", "expense")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Mirrors migration 0003's constraint (same name) so Alembic autogenerate
        # sees the model and the table as matching. A CHECK, not a Postgres ENUM.
        CheckConstraint(
            "kind IN (" + ", ".join(f"'{k}'" for k in CATEGORY_KINDS) + ")",
            name="ck_categories_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)

    # "income" or "expense" — groups categories on the dashboard and keeps
    # income rows out of expense budgets. Immutable through the API once set
    # (S3): flipping it would silently re-bucket every past transaction.
    kind: Mapped[str] = mapped_column(String(16), default="expense")

    # Archived categories are hidden from pickers but keep their history (S3),
    # and no new transaction can be filed under one. There is no delete.
    is_archived: Mapped[bool] = mapped_column(default=False, server_default=false())

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ~15 rows are seeded by the initial migration (spec Phase 0); the owner
    # manages the list from Phase 3 (S3) on.
