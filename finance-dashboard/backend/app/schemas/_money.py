"""Shared money-field validation for Pydantic schemas (ADR-0005).

Every schema with a Decimal money field wires these two functions in rather
than each schema re-inventing its own float guard / string serializer. One
place to fix if the rule ever changes.
"""

from decimal import Decimal


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
