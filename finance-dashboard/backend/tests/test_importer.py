"""CSV import parser (app/importer.py) — pure functions, no database.

Every CSV here is a synthetic string built in the test (real bank exports are
personal data and `*.csv` is gitignored). The API-level behaviour — batches,
balance, dedupe against the table — is tests/test_imports.py.
"""

from datetime import date
from decimal import Decimal

import pytest

from app import importer
from app.importer import ImportFileError, RowError
from app.schemas.import_batch import ImportMapping


def mapping(**overrides) -> ImportMapping:
    fields = {
        "date_column": "Date",
        "amount_column": "Amount",
        "description_column": "Description",
        "date_format": "iso",
    }
    fields.update(overrides)
    return ImportMapping(**fields)


def parse(text: str, **overrides) -> importer.ParseResult:
    return importer.parse_rows(importer.read_csv(text.encode()), mapping(**overrides))


# --------------------------------------------------------------------------- dates


@pytest.mark.parametrize(
    "text, fmt, expected",
    [
        ("2026-03-04", "iso", date(2026, 3, 4)),
        (" 2026-03-04 ", "iso", date(2026, 3, 4)),
        ("03/04/2026", "mdy", date(2026, 3, 4)),
        ("03/04/2026", "dmy", date(2026, 4, 3)),
        ("3/4/2026", "mdy", date(2026, 3, 4)),  # banks drop the leading zero
        ("12/31/2026", "mdy", date(2026, 12, 31)),
        ("31/12/2026", "dmy", date(2026, 12, 31)),
        ("02/29/2028", "mdy", date(2028, 2, 29)),  # leap year
    ],
)
def test_parse_date_accepts_the_chosen_format(text, fmt, expected):
    assert importer.parse_date(text, fmt) == expected


@pytest.mark.parametrize(
    "text, fmt",
    [
        ("02/30/2026", "mdy"),  # no rollover to March
        ("30/02/2026", "dmy"),
        ("02/29/2026", "mdy"),  # not a leap year
        ("13/01/2026", "mdy"),
        ("01/13/2026", "dmy"),
        ("2026-02-30", "iso"),
        ("2026-3-4", "iso"),  # ISO is exact
        ("03/04/26", "mdy"),  # 2-digit year: a guess
        ("2026-03-04", "mdy"),  # the wrong format is not guessed around
        ("03/04/2026", "iso"),
        ("0000-01-01", "iso"),
        ("2026/03/04", "iso"),
        ("٢٠٢٦-03-04", "iso"),  # non-ASCII digits
        ("", "iso"),
        ("2026-03-04T10:00", "iso"),
    ],
)
def test_parse_date_rejects_anything_else(text, fmt):
    with pytest.raises(RowError):
        importer.parse_date(text, fmt)


# --------------------------------------------------------------------------- amounts


@pytest.mark.parametrize(
    "text, expected",
    [
        ("12.50", "12.50"),
        ("-12.50", "-12.50"),
        ("12", "12.00"),
        ("12.5", "12.50"),
        ("(12.50)", "-12.50"),  # accounting negative
        ("( 12.50 )", "-12.50"),
        ("$1,234.50", "1234.50"),
        ("-$1,234.50", "-1234.50"),
        ("$-1,234.50", "-1234.50"),
        ("($1,234.50)", "-1234.50"),
        ("$ 12.50", "12.50"),
        ("  -12.50  ", "-12.50"),
        ("1,000,000.00", "1000000.00"),
        ("999999999999.99", "999999999999.99"),  # NUMERIC(14,2)'s largest
        ("0.00", "0.00"),  # zero parses; the ROW is rejected by parse_rows
    ],
)
def test_parse_amount_accepts_bank_formats(text, expected):
    value = importer.parse_amount(text)
    assert isinstance(value, Decimal)
    assert str(value) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "1.234",  # European thousands: refused, not rounded to 1.23
        "12.345",
        "1,50",  # European decimal comma
        "12,34,5",
        "1,2345.00",
        "1e3",
        "1E+3",
        "+12.50",
        "12.50-",
        "(-12.50)",
        "-(12.50)",
        "-$-12.50",
        "--12.50",
        "12.50.1",
        "$",
        "abc",
        "NaN",
        "Infinity",
        "１２.50",  # full-width digits
        "1000000000000.00",  # past NUMERIC(14,2)
        "€12.50",
        ".50",
    ],
)
def test_parse_amount_rejects_anything_else(text):
    with pytest.raises(RowError):
        importer.parse_amount(text)


def test_parse_amount_never_goes_through_float():
    # 0.1 + 0.2 style drift would show up here if a float were ever involved.
    assert importer.parse_amount("0.10") + importer.parse_amount("0.20") == Decimal("0.30")
    assert str(importer.parse_amount("123456789012.34")) == "123456789012.34"


# --------------------------------------------------------------------------- descriptions


