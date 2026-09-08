from __future__ import annotations

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CategoryKind(str, enum.Enum):
    income = "income"
    expense = "expense"


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[CategoryKind] = mapped_column(Enum(CategoryKind, name="category_kind"))
    archived: Mapped[bool] = mapped_column(default=False)
