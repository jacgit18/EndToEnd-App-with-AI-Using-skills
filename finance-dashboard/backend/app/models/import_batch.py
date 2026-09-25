"""ImportBatch — one CSV upload and what it did."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))

    # The account the file was imported into (migration 0005). One file, one
    # account (S5: multiple accounts in one file is out of scope).
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))

    # How many CSV rows became transactions, how many were skipped as duplicates
    # by the content-hash dedupe (ADR-0005), and how many were rejected as
    # unparseable (bad date, blank description, ...). The three add up to the
    # file's data rows. A batch is written even when all three leave nothing
    # imported: the history should show that the file was tried.
    imported_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    rejected_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
