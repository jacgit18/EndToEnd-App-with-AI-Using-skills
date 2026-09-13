"""Database wiring: one engine, one session factory, one declarative Base.

SQLAlchemy 2.0 style (ADR-0006). Everything that talks to Postgres goes through
here — models inherit `Base`, request handlers get a `Session` via `get_db`.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# One engine per process. It owns a connection pool and is safe to share across
# threads. `pool_pre_ping` quietly checks a pooled connection is still alive
# before handing it out — Postgres in a container can drop idle connections.
# `echo` logs every SQL statement; on in dev, off in prod.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=(settings.env == "dev"),
)

# A factory for Session objects. Each unit of work (one HTTP request) gets its
# own short-lived Session from this. `expire_on_commit=False` lets handlers keep
# reading attributes off an object after the transaction commits.
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent of every ORM model. `Base.metadata` is the catalogue of tables
    that Alembic diffs against to generate migrations (ADR-0006)."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency. Opens a Session for the request, guarantees it is
    closed afterwards even if the handler raises. Used as `db: Session = Depends(get_db)`.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
