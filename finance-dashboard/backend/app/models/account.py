from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    cash = "cash"


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    starting_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0")
    )
    archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
