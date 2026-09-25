"""Pydantic schemas for the transactions API. See account.py's note on why
these are kept separate from app/models/transaction.py.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_serializer,
    field_validator,
)

from app.schemas._money import Money, as_str, reject_float

# Same rule as AccountName (account.py), at the column's 255 characters: trimmed,
# non-empty, no control or zero-width characters (a NUL byte is a database error,
# a lone zero-width space an invisible description in the ledger).
Description = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
        pattern=r"^[^\x00-\x1f​-‍﻿]+$",
    ),
]


class TransactionCreate(BaseModel):
    """POST /api/transactions body. Only ever adds a normal entry — voiding is
    its own endpoint (POST /api/transactions/{id}/void), so `type` and
    `reverses_transaction_id` aren't client-settable here.

    `extra="forbid"`: a client sending `type="reversal"` (or a typo like
    `categoryId`) gets a 422, not a silent ignore that posts something other
    than what it asked for."""

    model_config = ConfigDict(extra="forbid")

    account_id: int
    category_id: int | None = None
    date: date
    amount: Money  # negative = money out, positive = money in; NUMERIC(14,2) rules, see _money.py
    description: Description

    _validate_amount = field_validator("amount", mode="before")(reject_float)

    @field_validator("amount")
    @classmethod
    def _non_zero(cls, v: Decimal) -> Decimal:
        # A zero row moves no money and can't be told apart from its own void.
        # Runs after Money has normalised the value, so "-0" and "0.00" are caught.
        if v == 0:
            raise ValueError("amount must not be zero")
        return v


class TransactionRead(BaseModel):
    """What every transactions endpoint returns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    date: date
    amount: Decimal
    description: str
    type: str
    reverses_transaction_id: int | None
    created_at: datetime

    _validate_amount = field_validator("amount", mode="before")(reject_float)
    _serialize_amount = field_serializer("amount")(as_str)
