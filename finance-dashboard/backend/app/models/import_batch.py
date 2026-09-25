"""ImportBatch — one CSV upload and what it did."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))

    # The account the rows were imported into (migration 0005). A multi-account
    # file (mapping with account_column/account_map) writes one batch PER account
    # it touched, all in one DB transaction, so this stays a single column.
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))

    # How many CSV rows became transactions, how many were skipped as duplicates
    # by the content-hash dedupe (ADR-0005), and how many were rejected as
    # unparseable (bad date, blank description, ...). In single-account mode the
    # three add up to the file's data rows; in multi-account mode, to the rows
    # attributed to this account (rows with an unmapped account value, and rows
    # mapped to "exclude", belong to no batch). A batch is written even when all
    # three leave nothing imported: the history should show that the file was tried.
    imported_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    rejected_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
