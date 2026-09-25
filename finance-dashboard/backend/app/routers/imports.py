"""POST /api/imports/preview, POST /api/imports, GET /api/imports — spec S5 (CSV import).

Thin on purpose: parsing and hashing live in app/importer.py (pure, unit-tested).
This file reads the upload, turns importer errors into HTTP errors, and does the
one thing that needs the database — writing the batch(es), their rows and the
balance changes as ONE transaction. A crash mid-import leaves nothing behind: no
batch, no half the rows, no balance that counts rows that aren't there.

Two modes, chosen by the mapping. Single-account: the form's `account_id` takes
every row, one batch. Multi-account: the mapping's `account_column` + `account_map`
file each row under its own account, one batch per account the file touched, all
in the same transaction.
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
    ImportResultBatch,
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
        distinct_values=importer.distinct_values(csv_file),
    )


@router.get("", response_model=list[ImportBatchRead])
def list_imports(db: Session = Depends(get_db)) -> list[ImportBatch]:
    """Import history, newest first."""
    stmt = select(ImportBatch).order_by(ImportBatch.created_at.desc(), ImportBatch.id.desc())
    return list(db.scalars(stmt))


def _form_error(error_type: str, message: str, value) -> RequestValidationError:
    # Same 422 shape FastAPI gives any other invalid form field.
    return RequestValidationError(
        [{"type": error_type, "loc": ("body", "account_id"), "msg": message, "input": value}]
    )


@router.post("", response_model=ImportResult, status_code=201)
def create_import(
    file: UploadFile = File(...),
    # Required in single-account mode, refused in multi-account mode (the mapping's
    # account_map names the accounts). Optional here so the router can say which.
    account_id: int | None = Form(None),
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
    if parsed_mapping.multi_account and account_id is not None:
        # Two sources of truth for where the money goes: refuse rather than pick one.
        raise _form_error(
            "extra_forbidden", "account_id is not allowed when the mapping has account_map",
            account_id,
        )
    if not parsed_mapping.multi_account and account_id is None:
        raise _form_error("missing", "Field required", None)

    csv_file = _read_upload(file)
    try:
        parsed = importer.parse_rows(csv_file, parsed_mapping)
    except importer.ImportFileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None

    # Which accounts get a batch, and what each one's rows and rejections are.
    rows_by_account: dict[int, list[importer.ParsedRow]] = {}
    if parsed_mapping.multi_account:
        for row in parsed.rows:
            rows_by_account.setdefault(row.account_id, []).append(row)
        # Per-batch rejected_count: only rejections whose account cell was readable
        # and mapped to that account (importer.parse_rows). A row rejected for an
        # unmapped value, or too short to reach the account column, has no account
        # and is counted at the top level only.
        rejected_by_account = parsed.rejected_by_account
        # A batch for every account the file actually touched: one with at least
        # one parsed row, or at least one attributed rejection — so, like single
        # mode, an account whose rows were all rejected still gets a history entry
        # showing the file was tried. An account in the map but absent from the
        # file gets no batch (it is still locked and checked below).
        batch_accounts = sorted(set(rows_by_account) | set(rejected_by_account))
        if not batch_accounts:
            # Every row was excluded or had an unmapped value: there is no account
            # to record anything against, and nothing could be imported.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="no row in the file belongs to an account in account_map",
            )
        # Every non-null id in the map, not just those with rows: a map naming a
        # missing or archived account is a wrong mapping, whatever this file holds.
        # dict.fromkeys de-duplicates keeping the map's order; sorted() is what
        # makes the lock order ascending (see step 2).
        lock_ids = sorted(
            dict.fromkeys(v for v in parsed_mapping.account_map.values() if v is not None)
        )
    else:
        rows_by_account[account_id] = parsed.rows
        rejected_by_account = {account_id: len(parsed.rejected)}  # single mode: all of them
        batch_accounts = [account_id]
        lock_ids = [account_id]

    # 2. Same lock as every other writer of `balance` (transaction create/void,
    #    account PATCH): `balance += imported` below is read-modify-write, so writers
    #    of one account take turns. Taken after parsing, so a 5000-row parse doesn't
    #    hold other writers up. With several accounts, the locks are taken one at a
    #    time in ASCENDING id order: two imports over overlapping accounts then
    #    always queue on the lowest shared id first instead of each holding one lock
    #    the other wants (a deadlock Postgres would break by failing one of them).
    #    Every other writer takes a single account lock, so it can't join a cycle.
    #    A 404/409 here ends the request with nothing written; closing the session
    #    rolls back and releases whatever locks were already taken.
    accounts: dict[int, Account] = {}
    for lock_id in lock_ids:
        # Multi mode names the account: the map can hold many ids. Single mode keeps
        # its original wording.
        label = f"account {lock_id}" if parsed_mapping.multi_account else "account"
        account = db.get(Account, lock_id, with_for_update=True)
        if account is None:
            raise HTTPException(status_code=404, detail=f"{label} not found")
        if account.is_archived:
            # Closed accounts take no new activity, imported or typed.
            raise HTTPException(status_code=409, detail=f"{label} is archived")
        accounts[lock_id] = account

    # 3. One DB transaction for the whole file: every batch, every row, every
    #    balance change, or none of them.
    filename = _filename(file)
    batches: list[ImportBatch] = []
    try:
        for batch_account in batch_accounts:
            account = accounts[batch_account]
            rows = rows_by_account.get(batch_account, [])
            # The batch is written even if nothing below imports (all rejected or all
            # duplicates): the history should show the file was tried and what happened.
            batch = ImportBatch(filename=filename, account_id=account.id)
            db.add(batch)
            db.flush()  # assigns batch.id for the rows' import_batch_id

            # Dedupe (ADR-0005) is the database's UNIQUE(account_id, content_hash), not a
            # "does it exist?" pre-check: ON CONFLICT DO NOTHING skips a row whose hash is
            # already there, including one a concurrent import committed a moment ago.
            # RETURNING lists only the rows actually inserted, so skipped rows are neither
            # counted as imported nor added to the balance.
            inserted = []
            for start in range(0, len(rows), INSERT_CHUNK):
                chunk = rows[start : start + INSERT_CHUNK]
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
            batch.skipped_count = len(rows) - len(inserted)
            batch.rejected_count = rejected_by_account.get(batch_account, 0)

            # Maintained balance (ADR-0005 hybrid), in the same DB transaction as the
            # inserts: exactly the sum of what went in for THIS account.
            account.balance += sum(inserted, Decimal("0.00"))
            batches.append(batch)

        db.commit()
    except DataError:
        # Some balance + imported sum overflowed NUMERIC(14,2) (raised at whichever
        # flush writes it). One transaction, so every account's rows, batches and
        # balance changes go with it: nothing saved.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="resulting balance is out of range for NUMERIC(14,2)",
        ) from None

    return ImportResult(
        batch_id=batches[0].id,
        imported_count=sum(b.imported_count for b in batches),
        skipped_count=sum(b.skipped_count for b in batches),
        rejected_count=len(parsed.rejected),  # includes rejections with no account
        rejected=[
            RejectedRow(line=line, reason=reason)
            for line, reason in parsed.rejected[: importer.REJECTED_LIST_CAP]
        ],
        excluded_count=parsed.excluded_count,
        batches=[
            ImportResultBatch(
                batch_id=b.id,
                account_id=b.account_id,
                imported_count=b.imported_count,
                skipped_count=b.skipped_count,
                rejected_count=b.rejected_count,
            )
            for b in batches
        ],
    )
