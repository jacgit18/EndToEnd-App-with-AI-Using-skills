from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    account_id: int
    date: date
    # Negative = money out, positive = money in.
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    description: str = ""
    category_id: int | None = None


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