@pytest.mark.parametrize(
    "text, reason",
    [
        ("", "blank"),
        ("   ", "blank"),
        ("a\x00b", "control"),
        ("tab\there", "control"),
        ("new\nline", "control"),
        ("zero​width", "control"),
        ("﻿bom", "control"),
        ("x" * 256, "longer"),
    ],
)
def test_clean_description_rejects(text, reason):
    with pytest.raises(RowError, match=reason):
        importer.clean_description(text)


def test_clean_description_trims_and_keeps_255():
    assert importer.clean_description("  Coffee  ") == "Coffee"
    assert importer.clean_description("x" * 255) == "x" * 255


# --------------------------------------------------------------------------- reading the file


def test_read_csv_basic_and_line_numbers():
    f = importer.read_csv(
        b"Date,Amount,Description\n2026-01-01,-1.00,A\n\n2026-01-02,-2.00,B\n"
    )
    assert f.headers == ["Date", "Amount", "Description"]
    assert f.delimiter == ","
    # The blank line is dropped but still counted: B is on line 4 of the file.
    assert f.rows == [(2, ["2026-01-01", "-1.00", "A"]), (4, ["2026-01-02", "-2.00", "B"])]


def test_read_csv_quoted_multiline_field_keeps_start_line():
    f = importer.read_csv(b'D,A,Desc\n2026-01-01,-1,"two\nlines"\n2026-01-02,-2,C\n')
    assert [line for line, _ in f.rows] == [2, 4]


def test_read_csv_accepts_a_bom_and_strips_header_whitespace():
    f = importer.read_csv("﻿ Date , Amount,Description\r\n2026-01-01,1,A\r\n".encode())
    assert f.headers == ["Date", "Amount", "Description"]


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_read_csv_sniffs_the_delimiter(delimiter):
    text = delimiter.join(["Date", "Amount", "Description"]) + "\n"
    text += delimiter.join(["2026-01-01", "-1.00", "A"]) + "\n"
    f = importer.read_csv(text.encode())
    assert f.delimiter == delimiter
    assert f.rows[0][1] == ["2026-01-01", "-1.00", "A"]


def test_semicolon_file_with_commas_in_amounts():
    f = importer.read_csv(b'Date;Amount;Description\n2026-01-01;"$1,234.50";Rent\n')
    assert f.delimiter == ";"
    result = importer.parse_rows(f, mapping())
    assert [r.amount for r in result.rows] == [Decimal("1234.50")]


def test_quoted_comma_in_header_does_not_fool_the_sniffer():
    f = importer.read_csv(b'"Amount, USD";Date;Description\n1;2026-01-01;A\n')
    assert f.delimiter == ";"
    assert f.headers == ["Amount, USD", "Date", "Description"]


def test_ragged_rows_are_kept_for_preview():
    f = importer.read_csv(b"Date,Amount,Description\n2026-01-01,-1\n2026-01-02,-2,B,extra\n")
    assert [cells for _, cells in f.rows] == [["2026-01-01", "-1"], ["2026-01-02", "-2", "B", "extra"]]


@pytest.mark.parametrize(
    "raw, message",
    [
        (b"", "empty"),
        (b"  \n\n", "empty"),
        (b"Date,Amount,Description\n", "no data rows"),
        (b"Date,Amount,Description\n\n,,\n", "no data rows"),
        ("Café".encode("latin-1") + b",1,2\n1,2,3\n", "UTF-8"),
        ("Date,Amount\n1,2\n".encode("utf-16"), "UTF-8"),
    ],
)
def test_read_csv_refuses_unusable_files(raw, message):
    with pytest.raises(ImportFileError, match=message) as exc:
        importer.read_csv(raw)
    assert exc.value.status_code == 422


def test_read_csv_size_and_row_limits():
    header = b"Date,Amount,Description\n"
    row = b"2026-01-01,-1.00,A\n"
    assert len(importer.read_csv(header + row * importer.MAX_DATA_ROWS).rows) == 5000
    with pytest.raises(ImportFileError, match="more than 5000"):
        importer.read_csv(header + row * (importer.MAX_DATA_ROWS + 1))

    # Exactly MAX_FILE_BYTES: ~1 KB rows (an extra padding column) so the row limit
    # isn't what trips, then one last row padded to land on the byte limit.
    padded = b"2026-01-01,-1.00,A," + b"x" * 980 + b"\n"
    body = header + padded * ((importer.MAX_FILE_BYTES - len(header)) // len(padded) - 1)
    tail = importer.MAX_FILE_BYTES - len(body) - len(b"2026-01-01,-1.00,A,\n")
    body += b"2026-01-01,-1.00,A," + b"x" * tail + b"\n"
    assert len(body) == importer.MAX_FILE_BYTES
    importer.read_csv(body)  # exactly at the limit: allowed
    with pytest.raises(importer.FileTooLarge) as exc:
        importer.read_csv(body + b"x")
    assert exc.value.status_code == 413


# --------------------------------------------------------------------------- mapping


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"date_column": "Posted"}, "not in the file"),
        ({"description_column": "date"}, "not in the file"),  # case-sensitive
    ],
)
def test_mapped_column_missing_from_header(overrides, message):
    with pytest.raises(ImportFileError, match=message):
        parse("Date,Amount,Description\n2026-01-01,1,A\n", **overrides)


