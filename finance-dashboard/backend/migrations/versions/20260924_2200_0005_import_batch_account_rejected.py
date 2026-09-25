"""import batch account and rejected count

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24

Phase 5 (S5, CSV import). 0001 shipped `import_batches` ahead of the feature; the
import flow needs two more facts on it:

1. `account_id` INTEGER NOT NULL, FK accounts.id. Which account the file was
   imported into — the history list shows it, and it's the account every row of
   the batch posts to. NOT NULL with no default and no backfill: nothing has
   ever written this table (0 rows in the dev DB, verified before writing this;
   the import endpoint is what this phase adds). If some database does hold a
   batch, Postgres refuses to add a NOT NULL column without a value and the
   migration fails loudly and rolls back, rather than inventing an account.

2. `rejected_count` INTEGER NOT NULL, server default 0. Rows the importer
   couldn't parse (bad date, blank description, ...). Alongside the existing
   imported_count / skipped_count, the three add up to the file's data rows.
   A default of 0 is right for any batch that predates it.

Downgrade drops both columns. The account link and rejected counts of any
batches made since are lost; the transactions themselves are not touched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "import_batches",
        sa.Column("account_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "import_batches_account_id_fkey",
        "import_batches",
        "accounts",
        ["account_id"],
        ["id"],
    )
    op.add_column(
        "import_batches",
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("import_batches", "rejected_count")
    op.drop_constraint("import_batches_account_id_fkey", "import_batches", type_="foreignkey")
    op.drop_column("import_batches", "account_id")
