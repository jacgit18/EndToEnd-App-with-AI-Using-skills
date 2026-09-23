"""Session lifecycle: create, look up, and delete AuthSession rows (ADR-0010).

Deliberately just database operations, nothing else — no HTTP, no cookies:
- app/security.py answers "is this cookie value genuine" (signing).
- This file answers "does this session id correspond to a still-valid row".
- app/dependencies.py (next increment) is what turns "no valid session"
  into an actual 401 for a request.

None of these functions call db.commit() — same convention as the existing
routers (app/routers/transactions.py commits once, in the router, after
every change belonging to one request is staged). The login router will
stage a session insert; logout will stage a delete; each owns its own
transaction boundary, this file just knows how to build the changes.
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.session import AuthSession


def create_session(db: Session) -> AuthSession:
    """Stage a new AuthSession row (uncommitted) and return it.

    The id is generated here, not left to a database default — the caller
    (the login router) needs it immediately, to sign into the cookie value,
    before the row is ever committed.
    """
    session = AuthSession(
        id=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.session_expire_minutes),
    )
    db.add(session)
    return session


def get_valid_session(db: Session, session_id: str) -> AuthSession | None:
    """Look up a session by id — None if it doesn't exist OR has expired.

    Deliberately doesn't delete an expired row it finds: ADR-0010 assigns
    cleanup to a separate reconciliation/maintenance job, not to this read
    path. A dependency running on every protected request is the wrong
    place to also be issuing writes.
    """
    session = db.get(AuthSession, session_id)
    if session is None:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        return None
    return session


def delete_session(db: Session, session_id: str) -> None:
    """Stage removing a session row (logout) — uncommitted, like create_session.

    Silently does nothing if the id doesn't exist: logging out of a session
    that's already gone (expired, already logged out elsewhere, cookie from
    a wiped database) isn't an error worth surfacing to the caller.
    """
    session = db.get(AuthSession, session_id)
    if session is not None:
        db.delete(session)
