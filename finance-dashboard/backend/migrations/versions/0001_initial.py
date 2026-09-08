"""initial schema + seeded categories

Revision ID: 0001
Revises:
Create Date: 2026-09-08

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_CATEGORIES: list[tuple[str, str]] = [
    ("Salary", "income"),
    ("Interest", "income"),
    ("Other Income", "income"),
    ("Groceries", "expense"),
    ("Dining", "expense"),
    ("Rent/Mortgage", "expense"),
    ("Utilities", "expense"),
    ("Transport", "expense"),
    ("Fuel", "expense"),
    ("Insurance", "expense"),
    ("Healthcare", "expense"),
    ("Entertainment", "expense"),
    ("Shopping", "expense"),
    ("Subscriptions", "expense"),
    ("Travel", "expense"),
    ("Fees & Charges", "expense"),
    ("Miscellaneous", "expense"),
]


def upgrade() -> None:
    account_type = sa.Enum(
        "checking", "savings", "credit_card", "cash", name="account_type"
    )
    category_kind = sa.Enum("income", "expense", name="category_kind")

    op.create_table(
        "account",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("type", account_type, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "starting_balance",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "archived", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "category",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("kind", category_kind, nullable=False),
        sa.Column(
            "archived", sa.Boolean, nullable=False, server_default=sa.false()
        ),
    )

    op.create_table(
        "import_batch",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("source", sa.String(80), nullable=False, server_default="csv"),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "transaction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer,
            sa.ForeignKey("account.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "description", sa.String(255), nullable=False, server_default=""
        ),
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("category.id"),
            nullable=True,
        ),
        sa.Column(
            "import_batch_id",
            sa.Integer,
            sa.ForeignKey("import_batch.id"),
            nullable=True,
        ),
        sa.Column("dedupe_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_transaction_dedupe_hash", "transaction", ["dedupe_hash"]
    )

    op.create_table(
        "budget",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("category.id"),
            nullable=False,
        ),
        sa.Column("month", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.UniqueConstraint(
            "category_id", "month", name="uq_budget_category_month"
        ),
    )

    category_table = sa.table(
        "category",
        sa.column("name", sa.String),
        sa.column("kind", category_kind),
    )
    op.bulk_insert(
        category_table,
        [{"name": name, "kind": kind} for name, kind in SEED_CATEGORIES],
    )


def downgrade() -> None:
    op.drop_table("budget")
    op.drop_index("ix_transaction_dedupe_hash", table_name="transaction")
    op.drop_table("transaction")
    op.drop_table("import_batch")
    op.drop_table("category")
    op.drop_table("account")
    bind = op.get_bind()
    sa.Enum(name="category_kind").drop(bind, checkfirst=True)
    sa.Enum(name="account_type").drop(bind, checkfirst=True)
