"""Pydantic schemas for the CSV import API (S5). See account.py's note on why
these are kept separate from app/models/import_batch.py.

The upload itself is multipart (a file can't ride in a JSON body), so the column
mapping arrives as a JSON *string* form field and is validated with
`ImportMapping.model_validate_json` in the router, not by FastAPI's body parsing.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

# A header name as it appears in the file (headers are trimmed when the file is read).
ColumnName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ImportMapping(BaseModel):
    """Which file column holds what. Columns are named by header, not position, so a
    re-ordered export still maps the same way.

    `date_format` is REQUIRED and never guessed: 03/04/2026 is March 4th in one bank's
    export and April 3rd in another's, and a wrong guess silently files every row in
    the wrong month (and hashes it differently, so a later correct import would
    double it). `extra="forbid"` for the same reason as TransactionCreate: a typo like
    `dateColumn` is a 422, not a silently ignored key."""

    model_config = ConfigDict(extra="forbid")

    date_column: ColumnName
    amount_column: ColumnName
    description_column: ColumnName
    date_format: Literal["iso", "mdy", "dmy"]  # YYYY-MM-DD / MM/DD/YYYY / DD/MM/YYYY
    # For exports that print money out as positive (many credit-card statements):
    # every parsed amount is multiplied by -1 before anything else looks at it.
    invert_sign: bool = False

    @model_validator(mode="after")
    def _distinct_columns(self) -> "ImportMapping":
        # One column can't be both the date and the amount; mapping it twice is
        # always a mistake in the form, never a real file layout.
        columns = [self.date_column, self.amount_column, self.description_column]
        if len(set(columns)) != len(columns):
            raise ValueError("date, amount and description columns must be different")
        return self


class ImportPreview(BaseModel):
    """POST /api/imports/preview. Enough for the mapping form: the header names to
    pick from and a few rows to check the pick against. Nothing is written."""

    headers: list[str]
    rows: list[list[str]]  # the first few data rows, raw cell text, possibly ragged
    row_count: int  # data rows in the whole file (blank lines not counted)
    delimiter: str


class RejectedRow(BaseModel):
    line: int  # 1-based line in the uploaded file; the header is line 1
    reason: str


class ImportResult(BaseModel):
    """POST /api/imports. The counts are exact; `rejected` lists at most the first
    100 rejected rows so a wholly wrong mapping on a 5000-row file doesn't return a
    5000-entry error list. `rejected_count` says how many there really were."""

    batch_id: int
    imported_count: int
    skipped_count: int
    rejected_count: int
    rejected: list[RejectedRow]


class ImportBatchRead(BaseModel):
    """GET /api/imports — the import history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    account_id: int
    imported_count: int
    skipped_count: int
    rejected_count: int
    created_at: datetime
