"""AuthSession — one logged-in browser session (ADR-0010).

Server-side sessions: the HttpOnly cookie carries only this row's opaque `id`.
Login inserts a row, logout deletes it, an expired row counts as logged-out.
Single-user for v1, so there is no user_id. Named AuthSession to avoid confusion
with SQLAlchemy's own Session class.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuthSession(Base):
    __tablename__ = "sessions"

    # Opaque random token generated at login, stored in the cookie.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Login/logout/expiry logic is built in Phase 1 (S1).
