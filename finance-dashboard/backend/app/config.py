"""Application configuration.

Values come from environment variables (or a local .env file in dev), are
validated once at import time by pydantic-settings, and are read everywhere
else in the app via the module-level `settings` object. See ADR-0014.
"""

from argon2 import extract_parameters
from argon2.exceptions import InvalidHashError
from pydantic import Field, field_validator
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

    # The one login identity. Unchanged by ADR-0010 — that ADR only replaced
    # the password side (AUTH_PASSWORD -> AUTH_PASSWORD_HASH); email stays a
    # plain compared value, never hashed (there's nothing secret about it).
    auth_email: str

    # Argon2 hash of the one login password (ADR-0010) — never the plaintext
    # password itself. Generated once with an argon2 hash helper (ADR-0014).
    # min_length=1 turns an env var that's *set but empty* (e.g. a Compose
    # ${VAR} with no default and nothing in .env — a plain str field would
    # accept "" as valid) into the same fail-fast startup error a genuinely
    # missing var already gets, rather than booting with a hash that can
    # never match any password.
    auth_password_hash: str = Field(min_length=1)

    @field_validator("auth_password_hash")
    @classmethod
    def _hash_must_be_a_real_argon2_hash(cls, value: str) -> str:
        """Refuse to boot on a hash argon2 can't parse.

        min_length=1 above only catches an empty value. A *malformed* one (a
        placeholder never replaced, or a Compose env_file value whose `$` wasn't
        doubled to `$$` and got stripped) is non-empty, so it used to pass
        startup and then make every login raise InvalidHashError -> HTTP 500.
        Parsing it here turns that into the same loud fail-fast as a missing var.
        """
        try:
            extract_parameters(value)
        except InvalidHashError as exc:
            raise ValueError(
                "AUTH_PASSWORD_HASH is not a valid argon2 hash. Generate one with "
                "PasswordHasher().hash(...); in a Compose env_file, double every '$' as '$$'."
            ) from exc
        return value

    # Signs the session-id cookie value (app/security.py) — a real secret
    # (ADR-0014), generated once with e.g.
    #   python -c "import secrets; print(secrets.token_urlsafe(32))"
    session_secret: str = Field(min_length=1)

    # Idle session lifetime. A plain int, not a security boundary by itself —
    # expiry is enforced by checking AuthSession.expires_at, this just sets
    # how far out that gets stamped at login.
    session_expire_minutes: int = 60

    # Sentry error tracking (ADR-0013). Unset = the SDK is never initialised and
    # nothing leaves the machine. A DSN comes from a Sentry project you create.
    # COST: Sentry's free "Developer" plan (as of writing, unverified since —
    # check sentry.io/pricing) covers one user and a few thousand errors/month
    # with no card. Past that, events are dropped or an upgrade is prompted; the
    # paid Team plan (~$26+/mo) adds seats, retention and alerting. Documented in
    # docs/paid-options.md.
    sentry_dsn: str | None = None

    @property
    def cookie_secure(self) -> bool:
        """Whether the session cookie gets the `Secure` flag (HTTPS-only).

        ADR-0010 wants `Secure` in production, but browsers silently refuse
        to set a `Secure` cookie over plain HTTP — and there's no TLS yet in
        dev (native or Compose) or even in prod until the deploy phase adds
        Caddy + a real domain. Gating on `env` means login actually works
        locally now, and starts enforcing `Secure` the moment `env=prod` is
        set, with no code change needed at deploy time.
        """
        return self.env == "prod"


# Import-time singleton. A missing or mistyped required variable makes this line
# raise, and the app refuses to start — a loud, early failure, by design (ADR-0014).
settings = Settings()  # type: ignore[call-arg]

