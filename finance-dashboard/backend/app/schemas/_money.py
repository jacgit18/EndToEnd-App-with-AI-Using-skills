"""Shared money-field validation for Pydantic schemas (ADR-0005).

Every schema with a Decimal money field uses these rather than re-inventing its
own guard: `reject_float` and `as_str` (the float ban and string serializer) and
the `Money` type for money that *comes in* (the NUMERIC(14,2) rules). One place to
fix if the rule ever changes.
"""

import re
from decimal import Decimal
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field, WithJsonSchema


def reject_float(v: object) -> object:
    """A `field_validator(..., mode="before")` — runs on the raw input before
    Pydantic coerces it. Refuses a JSON *number with a decimal point* (which
    Python's JSON parser hands FastAPI as a `float`); a JSON string or a bare
    integer is fine. This is ADR-0005's "money enters as a string" rule,
    enforced at the API boundary rather than just hoped for.
    """
    if isinstance(v, float):
        raise ValueError(
            "money fields must be a JSON string or integer, not a float — "
            "floats lose precision (ADR-0005)"
        )
    return v


def as_str(v: Decimal) -> str:
    """A `field_serializer` — how a Decimal leaves the API as JSON. `str()` on
    a Decimal prints the exact stored value; letting the JSON encoder handle
    it directly would emit a bare number, and JSON numbers are floats."""
    return str(v)


# A plain decimal in ASCII: optional minus, up to 12 integer digits, up to 2 after the
# point. Rejects the forms Decimal() would happily parse but that mean nothing to a
# client: exponents ("1E+3"), padding (" 5 "), "+5", "5.", "1_000", non-ASCII digits.
_MONEY_RE = re.compile(r"-?[0-9]{1,12}(\.[0-9]{1,2})?")


def _plain_money(v: Any) -> Any:
    if isinstance(v, str) and not _MONEY_RE.fullmatch(v):
        raise ValueError("money must look like 1234.56 (plain digits, at most 2 decimals)")
    return v


# NUMERIC(14,2) holds |value| < 10**12. Pydantic's max_digits=14 counts ALL digits, so
# a 13-14 digit integer (10000000000000, or Decimal("1E+13")) passes it; strings are
# stopped earlier by _MONEY_RE's {1,12}, but ints/Decimals are not. Checked here, AFTER
# quantizing, so a value that rounds up across the limit is caught too.
_MONEY_LIMIT = Decimal(10) ** 12


def _two_places(v: Decimal) -> Decimal:
    # Always store/return the canonical 2dp form, and turn -0 into 0: a handler that
    # doesn't re-read the row after saving would otherwise echo "-0.00" or "0E-10".
    q = v.quantize(Decimal("0.01")) + Decimal("0.00")
    if abs(q) >= _MONEY_LIMIT:
        raise ValueError("money must have at most 12 digits before the decimal point")
    return q


# NUMERIC(14,2) as an API rule: max 14 digits, 2 after the point, no NaN/Infinity.
# Enforced here so a bad amount is a clean 422, not a database error (500) or a
# silently rounded value ("1.005" -> "1.01"). Negative is allowed on purpose: amounts
# are signed (negative = money out), so a credit card can start in debt.
# WithJsonSchema: the OpenAPI doc must say "string", because a JSON number with a
# decimal point is refused (reject_float) and the generated TS client reads this.
Money = Annotated[
    Decimal,
    BeforeValidator(_plain_money),
    Field(max_digits=14, decimal_places=2, allow_inf_nan=False),
    AfterValidator(_two_places),
    WithJsonSchema({"type": "string", "pattern": r"^-?\d{1,12}(\.\d{1,2})?$"}),
]
