"""CSV import parsing (S5) — pure functions, no database.

Everything that turns uploaded bytes into ledger-ready rows lives here, so it can be
unit-tested without Postgres (tests/test_importer.py). The router (routers/imports.py)
only reads the upload, calls these, and writes the result in one DB transaction.

Two kinds of failure, kept apart on purpose:
- The FILE or MAPPING is wrong (not UTF-8, too big, no data rows, a mapped column
  that isn't in the header) -> `ImportFileError`, and the whole request is a 422
  (413 for size) with nothing saved.
- One ROW is wrong (a bad date, a blank description) -> that row is rejected and
  reported with its line number; the rest of the file still imports. A bank export
  with one odd line shouldn't block the other 400.

Money never passes through float (ADR-0005): amount text is cleaned as a string,
then validated by the same `Money` type the transactions API uses.
"""

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import TypeAdapter, ValidationError

from app.schemas._money import Money
from app.schemas.import_batch import ImportMapping

MAX_FILE_BYTES = 2 * 1024 * 1024  # a year of a busy account is well under 1 MB
MAX_DATA_ROWS = 5000
PREVIEW_ROWS = 10
REJECTED_LIST_CAP = 100  # the count is always exact; only the list is capped

# Tried in this order; on a tie the earlier one wins (so a one-column file is ",").
DELIMITERS = (",", ";", "\t", "|")


class ImportFileError(ValueError):
    """The file or mapping as a whole is unusable. `status_code` is what the
    router answers with."""

    status_code = 422


class FileTooLarge(ImportFileError):
    status_code = 413


class RowError(ValueError):
    """One row can't be imported; the message is the reason shown to the user."""


# --------------------------------------------------------------------------- reading the file


@dataclass(frozen=True)
class CsvFile:
    headers: list[str]
    # (1-based line in the file where the record starts, raw cells). Blank lines are
    # dropped but still counted in line numbers, so "line 7" is line 7 in an editor.
    rows: list[tuple[int, list[str]]]
    delimiter: str


