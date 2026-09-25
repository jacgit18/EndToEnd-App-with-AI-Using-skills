"""POST /api/imports/preview, POST /api/imports, GET /api/imports — spec S5 (CSV import).

Thin on purpose: parsing and hashing live in app/importer.py (pure, unit-tested).
This file reads the upload, turns importer errors into HTTP errors, and does the
one thing that needs the database — writing the batch, its rows and the balance
change as ONE transaction. A crash mid-import leaves nothing behind: no batch,
no half the rows, no balance that counts rows that aren't there.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app import importer
from app.db import get_db
from app.models.account import Account
from app.models.import_batch import ImportBatch
from app.models.transaction import Transaction
from app.schemas.import_batch import (
    ImportBatchRead,
    ImportMapping,
    ImportPreview,
    ImportResult,
    RejectedRow,
)

router = APIRouter()

DEDUPE_CONSTRAINT = "uq_transaction_account_hash"  # UNIQUE(account_id, content_hash)
INSERT_CHUNK = 1000  # rows per INSERT: 1000 x 8 params, far under the 65535 bind-param limit


def _read_upload(file: UploadFile) -> importer.CsvFile:
    # One byte past the limit is enough to know it's too big without reading it all.
    raw = file.file.read(importer.MAX_FILE_BYTES + 1)
    try:
        return importer.read_csv(raw)
    except importer.ImportFileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None


def _filename(file: UploadFile) -> str:
    # The client names the file, so it's untrusted text headed for a VARCHAR(255):
    # control characters out (a NUL is a database error), cut to the column.
    name = "".join(ch for ch in (file.filename or "") if ch.isprintable()).strip()
    return name[:255] or "upload.csv"


@router.post("/preview", response_model=ImportPreview)
def preview_import(file: UploadFile = File(...)) -> ImportPreview:
    """Header + first rows for the mapping form. Reads the file, writes nothing
    (no DB session at all), so it's safe to call as often as the UI likes."""
    csv_file = _read_upload(file)
    return ImportPreview(
        headers=csv_file.headers,
        rows=[cells for _, cells in csv_file.rows[: importer.PREVIEW_ROWS]],
        row_count=len(csv_file.rows),
        delimiter=csv_file.delimiter,
    )


@router.get("", response_model=list[ImportBatchRead])
def list_imports(db: Session = Depends(get_db)) -> list[ImportBatch]:
    """Import history, newest first."""
    stmt = select(ImportBatch).order_by(ImportBatch.created_at.desc(), ImportBatch.id.desc())
    return list(db.scalars(stmt))


@router.post("", response_model=ImportResult, status_code=201)
def create_import(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    mapping: str = Form(...),  # JSON: a multipart form can't carry a nested object
    db: Session = Depends(get_db),
) -> ImportResult:
    # 1. Everything that can fail on the file or mapping, before touching the DB, so
    #    a bad request is a 422 with nothing saved (not even a batch row).
    try:
        parsed_mapping = ImportMapping.model_validate_json(mapping)
    except ValidationError as exc:
        # Same 422 shape FastAPI gives any other invalid field, located under "mapping".
        raise RequestValidationError(
            [
                {**e, "loc": ("body", "mapping", *e["loc"])}
                for e in exc.errors(include_url=False, include_context=False)
            ]
        ) from None
    csv_file = _read_upload(file)
    try:
        parsed = importer.parse_rows(csv_file, parsed_mapping)
    except importer.ImportFileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None

    # 2. Same lock, same order, as every other writer of `balance` (transaction
    #    create/void, account PATCH): `balance += imported` below is read-modify-write,
    #    so writers of one account take turns. Taken after parsing, so a 5000-row parse
    #    doesn't hold other writers up.
    account = db.get(Account, account_id, with_for_update=True)
    if account is None:
        raise HTTPException(status_code=404, detail="account not found")
    if account.is_archived:
        # Closed accounts take no new activity, imported or typed.
        raise HTTPException(status_code=409, detail="account is archived")

    try:
        # The batch is written even if nothing below imports (all rejected or all
        # duplicates): the history should show the file was tried and what happened.
        batch = ImportBatch(filename=_filename(file), account_id=account.id)
        db.add(batch)
        db.flush()  # assigns batch.id for the rows' import_batch_id

        # Dedupe (ADR-0005) is the database's UNIQUE(account_id, content_hash), not a
        # "does it exist?" pre-check: ON CONFLICT DO NOTHING skips a row whose hash is
        # already there, including one a concurrent import committed a moment ago.
        # RETURNING lists only the rows actually inserted, so skipped rows are neither
        # counted as imported nor added to the balance.
        inserted = []
        for start in range(0, len(parsed.rows), INSERT_CHUNK):
            chunk = parsed.rows[start : start + INSERT_CHUNK]
            stmt = (
                pg_insert(Transaction)
                .values(
                    [
                        {
                            "account_id": account.id,
                            "category_id": None,  # imported rows land uncategorized (S5)
                            "date": row.date,
                            "amount": row.amount,
                            "description": row.description,
                            "type": "normal",
                            "content_hash": row.content_hash,
                            "import_batch_id": batch.id,
                        }
                        for row in chunk
                    ]
                )
                .on_conflict_do_nothing(constraint=DEDUPE_CONSTRAINT)
                .returning(Transaction.amount)
            )
            inserted.extend(db.execute(stmt).scalars())

        batch.imported_count = len(inserted)
        batch.skipped_count = len(parsed.rows) - len(inserted)
        batch.rejected_count = len(parsed.rejected)

        # Maintained balance (ADR-0005 hybrid), in the same DB transaction as the
        # inserts: exactly the sum of what went in.
        account.balance += sum(inserted, Decimal("0.00"))

        db.commit()
    except DataError:
        db.rollback()  # balance + imported sum overflowed NUMERIC(14,2); nothing saved
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="resulting balance is out of range for NUMERIC(14,2)",
        ) from None

    return ImportResult(
        batch_id=batch.id,
        imported_count=batch.imported_count,
        skipped_count=batch.skipped_count,
        rejected_count=batch.rejected_count,
        rejected=[
            RejectedRow(line=line, reason=reason)
            for line, reason in parsed.rejected[: importer.REJECTED_LIST_CAP]
        ],
    )
