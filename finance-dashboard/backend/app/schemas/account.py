"""Pydantic schemas for the accounts API.

Deliberately separate from app/models/account.py: the ORM model is the table;
these are what the API accepts and returns, and they diverge on purpose — e.g.
a client can never set `balance` (it's maintained by the server, ADR-0005), so
no input schema has that field.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StringConstraints,
    field_serializer,
    field_validator,
    model_validator,
)

from app.models.account import ACCOUNT_TYPES
from app.schemas._money import Money, as_str, reject_float

# Written out (not built from ACCOUNT_TYPES) so type checkers can read it; the assert
# is the drift guard against the database CHECK's list in app/models/account.py.
AccountType = Literal["checking", "savings", "credit_card", "cash"]
assert get_args(AccountType) == ACCOUNT_TYPES, "AccountType and ACCOUNT_TYPES disagree"

# Trimmed, non-empty, at most the column's 120 characters, and no control characters
# or zero-width characters (a NUL byte would be a database error, a lone zero-width
# space an invisible name).
AccountName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=120,
        pattern=r"^[^\x00-\x1f\u200b-\u200d\ufeff]+$",
    ),
]


class AccountCreate(BaseModel):
    """POST /api/accounts body. No id and no `balance`: the database assigns the
    id, and the router sets balance = starting_balance (ADR-0005's invariant
    balance == starting_balance + SUM(transactions) starts out true).

    `extra="forbid"`: a client sending `balance` (or a typo like `startingBalance`) gets
    a 422, not a silent ignore that would create an account with a different opening
    balance than the client thought it asked for."""

    model_config = ConfigDict(extra="forbid")

    name: AccountName
    type: AccountType
    starting_balance: Money = Decimal("0.00")

    _validate_starting_balance = field_validator("starting_balance", mode="before")(
        reject_float
    )


class AccountUpdate(BaseModel):
    """PATCH /api/accounts/{id} body — every field optional, send only what changes.

    `extra="forbid"` is load-bearing: without it, a client sending `balance` (or
    any typo) would be silently ignored instead of rejected. `balance` must not
    be settable — it's the server's maintained figure.
    """

    model_config = ConfigDict(extra="forbid")

    name: AccountName | None = None
    type: AccountType | None = None
    starting_balance: Money | None = None
    is_archived: StrictBool | None = None

    _validate_starting_balance = field_validator("starting_balance", mode="before")(
        reject_float
    )

    @model_validator(mode="after")
    def _at_least_one_real_field(self) -> "AccountUpdate":
        # "Omitted" and "explicitly null" are different in PATCH; here null is never
        # meaningful (no field is nullable in the table), so reject it rather than
        # let it mean "leave alone" or, worse, "clear".
        sent = self.model_fields_set
        if not sent:
            raise ValueError("send at least one field to change")
        nulls = [f for f in sent if getattr(self, f) is None]
        if nulls:
            raise ValueError(f"fields cannot be null: {', '.join(sorted(nulls))}")
        return self


class AccountRead(BaseModel):
    """What every accounts endpoint returns."""

    model_config = ConfigDict(from_attributes=True)  # build directly from an ORM Account

    id: int
    name: str
    type: AccountType
    starting_balance: Decimal
    balance: Decimal
    is_archived: bool
    created_at: datetime

    _validate_money = field_validator("starting_balance", "balance", mode="before")(
        reject_float
    )
    _serialize_money = field_serializer("starting_balance", "balance")(as_str)
