"""Pydantic schemas for the categories API. See account.py's note on why these
are kept separate from app/models/category.py.
"""

from datetime import datetime
from typing import Annotated, Literal, get_args

from pydantic import BaseModel, ConfigDict, StrictBool, StringConstraints, model_validator

from app.models.category import CATEGORY_KINDS

# Written out (not built from CATEGORY_KINDS) so type checkers can read it; the
# assert is the drift guard against the database CHECK's list in app/models/category.py.
CategoryKind = Literal["income", "expense"]
assert get_args(CategoryKind) == CATEGORY_KINDS, "CategoryKind and CATEGORY_KINDS disagree"

# Same rules as AccountName (trimmed, non-empty, no control or zero-width
# characters), capped at the column's 80 characters.
CategoryName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=80,
        pattern=r"^[^\x00-\x1f​-‍﻿]+$",
    ),
]


class CategoryCreate(BaseModel):
    """POST /api/categories body. `kind` is required: guessing "expense" for a
    salary category would put income into expense totals without anyone noticing."""

    model_config = ConfigDict(extra="forbid")

    name: CategoryName
    kind: CategoryKind


class CategoryUpdate(BaseModel):
    """PATCH /api/categories/{id} body: rename and/or archive/unarchive.

    No `kind` field, and `extra="forbid"` is what makes that a rule rather than a
    silent ignore: a client sending `kind` gets a 422. Kind is immutable because
    changing it would re-bucket every past transaction filed under the category
    (income suddenly counted as spending, or the reverse)."""

    model_config = ConfigDict(extra="forbid")

    name: CategoryName | None = None
    is_archived: StrictBool | None = None

    @model_validator(mode="after")
    def _at_least_one_real_field(self) -> "CategoryUpdate":
        # Same rule as AccountUpdate: omitted means "leave alone", explicit null is
        # never meaningful (neither column is nullable), so it's refused.
        sent = self.model_fields_set
        if not sent:
            raise ValueError("send at least one field to change")
        nulls = [f for f in sent if getattr(self, f) is None]
        if nulls:
            raise ValueError(f"fields cannot be null: {', '.join(sorted(nulls))}")
        return self


class CategoryRead(BaseModel):
    """What every categories endpoint returns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: CategoryKind
    is_archived: bool
    created_at: datetime
