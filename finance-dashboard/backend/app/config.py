"""Application configuration.

Values come from environment variables (or a local .env file in dev), are
validated once at import time by pydantic-settings, and are read everywhere
else in the app via the module-level `settings` object. See ADR-0014.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # dev convenience; in prod the vars are real env vars
        env_file_encoding="utf-8",
        extra="ignore",            # tolerate unrelated vars in the environment
    )

    # Postgres connection string, e.g.
    #   postgresql+psycopg://finance:finance@localhost:5432/finance
    # Under Docker Compose the host is the service name ("db"), not localhost.
    database_url: str

    # "dev" locally, "prod" on the VPS. Gates dev-only behaviour (verbose errors,
    # SQL echo) only — never used as a security boundary.
    env: str = "dev"


# Import-time singleton. A missing or mistyped required variable makes this line
# raise, and the app refuses to start — a loud, early failure, by design (ADR-0014).
settings = Settings()  # type: ignore[call-arg]

# Added in later phases, same pattern:
#   auth_password_hash: str        argon2 hash of the one login password   (Phase 1, ADR-0010)
#   session_secret: str            signs the session cookie                (Phase 1, ADR-0010)
#   session_expire_minutes: int    idle session lifetime                   (Phase 1, ADR-0010)
#   sentry_dsn: str | None = None  error tracking; unset = disabled        (Phase 1, ADR-0013)
