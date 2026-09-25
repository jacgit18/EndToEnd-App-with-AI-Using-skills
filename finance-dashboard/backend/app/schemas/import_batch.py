"""Pydantic schemas for the CSV import API (S5). See account.py's note on why
these are kept separate from app/models/import_batch.py.

The upload itself is multipart (a file can't ride in a JSON body), so the column
mapping arrives as a JSON *string* form field and is validated with
`ImportMapping.model_validate_json` in the router, not by FastAPI's body parsing.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# A header name as it appears in the file (headers are trimmed when the file is read).
ColumnName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# An account id in `account_map`. Strict: JSON `"3"` or `true` is a 422, not quietly
# turned into account 3 or account 1 (a mis-typed id would file money in the wrong
# account). gt=0 because ids start at 1.
AccountId = Annotated[int, Field(strict=True, gt=0)]

# Upper bound on `account_map` entries. Each distinct non-null id is one row lock,
# so the map has to be bounded; the preview only ever offers <= 50 values per
# column, so 500 leaves room without allowing an unbounded lock loop.
ACCOUNT_MAP_MAX = 500


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

    # Per-row account mode (one file, many accounts — e.g. an export with an
    # "Account Name" column). Both present, or both absent (single-account mode,
    # where the form field `account_id` names the one account instead).
    #
    # `account_map` is CSV cell value -> account id, or null = leave those rows out
    # of the import entirely ("excluded": not imported, not rejected, not skipped).
    # Matching is EXACT and CASE-SENSITIVE against the cell with leading/trailing
    # whitespace trimmed (str.strip(), the same trim every other cell and every
    # header gets). So the keys must already be trimmed and non-blank: an untrimmed
    # key could never match, and "Card" and "Card " both present would be two keys
    # for one value. A row whose value is not a key is REJECTED, never guessed at.
    account_column: ColumnName | None = None
    account_map: dict[str, AccountId | None] | None = Field(
        default=None, max_length=ACCOUNT_MAP_MAX
    )

    @model_validator(mode="after")
    def _distinct_columns(self) -> "ImportMapping":
        # One column can't be both the date and the amount; mapping it twice is
        # always a mistake in the form, never a real file layout.
        columns = [self.date_column, self.amount_column, self.description_column]
        if len(set(columns)) != len(columns):
            raise ValueError("date, amount and description columns must be different")
        if self.account_column is not None and self.account_column in columns:
            raise ValueError("account column must differ from the date, amount and description columns")
        return self

    @model_validator(mode="after")
    def _account_mode(self) -> "ImportMapping":
        if (self.account_column is None) != (self.account_map is None):
            raise ValueError("account_column and account_map must be given together")
        if self.account_map is not None:
            for key in self.account_map:
                if not key or key != key.strip():
                    # Not echoed: the key is a cell value, i.e. the user's data.
                    raise ValueError("account_map keys must be non-blank and trimmed")
            if all(v is None for v in self.account_map.values()):
                # Every row would be excluded: nothing could ever be imported.
                raise ValueError("account_map must map at least one value to an account")
        return self

    @property
    def multi_account(self) -> bool:
        return self.account_column is not None


class ImportPreview(BaseModel):
    """POST /api/imports/preview. Enough for the mapping form: the header names to
    pick from and a few rows to check the pick against. Nothing is written."""

    headers: list[str]
    rows: list[list[str]]  # the first few data rows, raw cell text, possibly ragged
    row_count: int  # data rows in the whole file (blank lines not counted)
    delimiter: str
    # For picking an account column and building `account_map`: header -> its
    # distinct non-blank (trimmed) values over the WHOLE file, most frequent first,
    # ties alphabetical, each cut to 200 characters. A column with more than 50
    # distinct values (dates, amounts, descriptions) is left out: it isn't an
    # account column, and listing it would only bloat the response.
    distinct_values: dict[str, list[str]]


class RejectedRow(BaseModel):
    line: int  # 1-based line in the uploaded file; the header is line 1
    reason: str


class ImportResultBatch(BaseModel):
    """One ImportBatch written by the request: one per account the file touched."""

    batch_id: int
    account_id: int
    imported_count: int
    skipped_count: int
    # Rows rejected while parsing that could be attributed to this account (the
    # account cell was readable and mapped to it; in single-account mode, every
    # rejected row). Rows rejected because their account value isn't in the map,
    # or because the row is too short to reach the account column, belong to no
    # account: they're in the top-level `rejected_count` only.
    rejected_count: int


class ImportResult(BaseModel):
    """POST /api/imports. The counts are exact; `rejected` lists at most the first
    100 rejected rows so a wholly wrong mapping on a 5000-row file doesn't return a
    5000-entry error list. `rejected_count` says how many there really were.

    Top-level counts are totals over the whole file, and
    imported + skipped + rejected + excluded == the file's data rows.
    `batch_id` is the first entry of `batches` (the lowest account id), so a
    single-account client reads the response exactly as before; `batches` has
    exactly one entry in single-account mode."""

    batch_id: int
    imported_count: int
    skipped_count: int
    rejected_count: int
    rejected: list[RejectedRow]
    excluded_count: int  # rows whose account value maps to null; always 0 in single mode
    batches: list[ImportResultBatch]


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