def test_mapped_column_duplicated_in_header():
    with pytest.raises(ImportFileError, match="more than once"):
        parse("Date,Amount,Description,Amount\n2026-01-01,1,A,2\n")


@pytest.mark.parametrize(
    "fields",
    [
        {"date_column": "A", "amount_column": "A", "description_column": "C", "date_format": "iso"},
        {"date_column": "A", "amount_column": "B", "description_column": "C"},  # no date_format
        {"date_column": "A", "amount_column": "B", "description_column": "C", "date_format": "ymd"},
        {"date_column": "A", "amount_column": "B", "description_column": "C", "date_format": "iso",
         "extra": 1},
        {"date_column": "", "amount_column": "B", "description_column": "C", "date_format": "iso"},
    ],
)
def test_bad_mapping_is_refused(fields):
    with pytest.raises(ValueError):
        ImportMapping(**fields)


# --------------------------------------------------------------------------- whole-file parse


def test_parse_rows_rejects_bad_rows_with_line_numbers_and_keeps_the_rest():
    text = (
        "Date,Amount,Description\n"  # line 1
        "2026-01-01,-1.00,Good one\n"  # 2
        "2026-02-30,-1.00,Bad date\n"  # 3
        "2026-01-02,0.00,Zero\n"  # 4
        "2026-01-03,-1.00,   \n"  # 5
        "2026-01-04,1e3,Float-looking\n"  # 6
        "2026-01-05,-2.00\n"  # 7 ragged: no description cell
        "\n"  # 8 blank: not a row at all
        "2026-01-06,(12.50),Good two\n"  # 9
    )
    result = parse(text)
    assert [(r.line, r.amount, r.description) for r in result.rows] == [
        (2, Decimal("-1.00"), "Good one"),
        (9, Decimal("-12.50"), "Good two"),
    ]
    assert [line for line, _ in result.rejected] == [3, 4, 5, 6, 7]
    assert "zero" in result.rejected[1][1]


def test_description_is_stored_trimmed_but_not_normalized():
    result = parse("Date,Amount,Description\n2026-01-01,-1,  ACME   Corp  \n")
    assert result.rows[0].description == "ACME   Corp"


def test_invert_sign_happens_before_hash_and_zero_check():
    text = "Date,Amount,Description\n2026-01-01,12.50,Card spend\n2026-01-02,-0.00,Zero\n"
    plain = parse(text)
    inverted = parse(text, invert_sign=True)

    assert inverted.rows[0].amount == Decimal("-12.50")
    assert str(inverted.rows[0].amount) == "-12.50"
    # The hash describes the stored (inverted) amount...
    key = importer.dedupe_key(date(2026, 1, 1), Decimal("-12.50"), "Card spend")
    assert inverted.rows[0].content_hash == importer.content_hash(key, 0)
    assert inverted.rows[0].content_hash != plain.rows[0].content_hash
    # ...and -0 inverted is still zero, still rejected.
    assert [line for line, _ in inverted.rejected] == [3]


def test_dedupe_key_normalizes_only_for_hashing():
    a = importer.dedupe_key(date(2026, 1, 1), Decimal("-3.50"), "ACME  Corp")
    b = importer.dedupe_key(date(2026, 1, 1), Decimal("-3.50"), "acme corp")
    assert a == b == "2026-01-01|-3.50|acme corp"


def test_same_transaction_hashes_the_same_in_any_date_format():
    iso = parse("Date,Amount,Description\n2026-03-04,-1,A\n")
    mdy = parse("Date,Amount,Description\n03/04/2026,-1.00,a\n", date_format="mdy")
    assert iso.rows[0].content_hash == mdy.rows[0].content_hash


def test_identical_rows_in_one_file_get_distinct_hashes_and_repeat_on_reparse():
    text = (
        "Date,Amount,Description\n"
        "2026-01-01,-3.50,Coffee\n"
        "2026-01-01,-3.50,Coffee\n"
        "2026-01-01,-3.50,coffee\n"  # same key after normalization: third occurrence
        "2026-01-01,-4.00,Coffee\n"
    )
    first = [r.content_hash for r in parse(text).rows]
    again = [r.content_hash for r in parse(text).rows]

    assert len(set(first)) == 4  # every row distinct
    assert first == again  # same file -> same hashes (so a re-import skips them all)
    key = importer.dedupe_key(date(2026, 1, 1), Decimal("-3.50"), "coffee")
    assert first[:3] == [importer.content_hash(key, n) for n in range(3)]


def test_rejected_rows_do_not_consume_an_occurrence_index():
    good = "2026-01-01,-3.50,Coffee\n"
    with_bad = parse("Date,Amount,Description\n2026-01-01,oops,Coffee\n" + good)
    without = parse("Date,Amount,Description\n" + good)
    assert with_bad.rows[0].content_hash == without.rows[0].content_hash
