"""FastAPI application entrypoint.

Dev: `uvicorn app.main:app --reload` (from backend/, with the venv active).
The Docker image runs the same `app.main:app` target without --reload.
"""

import sentry_sdk
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import require_csrf
from app.routers import accounts, auth, transactions

# Error tracking only when a DSN is configured (ADR-0013). This is a finance app,
# so the defaults are tightened: no request bodies (they carry transaction
# descriptions and amounts), no user/IP/cookie data, and no performance tracing
# (errors only — also keeps event volume inside the free tier).
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=0.0,
    )

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
