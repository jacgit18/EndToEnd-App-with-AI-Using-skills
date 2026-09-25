"""Transaction — one row on the append-only ledger (ADR-0005).

Rows are never edited or deleted. A correction is a second row that reverses
the first (`type="reversal"`, `reverses_transaction_id` pointing back at it).
The account's `balance` column (account.py) is a cached, maintained total —
this table is the source of truth it's checked against.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # The CSV-import dedupe key (ADR-0005): a hash of date + amount +
        # normalized description, unique per account. A second import of the
        # same bank export can't double-insert a row.
        UniqueConstraint("account_id", "content_hash", name="uq_transaction_account_hash"),
        CheckConstraint(
            "type in ('normal', 'reversal', 'adjustment')", name="ck_transaction_type"
        ),
        # Mirror migration 0004 (same names) so Alembic autogenerate sees no drift.
        # A row can be voided at most once: the second reversal of the same row is
        # refused by the database even if two voids race past the router's pre-check.
        # Partial, so the NULL on every ordinary row stays out of the index.
        Index(
            "uq_transaction_one_reversal",
            "reverses_transaction_id",
            unique=True,
            postgresql_where=text("reverses_transaction_id IS NOT NULL"),
        ),
        # A reversal always names the row it reverses, and nothing else does.
        CheckConstraint(
            "(type = 'reversal') = (reverses_transaction_id IS NOT NULL)",
            name="ck_transaction_reversal_link",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    # The bank's transaction date (not when this row was inserted) — a plain
    # calendar date, not a timestamp; see the deferred date/timezone policy.
    date: Mapped[date] = mapped_column(Date)

    # Signed: negative = money out, positive = money in. Always Decimal,
    # never float (ADR-0005) — this is the number the balance column sums.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str] = mapped_column(String(255))

    # "normal" = an ordinary entry. "reversal" = voids an earlier row; carries
    # `reverses_transaction_id`. "adjustment" = a manual correction that isn't
    # voiding anything in particular (e.g. a reconciliation fix). S4 only
    # produces normal + reversal; adjustment exists for the reconciliation job.
    type: Mapped[str] = mapped_column(String(16), default="normal")

    # Self-referencing FK: a reversal row points at the transaction it voids.
    # Null on every ordinary row.
    reverses_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id")
    )

    # CSV dedupe (ADR-0005): sha256(date_iso|amount_2dp|normalized description).
    # Null for transactions entered by hand; only CSV-imported rows are hashed.
    content_hash: Mapped[str | None] = mapped_column(String(64))
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))

    # When this row was written — an audit fact, distinct from `date` above.
    # Always UTC; this is why it's timestamptz and `date` above is a plain DATE.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # No `updated_at` — nothing on this table is ever updated in place. That
    # absence is deliberate: it's the append-only rule, visible in the schema.
