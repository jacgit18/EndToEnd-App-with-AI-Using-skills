"""Startup validation in app/config.py — pure unit tests, no database."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@localhost/x")
os.environ.setdefault("AUTH_EMAIL", "a@b.c")
os.environ.setdefault("AUTH_PASSWORD_HASH", "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$aGFzaGhhc2hoYXNoaGFzaA")
os.environ.setdefault("SESSION_SECRET", "s")

import pytest  # noqa: E402
from argon2 import PasswordHasher  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.config import Settings  # noqa: E402


def make_settings(auth_password_hash: str) -> Settings:
    # _env_file=None: ignore a local .env so the test controls every value.
    return Settings(
        _env_file=None,
        database_url="postgresql+psycopg://x:x@localhost/x",
        auth_email="a@b.c",
        auth_password_hash=auth_password_hash,
        session_secret="s",
    )


def test_a_real_argon2_hash_is_accepted():
    real = PasswordHasher().hash("pw")

    assert make_settings(real).auth_password_hash == real


@pytest.mark.parametrize(
    "bad",
    [
        "not-a-hash",
        "argon2id$v=19$m=65536",  # what Compose leaves after eating an un-doubled '$'
        "=19=65536,t=3,p=4",
    ],
)
def test_a_malformed_hash_stops_startup(bad):
    with pytest.raises(ValidationError, match="not a valid argon2 hash"):
        make_settings(bad)
