"""POST /api/auth/login, POST /api/auth/logout (ADR-0010).

The only place the pieces built in increments 3-6 meet HTTP:
- login: check credentials -> stage a session row -> commit -> set the signed
  cookie and hand back the CSRF token in the body.
- logout: delete the caller's session row and clear the cookie.

Routers own the transaction (app/auth.py never commits), so each handler
commits exactly once.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import create_session, delete_session
from app.config import settings
from app.db import get_db
from app.dependencies import SESSION_COOKIE_NAME, get_current_session
from app.models.session import AuthSession
from app.schemas.auth import LoginRequest, LoginResponse
from app.security import make_csrf_token, sign_session_id, verify_password

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> LoginResponse:
    # Evaluate both checks before branching, so a wrong email and a wrong
    # password cost the same time and produce the same 401.
    email_ok = secrets.compare_digest(
        payload.email.encode(), settings.auth_email.encode()
    )
    password_ok = verify_password(payload.password.get_secret_value())
    if not (email_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    session = create_session(db)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sign_session_id(session.id),
        max_age=settings.session_expire_minutes * 60,
        httponly=True,  # page JS can't read it (ADR-0010)
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return LoginResponse(csrf_token=make_csrf_token(session.id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> None:
    delete_session(db, session.id)
    db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
