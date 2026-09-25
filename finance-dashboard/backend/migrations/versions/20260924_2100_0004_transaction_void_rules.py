"""transaction void rules: one reversal per row, reversal link check

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-24

Phase 4 (S4). The ledger is append-only (ADR-0005): "delete" is a void, which
posts a reversal row pointing back at the original through
`reverses_transaction_id`. Two rules the router enforces are also made
database facts here, so a race or a future writer can't break them:

1. Partial UNIQUE INDEX `uq_transaction_one_reversal` on
   (reverses_transaction_id) WHERE reverses_transaction_id IS NOT NULL.
   A row can be voided at most once. The router pre-checks this, but two
   simultaneous voids can both pass a pre-check; the index is what makes the
   second insert fail, and the router turns that failure into a 409. Partial
   so the NULLs on every ordinary row stay out of the index entirely.

2. CHECK `ck_transaction_reversal_link`:
   (type = 'reversal') = (reverses_transaction_id IS NOT NULL).
   A reversal always says what it reverses, and nothing else carries the link.
   Every existing row is type 'normal' with a null link (verified against the
   dev DB before writing this), so it applies without a backfill. If some
   database does hold a violating row, the migration fails loudly and rolls
   back rather than rewriting ledger rows.

Downgrade drops both. No data is lost: both are rules, not columns.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_transaction_one_reversal",
        "transactions",
        ["reverses_transaction_id"],
        unique=True,
        postgresql_where=sa.text("reverses_transaction_id IS NOT NULL"),
    )
    op.create_check_constraint(
        "ck_transaction_reversal_link",
        "transactions",
        "(type = 'reversal') = (reverses_transaction_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_transaction_reversal_link", "transactions", type_="check")
    op.drop_index("uq_transaction_one_reversal", table_name="transactions")
