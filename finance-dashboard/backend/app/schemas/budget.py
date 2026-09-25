"""Pydantic schemas for the budgets API (spec S6). Kept separate from
app/models/budget.py for the reason given in account.py.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from app.schemas._money import Money, as_str, reject_float

# "YYYY-MM", month 01-12. The same string the dashboard will take as ?month=, and
# the exact form stored in budgets.month. Checked by pattern rather than parsed to a
# date so what the client sent is what gets stored: "2026-9" and "2026-09-01" are
# 422s, not silently reshaped into a key that a later lookup would miss.
MONTH_PATTERN = r"^[1-9][0-9]{3}-(0[1-9]|1[0-2])$"
Month = Annotated[str, Field(pattern=MONTH_PATTERN)]


class BudgetSet(BaseModel):
    """PUT /api/budgets/{month}/{category_id} body. The month and category come
    from the path; the body is only the amount, so a client can't disagree with
    its own URL. `extra="forbid"` turns a typo (`ammount`) into a 422."""

    model_config = ConfigDict(extra="forbid")

    amount: Money  # NUMERIC(14,2) rules, see _money.py

    _validate_amount = field_validator("amount", mode="before")(reject_float)

    @field_validator("amount")
    @classmethod
    def _positive(cls, v: Decimal) -> Decimal:
        # A budget is a planned spend. Zero or negative isn't one; "no budget" is
        # the absence of a row (DELETE), not a zero row. Runs after Money has
        # normalised the value, so "-0" and "0.00" are caught.
        if v <= 0:
            raise ValueError("amount must be greater than zero")
        return v


class BudgetRead(BaseModel):
    """What the budgets endpoints return."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    month: str
    amount: Decimal

    _validate_amount = field_validator("amount", mode="before")(reject_float)
    _serialize_amount = field_serializer("amount")(as_str)


class CopyForwardResult(BaseModel):
    """POST /api/budgets/{month}/copy-forward response: how many rows were
    copied, and how many were skipped because the target month already had a
    budget for that category or the category is archived."""

    copied: int
    skipped: int
