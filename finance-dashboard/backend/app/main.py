"""FastAPI application entrypoint.

Dev: `uvicorn app.main:app --reload` (from backend/, with the venv active).
The Docker image runs the same `app.main:app` target without --reload.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_csrf
from app.routers import accounts, auth, transactions

app = FastAPI(title="Finance Dashboard API")

# Public: login needs no session; logout authenticates itself (app/routers/auth.py).
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Everything else requires a valid session, plus a CSRF token on writes. Applying
# require_csrf here (not per route) means a future router can't forget it.
_protected = [Depends(require_csrf)]
app.include_router(
    accounts.router, prefix="/api/accounts", tags=["accounts"], dependencies=_protected
)
app.include_router(
    transactions.router,
    prefix="/api/transactions",
    tags=["transactions"],
    dependencies=_protected,
)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness + DB connectivity check (ADR-0013).

    Hit by uptime monitoring in prod, and by the Phase 0 frontend badge — the
    first real end-to-end round trip: browser -> Vite proxy -> FastAPI -> Postgres.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unreachable"
    return {"status": "ok", "db": db_status}
