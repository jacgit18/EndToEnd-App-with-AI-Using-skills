"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-13

Creates the full data model in one migration (spec Phase 0): accounts,
categories, budgets, import_batches, sessions, and the append-only
transactions ledger — plus ~15 seed categories. Endpoints only cover
accounts + transactions in Phase 0; the rest of the schema ships now so
later phases add behaviour, not schema churn.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="expense"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.UniqueConstraint("category_id", "month", name="uq_budget_category_month"),
    )

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("type", sa.String(16), nullable=False, server_default="normal"),
        sa.Column(
            "reverses_transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column(
            "import_batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("account_id", "content_hash", name="uq_transaction_account_hash"),
        sa.CheckConstraint(
            "type in ('normal', 'reversal', 'adjustment')", name="ck_transaction_type"
        ),
    )

    # Seed categories via a bare `sa.table`, not the ORM `Category` class — a
    # migration must stay runnable exactly as written even after the model
    # class changes shape later. Reaching for `app.models.Category` here would
    # quietly break this migration the day that class gains a new required
    # column with no default.
    categories_table = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("kind", sa.String),
    )
    op.bulk_insert(
        categories_table,
        [
            {"name": "Salary", "kind": "income"},
            {"name": "Interest", "kind": "income"},
            {"name": "Other Income", "kind": "income"},
            {"name": "Groceries", "kind": "expense"},
            {"name": "Rent/Mortgage", "kind": "expense"},
            {"name": "Utilities", "kind": "expense"},
            {"name": "Transportation", "kind": "expense"},
            {"name": "Dining Out", "kind": "expense"},
            {"name": "Entertainment", "kind": "expense"},
            {"name": "Healthcare", "kind": "expense"},
            {"name": "Insurance", "kind": "expense"},
            {"name": "Subscriptions", "kind": "expense"},
            {"name": "Shopping", "kind": "expense"},
            {"name": "Travel", "kind": "expense"},
            {"name": "Miscellaneous", "kind": "expense"},
        ],
    )


def downgrade() -> None:
    # Reverse order — a table can't be dropped while another still references it.
    op.drop_table("transactions")
    op.drop_table("sessions")
    op.drop_table("import_batches")
    op.drop_table("budgets")
    op.drop_table("categories")
    op.drop_table("accounts")
