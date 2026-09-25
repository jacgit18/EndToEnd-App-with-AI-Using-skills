"""GET/POST/PATCH /api/categories — list, create, rename/archive (spec S3).

No DELETE: transactions reference categories forever, so an unwanted category is
archived instead (hidden from pickers, history kept).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()

NAME_CONSTRAINT = "categories_name_key"  # the UNIQUE(name) index, named by Postgres


def _is_name_conflict(exc: IntegrityError) -> bool:
    """True only for the unique-name violation. Any other integrity error is a bug
    or a new constraint, and must not be reported to the client as "duplicate name"."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == NAME_CONSTRAINT


def _name_taken() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="a category with that name already exists",
    )


@router.get("", response_model=list[CategoryRead])
def list_categories(
    include_archived: bool = False, db: Session = Depends(get_db)
) -> list[Category]:
    """Archived categories are hidden by default (they must not appear in the
    transaction form's picker). The categories page passes ?include_archived=true."""
    stmt = select(Category).order_by(Category.kind, Category.name)
    if not include_archived:
        stmt = stmt.where(Category.is_archived.is_(False))
    return list(db.scalars(stmt))


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    category = Category(name=payload.name, kind=payload.kind)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        # name is UNIQUE; catching the database's refusal is race-safe (see accounts).
        db.rollback()
        if not _is_name_conflict(exc):
            raise
        raise _name_taken()
    db.refresh(category)  # pulls back the DB-assigned id, created_at, is_archived
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)
) -> Category:
    """Rename and/or archive/unarchive. `kind` is not editable (CategoryUpdate
    rejects it). Archiving leaves every existing transaction as it is; it only
    hides the category from the default list and blocks new transactions."""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()  # nothing was saved
        if not _is_name_conflict(exc):
            raise
        raise _name_taken()
    db.refresh(category)
    return category
