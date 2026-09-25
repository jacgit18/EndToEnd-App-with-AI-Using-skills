"""Pydantic schemas for the dashboard API (spec S7, docs/phase7-spec.md). Read-only:
nothing here is ever an input, so money fields only need the string serializer."""

from decimal import Decimal

from pydantic import BaseModel, field_serializer

from app.schemas._money import as_str
from app.schemas.transaction import TransactionRead


class DashboardCategory(BaseModel):
    """One row of the category chart. `actual` is spend (positive = money out, a
    refund can push it below zero). `budget` is None when the category has no budget
    row that month ("no budget", not zero). `category_id` is None for the
    Uncategorized line."""

    category_id: int | None
    name: str
    actual: Decimal
    budget: Decimal | None

    _serialize_actual = field_serializer("actual")(as_str)

    @field_serializer("budget")
    def _serialize_budget(self, v: Decimal | None) -> str | None:
        return None if v is None else str(v)


class Dashboard(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    net: Decimal
    categories: list[DashboardCategory]
    recent: list[TransactionRead]

    _serialize_income = field_serializer("income")(as_str)
    _serialize_expense = field_serializer("expense")(as_str)
    _serialize_net = field_serializer("net")(as_str)
