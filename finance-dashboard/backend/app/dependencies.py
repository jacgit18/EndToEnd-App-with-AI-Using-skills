"""Request-level auth: turn "no valid session" into a 401 (ADR-0010).

The last link in the chain the earlier increments built:
- app/security.py: is the cookie's signature genuine?
- app/auth.py: does that id match a row that hasn't expired?
- this file: read the cookie off the request, run those two checks in order,
  and refuse the request if either fails.

Every failure mode — no cookie, bad signature, unknown id, expired row —
raises the same 401 with the same message. A caller (or attacker) can't
tell which check failed, and the frontend only needs one behavior for all
of them: redirect to login.
"""

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import get_valid_session
from app.db import get_db
from app.models.session import AuthSession
from app.security import unsign_session_id, verify_csrf_token

# Shared with the login/logout router (increment 7), which sets and clears
# the cookie under this same name.
SESSION_COOKIE_NAME = "session"
CSRF_HEADER_NAME = "X-CSRF-Token"
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_current_session(
    cookie_value: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> AuthSession:
    """FastAPI dependency: the caller's valid AuthSession, or a 401.

    Used as `session: AuthSession = Depends(get_current_session)`, or as
    `dependencies=[Depends(get_current_session)]` on a router when the
    handler doesn't need the session object itself.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
    if cookie_value is None:
        raise unauthorized
    session_id = unsign_session_id(cookie_value)
    if session_id is None:
        raise unauthorized
    session = get_valid_session(db, session_id)
    if session is None:
        raise unauthorized
    return session


def require_csrf(
    request: Request,
    session: AuthSession = Depends(get_current_session),
) -> AuthSession:
    """FastAPI dependency: authenticated AND, for state-changing methods, CSRF-checked.

    A cross-site page can make the browser attach the session cookie to a
    request, but it can't read our CSRF token or set a custom header, so a
    matching X-CSRF-Token proves the request came from our own frontend.
    Safe methods (GET/HEAD/OPTIONS) change nothing and skip the check.

    Authentication runs first (via get_current_session), so an unauthenticated
    caller gets the uniform 401, never a 403 that hints a session was needed.
    """
    if request.method in _SAFE_METHODS:
        return session
    token = request.headers.get(CSRF_HEADER_NAME)
    if token is None or not verify_csrf_token(token, session.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
    return session
