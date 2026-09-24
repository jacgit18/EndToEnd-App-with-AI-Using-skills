"""account type and starting balance

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-24

Phase 2 (S2). Adds the two account fields the spec has always required and
0001 left out: `type` (checking / savings / credit_card / cash) and
`starting_balance`.

The invariant ADR-0005 rests on is
    balance == starting_balance + SUM(transactions.amount)
Existing rows get starting_balance = 0.00, deliberately NOT derived from
balance - SUM(amount). Before this migration nothing could create a nonzero
starting balance (create set balance 0.00; only POST /transactions moved it),
so 0.00 is the true starting balance of every legacy row. Deriving it would be
wrong in the one case that matters: a row whose balance had already drifted
from its ledger would have that drift written into starting_balance, and the
reconciliation job could then never report it. With 0.00, drift stays visible.

Downgrade caveat: it drops both columns, so once the edit endpoint exists a
downgrade loses user-set types (re-upgrade resets every row to 'checking').
starting_balance survives round trips fine: the maintained balance already
includes it.

Order matters: add the columns nullable, backfill, then tighten to NOT NULL.
Adding NOT NULL first would fail on any table that already has rows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACCOUNT_TYPES = ("checking", "savings", "credit_card", "cash")


def upgrade() -> None:
    # 1. Add both columns nullable so existing rows are legal during the backfill.
    op.add_column("accounts", sa.Column("type", sa.String(20), nullable=True))
    op.add_column(
        "accounts", sa.Column("starting_balance", sa.Numeric(14, 2), nullable=True)
    )

    # 2. Backfill. Every pre-existing account becomes "checking" (the spec gave
    #    no type to infer from; the owner can edit it once the edit endpoint
    #    ships) with a 0.00 starting balance (see docstring for why it is not derived).
    op.execute("UPDATE accounts SET type = 'checking', starting_balance = 0.00")

    # 3. Tighten. No server default on either column: a row that omits them
    #    should fail at the database, not silently become "checking" / 0.
    op.alter_column("accounts", "type", nullable=False)
    op.alter_column("accounts", "starting_balance", nullable=False)

    # 4. A CHECK, not a Postgres ENUM: changing the allowed set later is a
    #    one-line constraint swap here, whereas ALTER TYPE ... ADD VALUE has
    #    transaction and removal restrictions.
    allowed = ", ".join(f"'{t}'" for t in ACCOUNT_TYPES)
    op.create_check_constraint("ck_accounts_type", "accounts", f"type IN ({allowed})")


def downgrade() -> None:
    op.drop_constraint("ck_accounts_type", "accounts", type_="check")
    op.drop_column("accounts", "starting_balance")
    op.drop_column("accounts", "type")
