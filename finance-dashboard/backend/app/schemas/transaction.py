"""Pydantic schemas for the transactions API. See account.py's note on why
these are kept separate from app/models/transaction.py.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.schemas._money import as_str, reject_float


class TransactionCreate(BaseModel):
    """POST /api/transactions body. Phase 0 only adds a normal entry — voiding
    (a reversal row) is Phase 4 (S4), so `type` isn't client-settable here."""

    account_id: int
    category_id: int | None = None
    date: date
    amount: Decimal  # negative = money out, positive = money in
    description: str

    _validate_amount = field_validator("amount", mode="before")(reject_float)


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