def decode(raw: bytes) -> str:
    """UTF-8 only. utf-8-sig drops the byte-order mark Excel puts at the start of a
    "CSV UTF-8" export; without that, the first header would be "\\ufeffDate" and
    never match the mapping. Anything else (Latin-1, UTF-16) is refused rather than
    guessed: a wrong guess turns "Café" into "CafÃ©" in every description, and the
    mangled text is what gets hashed."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ImportFileError("file must be UTF-8") from None


def _is_blank(cells: list[str]) -> bool:
    # A truly empty line, or a spreadsheet's trailing ",,,," row.
    return all(not c.strip() for c in cells)


def sniff_delimiter(text: str) -> str:
    """The candidate that splits the header record into the most fields. Parsed
    with the csv module (quote-aware), so a quoted "Amount, USD" header doesn't
    count its comma. Header-only on purpose: data rows can legitimately contain
    other candidates ("$1,234.50" in a semicolon file)."""
    best, best_count = DELIMITERS[0], 1
    for delimiter in DELIMITERS:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
        try:
            header = next((row for row in reader if not _is_blank(row)), [])
        except csv.Error:
            continue
        if len(header) > best_count:
            best, best_count = delimiter, len(header)
    return best


def read_csv(raw: bytes) -> CsvFile:
    """Bytes -> headers + data rows. Raises ImportFileError for anything that makes
    the file as a whole unusable. Ragged rows (more or fewer cells than the header)
    are kept as-is here; only the importer cares whether a row reaches its columns."""
    if len(raw) > MAX_FILE_BYTES:
        raise FileTooLarge(f"file is larger than {MAX_FILE_BYTES // (1024 * 1024)} MB")
    text = decode(raw)
    if not text.strip():
        raise ImportFileError("file is empty")

    delimiter = sniff_delimiter(text)
    # newline="": let the csv module see the raw line endings, so a quoted field
    # with an embedded newline stays one field (the csv docs require this).
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    headers: list[str] | None = None
    rows: list[tuple[int, list[str]]] = []
    previous_end = 0
    try:
        for cells in reader:
            start = previous_end + 1  # reader.line_num is where the record ENDS
            previous_end = reader.line_num
            if _is_blank(cells):
                continue
            if headers is None:
                headers = [h.strip() for h in cells]
                continue
            rows.append((start, cells))
            if len(rows) > MAX_DATA_ROWS:
                raise ImportFileError(f"file has more than {MAX_DATA_ROWS} data rows")
    except csv.Error as exc:  # e.g. one field over the csv module's 128 KiB limit
        raise ImportFileError(f"file is not valid CSV: {exc}") from None

    if not rows:
        raise ImportFileError("file has no data rows")
    return CsvFile(headers=headers, rows=rows, delimiter=delimiter)


# --------------------------------------------------------------------------- one cell at a time


_DATE_PATTERNS = {
    # ASCII digits only ([0-9], not \d). ISO is exact; the slash formats allow a
    # 1-digit month/day ("3/4/2026") because banks drop the zero, but the year is
    # always 4 digits: "03/04/26" could be 1926 or 2026, and that's a guess.
    "iso": (re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})"), ("y", "m", "d")),
    "mdy": (re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"), ("m", "d", "y")),
    "dmy": (re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"), ("d", "m", "y")),
}
_DATE_LABELS = {"iso": "YYYY-MM-DD", "mdy": "MM/DD/YYYY", "dmy": "DD/MM/YYYY"}


def parse_date(text: str, date_format: str) -> date:
    """Strict: the text must be exactly the chosen format and a real calendar day.
    02/30/2026 is rejected, never rolled over to March 2nd."""
    pattern, order = _DATE_PATTERNS[date_format]
    match = pattern.fullmatch(text.strip())
    if match is None:
        raise RowError(f"date is not {_DATE_LABELS[date_format]}")
    parts = dict(zip(order, (int(g) for g in match.groups())))
    try:
        return date(parts["y"], parts["m"], parts["d"])  # year 0, month 13, Feb 30 all raise
    except ValueError:
        raise RowError("date is not a real calendar day") from None


# Sign, currency and number, with optional spaces between them: "-12.50", "$12.50",
# "-$12.50", "$-12.50", "$ 1,234.50". The number part is checked further below.
_AMOUNT_RE = re.compile(r"(-)?\s*(\$)?\s*(-)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)")
_GROUPED_RE = re.compile(r"[0-9]{1,3}(,[0-9]{3})+")
_MONEY = TypeAdapter(Money)


def parse_amount(text: str) -> Decimal:
    """Bank-export money text -> a 2dp Decimal under the NUMERIC(14,2) rules.

    Tolerated: "$", thousands commas in correct groups, spaces around the sign or
    "$", and accounting negatives "(12.50)". Refused, not guessed:
    - more than 2 decimals ("1.234"): in a European export that's one thousand two
      hundred thirty-four, and rounding it to 1.23 would be off by 1000x, silently;
    - a comma that isn't a thousands separator ("1,50", "12,34,5"): same reason;
    - exponents ("1e3"), "+5", "12.50-", a sign inside the parentheses.
    Zero is not refused here; that's the caller's rule (after invert_sign)."""
    s = text.strip()
    if not s:
        raise RowError("amount is blank")
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative, s = True, s[1:-1].strip()
    match = _AMOUNT_RE.fullmatch(s)
    if match is None:
        raise RowError("amount is not a number")
    sign_before, _, sign_after, number = match.groups()
    if sign_before and sign_after:
        raise RowError("amount is not a number")  # "-$-5"
    if (sign_before or sign_after) and negative:
        raise RowError("amount is not a number")  # "(-12.50)": which sign is meant?
    negative = negative or bool(sign_before or sign_after)

    integer, _, fraction = number.partition(".")
    if "," in integer:
        if not _GROUPED_RE.fullmatch(integer):
            raise RowError("amount has a comma that isn't a thousands separator")
        integer = integer.replace(",", "")
    if len(fraction) > 2:
        raise RowError("amount has more than 2 decimal places")

    plain = ("-" if negative else "") + integer + (f".{fraction}" if fraction else "")
    try:
        # The transactions API's Money type: plain-decimal check, 12 integer digits
        # max, canonical 2dp, -0 -> 0. One rule for money in, whichever door it uses.
        return _MONEY.validate_python(plain)
    except ValidationError:
        raise RowError("amount is out of range") from None


# Same rule as schemas/transaction.py's Description: no control characters (a NUL
# is a database error) and no zero-width characters (an invisible description).
_BAD_CHARS = re.compile(r"[\x00-\x1f​-‍﻿]")
DESCRIPTION_MAX = 255  # transactions.description is VARCHAR(255)


def clean_description(text: str) -> str:
    """Trimmed; blank, over-long, or containing a control/zero-width character is a
    rejected row. Over-long is rejected, not truncated: two long descriptions that
    differ only after character 255 would truncate to the same text and dedupe as
    one transaction."""
    s = text.strip()
    if not s:
        raise RowError("description is blank")
    if len(s) > DESCRIPTION_MAX:
        raise RowError(f"description is longer than {DESCRIPTION_MAX} characters")
    if _BAD_CHARS.search(s):
        raise RowError("description contains a control or zero-width character")
    return s


# --------------------------------------------------------------------------- dedupe hash (ADR-0005)


def dedupe_key(day: date, amount: Decimal, description: str) -> str:
    """`date_iso|amount_2dp|normalized description` (ADR-0005).

    - date: the PARSED calendar date in ISO form, so the same transaction hashes the
      same whether the export printed it 03/04/2026 or 2026-03-04.
    - amount: the stored, signed, 2dp value (after invert_sign), so the hash always
      describes the row as it sits in the ledger.
    - description: casefolded and whitespace-collapsed, so a bank re-exporting
      "ACME  Corp" as "acme corp" doesn't double the row. Only the hash is
      normalized; the description is stored as the file had it (trimmed)."""
    normalized = " ".join(description.casefold().split())
    return f"{day.isoformat()}|{amount}|{normalized}"


def content_hash(key: str, occurrence: int) -> str:
    """sha256 of the key plus its occurrence index within the file.

    Two genuinely identical rows in one statement (two $3.50 coffees on the same
    day) share a key; without the index the second would be "skipped" as a
    duplicate of the first and silently lost. With it they hash as key|0 and key|1,
    both import, and re-importing the same file produces the same two hashes, so
    both are skipped. An overlapping export works too: a file holding that day's
    coffees again yields key|0 and key|1 again.

    Known gap: hand-entered transactions have a NULL hash, so importing a statement
    that contains a row already typed in by hand imports it a second time. Dedupe
    only protects imports from other imports."""
    return hashlib.sha256(f"{key}|{occurrence}".encode()).hexdigest()


# --------------------------------------------------------------------------- whole file


@dataclass(frozen=True)
class ParsedRow:
    line: int
    date: date
    amount: Decimal
    description: str
    content_hash: str


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    rejected: list[tuple[int, str]] = field(default_factory=list)  # (line, reason), all of them


def column_indexes(headers: list[str], mapping: ImportMapping) -> tuple[int, int, int]:
    """Where the mapped columns are. A missing or duplicated header name is a
    problem with the whole request, not with any one row -> ImportFileError."""
    indexes = []
    for name in (mapping.date_column, mapping.amount_column, mapping.description_column):
        found = [i for i, h in enumerate(headers) if h == name]
        if not found:
            raise ImportFileError(f"column {name!r} is not in the file's header")
        if len(found) > 1:
            raise ImportFileError(f"column {name!r} appears more than once in the header")
        indexes.append(found[0])
    return indexes[0], indexes[1], indexes[2]


def parse_rows(csv_file: CsvFile, mapping: ImportMapping) -> ParseResult:
    """Every data row -> a ParsedRow or a (line, reason) rejection. Never raises for
    a bad row; raises ImportFileError only if the mapping doesn't fit the header."""
    date_i, amount_i, desc_i = column_indexes(csv_file.headers, mapping)
    needed = max(date_i, amount_i, desc_i) + 1
    result = ParseResult()
    occurrences: dict[str, int] = {}

    for line, cells in csv_file.rows:
        try:
            if len(cells) < needed:
                raise RowError(f"row has {len(cells)} fields, the mapping needs {needed}")
            day = parse_date(cells[date_i], mapping.date_format)
            amount = parse_amount(cells[amount_i])
            if mapping.invert_sign:
                # Before the zero check and the hash: the hash must match the amount
                # that is actually stored. + 0.00 keeps it canonical (no "-0.00").
                amount = -amount + Decimal("0.00")
            if amount == 0:
                # Same rule as the API: a zero row moves no money and can't be told
                # apart from its own void.
                raise RowError("amount is zero")
            description = clean_description(cells[desc_i])
        except RowError as exc:
            result.rejected.append((line, str(exc)))
            continue

        key = dedupe_key(day, amount, description)
        occurrence = occurrences.get(key, 0)  # counted over accepted rows only
        occurrences[key] = occurrence + 1
        result.rows.append(
            ParsedRow(
                line=line,
                date=day,
                amount=amount,
                description=description,
                content_hash=content_hash(key, occurrence),
            )
        )
    return result
