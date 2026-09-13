"""Pydantic schemas for the accounts API.

Deliberately separate from app/models/account.py: the ORM model is the table;
these are what the API accepts and returns. They will diverge — e.g.
`is_archived` exists on the model well before any endpoint lets a client set
it, and a future `AccountRead` might add a computed field the table doesn't have.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.schemas._money import as_str, reject_float


class AccountCreate(BaseModel):
    """POST /api/accounts body. No id, no balance — the database assigns the
    id and the model's column default starts balance at 0.00."""

    name: str


class AccountRead(BaseModel):
    """What every accounts endpoint returns."""

    model_config = ConfigDict(from_attributes=True)  # build directly from an ORM Account

    id: int
    name: str
    balance: Decimal
    is_archived: bool
    created_at: datetime

    _validate_balance = field_validator("balance", mode="before")(reject_float)
    _serialize_balance = field_serializer("balance")(as_str)
