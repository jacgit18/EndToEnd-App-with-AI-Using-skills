"""Money round-trips as NUMERIC(14,2) <-> Decimal <-> JSON string (ADR-0005).

Pure unit tests: no database, no running server — these exercise the schema
layer (app/schemas/_money.py) directly, so they run in milliseconds and can't
be skipped for lack of a Postgres connection.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.account import AccountRead
from app.schemas.transaction import TransactionCreate, TransactionRead


def test_transaction_create_rejects_a_float_amount():
    """The core guard: a raw Python float must never become a Decimal amount."""
    with pytest.raises(ValidationError):
        TransactionCreate(
            account_id=1,
            date="2026-01-01",
            amount=12.50,  # a real float — this is what the guard exists for
            description="rejected",
        )


def test_transaction_create_accepts_a_string_amount():
    txn = TransactionCreate(
        account_id=1, date="2026-01-01", amount="12.50", description="groceries"
    )
    assert txn.amount == Decimal("12.50")
    assert isinstance(txn.amount, Decimal)


def test_transaction_create_accepts_a_bare_integer_amount():
    txn = TransactionCreate(account_id=1, date="2026-01-01", amount=12, description="round number")
    assert txn.amount == Decimal("12")


def test_transaction_read_serializes_amount_as_a_json_string():
    txn = TransactionRead(
        id=1,
        account_id=1,
        category_id=None,
        date="2026-01-01",
        amount=Decimal("12.50"),
        description="groceries",
        type="normal",
        reverses_transaction_id=None,
        created_at="2026-01-01T00:00:00Z",
    )
    dumped = txn.model_dump(mode="json")
    assert dumped["amount"] == "12.50"
    assert isinstance(dumped["amount"], str)  # never a bare JSON number


def test_account_read_rejects_a_float_balance():
    with pytest.raises(ValidationError):
        AccountRead(
            id=1,
            name="Checking",
            type="checking",
            starting_balance="0.00",  # every other field valid, so ONLY the float can fail this
            balance=100.0,  # a real float
            is_archived=False,
            created_at="2026-01-01T00:00:00Z",
        )


def txn(amount):
    return TransactionCreate(
        account_id=1, date="2026-01-01", amount=amount, description="x"
    )


@pytest.mark.parametrize(
    "bad",
    [
        "1.005",  # 3 decimals: the database would silently round it
        "99999999999999999999.99",  # too many digits for NUMERIC(14,2): a 500 at the database
        "1E+3",  # exponent form parses as a Decimal but is not a plain amount
        "NaN",
        " 5 ",
        "1_000",
        "\u0661\u0662",  # Arabic-Indic digits
    ],
)
def test_transaction_amount_rejects_values_the_column_cannot_hold(bad):
    with pytest.raises(ValidationError):
        txn(bad)


def test_transaction_amount_limits_also_hold_for_non_string_input():
    """A JSON integer or a Decimal object skips the plain-string regex, so the
    Field(max_digits, decimal_places) limits are what stop these."""
    from decimal import Decimal

    with pytest.raises(ValidationError):
        txn(10**14)  # 15 digits as a JSON integer
    with pytest.raises(ValidationError):
        txn(Decimal("1.005"))  # 3 decimals as a Decimal


def test_transaction_amount_is_normalised_to_two_places():
    assert str(txn("12.5").amount) == "12.50"
    assert str(txn(7).amount) == "7.00"
    # "-0" -> "0.00" used to be checked on a transaction amount; since S4 a zero
    # amount is refused there (test_transaction_amount_rejects_zero), so the -0
    # normalisation is checked on starting_balance, which shares the Money type.
    from app.schemas.account import AccountCreate

    assert str(AccountCreate(name="x", type="cash", starting_balance="-0").starting_balance) == "0.00"


@pytest.mark.parametrize("zero", ["0", "0.00", "-0", "-0.00", 0, Decimal("0")])
def test_transaction_amount_rejects_zero(zero):
    # S4: a zero row moves no money and can't be told apart from its own void.
    with pytest.raises(ValidationError):
        txn(zero)


def test_transaction_amount_accepts_the_column_limits():
    assert str(txn("999999999999.99").amount) == "999999999999.99"
    assert str(txn("-999999999999.99").amount) == "-999999999999.99"


def test_largest_valid_amount_is_accepted_in_every_input_form():
    assert str(txn("999999999999.99").amount) == "999999999999.99"
    assert str(txn(Decimal("999999999999.99")).amount) == "999999999999.99"
    assert str(txn(999999999999).amount) == "999999999999.00"
    assert str(txn(-999999999999).amount) == "-999999999999.00"


@pytest.mark.parametrize(
    "bad",
    [
        10**12,  # 13 integer digits as a JSON integer
        10**13,  # 14 digits: fits max_digits=14 but not NUMERIC(14,2)
        -(10**13),
        99999999999999,
        "1000000000000",  # the same values as strings
        "10000000000000",
        "-10000000000000",
        Decimal("1E+13"),  # exponent-form Decimal object, 1 significant digit
        Decimal("10000000000000.00"),
        Decimal("999999999999.995"),  # would round UP across the limit
        "999999999999.995",
        "9999999999999.996",  # rounds up to 14 integer digits
        Decimal("9999999999999.996"),
    ],
)
def test_amount_over_12_integer_digits_is_rejected_whatever_the_input_type(bad):
    """NUMERIC(14,2) holds |x| < 10**12. Every form must be a ValidationError (422),
    never a value that reaches the database and overflows (500)."""
    with pytest.raises(ValidationError):
        txn(bad)


def test_account_create_starting_balance_has_the_same_limit():
    from app.schemas.account import AccountCreate

    for bad in (10**13, "10000000000000", 10**12):
        with pytest.raises(ValidationError):
            AccountCreate(name="x", type="cash", starting_balance=bad)
    ok = AccountCreate(name="x", type="cash", starting_balance=999999999999)
    assert str(ok.starting_balance) == "999999999999.00"


def test_account_read_rejects_a_float_starting_balance():
    with pytest.raises(ValidationError):
        AccountRead(
            id=1, name="c", type="checking", starting_balance=5.5, balance="0.00",
            is_archived=False, created_at="2026-01-01T00:00:00Z",
        )


def test_decimal_avoids_the_classic_float_rounding_trap():
    """The reason any of this matters: 0.1 + 0.2 != 0.3 in binary floating
    point (try it: float(0.1) + float(0.2) == 0.30000000000000004). Decimal,
    built from strings/ints — never from a float — doesn't have this problem."""
    assert Decimal("0.10") + Decimal("0.20") == Decimal("0.30")
