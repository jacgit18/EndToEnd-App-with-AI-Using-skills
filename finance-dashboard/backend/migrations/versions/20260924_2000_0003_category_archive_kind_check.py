"""category archive flag and kind check

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-24

Phase 3 (S3). Categories become user-managed: create, rename, archive. There is
no delete — transactions keep pointing at their category forever, so a category
the owner no longer wants is archived (hidden from pickers, history kept), the
same rule S2 gave accounts.

1. `is_archived` BOOLEAN NOT NULL, server default false. Unlike 0002's columns
   this one has an obviously right value for every existing row (nothing was
   archived before archiving existed), so a server default does the backfill in
   one step and a row inserted without it is simply active.

2. CHECK `ck_categories_kind`: kind IN ('income', 'expense'). The column has
   been a free String(16) since 0001; only the seed wrote to it, and every
   seeded row is one of the two (verified against the dev DB before writing
   this). Now that the API writes it, the database refuses anything else too.
   A CHECK, not a Postgres ENUM, for the reason in 0002.

Downgrade drops both. Archived flags are lost (every category becomes visible
again); nothing else is.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORY_KINDS = ("income", "expense")


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    # Fails loudly (and the whole migration rolls back) if any row has another
    # kind, rather than silently rewriting data the owner entered.
    allowed = ", ".join(f"'{k}'" for k in CATEGORY_KINDS)
    op.create_check_constraint(
        "ck_categories_kind", "categories", f"kind IN ({allowed})"
    )


def downgrade() -> None:
    op.drop_constraint("ck_categories_kind", "categories", type_="check")
    op.drop_column("categories", "is_archived")
