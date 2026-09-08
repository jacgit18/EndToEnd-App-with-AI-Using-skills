from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    currency: str = "USD"
    starting_balance: Decimal = Field(
        default=Decimal("0"), max_digits=14, decimal_places=2
    )


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived: bool
