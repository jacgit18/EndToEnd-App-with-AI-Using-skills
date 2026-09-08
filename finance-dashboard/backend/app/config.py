from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from the environment (and a local .env if present)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://finance:finance@db:5432/finance"

    # Single-user auth (story S1). No user table in v1.
    auth_email: str = "you@example.com"
    auth_password: str = "change-me"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # one week

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
