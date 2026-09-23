"""Password verification and session-cookie signing (ADR-0010).

Two independent mechanisms, kept in one small file since both exist to
answer the same question — "can this be trusted?" — at two different points
in the request:

- verify_password: checks a login attempt against the one configured
  AUTH_PASSWORD_HASH (argon2). Runs once, at login.
- sign_session_id / unsign_session_id: the value that actually goes in the
  cookie isn't the bare AuthSession.id — it's that id signed with
  SESSION_SECRET. ADR-0010 keeps the session id itself a simple opaque DB
  lookup key (that's the whole point vs. a JWT); signing it is the separate,
  belt-and-suspenders layer ADR-0014 calls "a session signing secret" —
  it stops a guessed or hand-edited cookie value from ever reaching the
  database lookup, rather than relying on the lookup alone to reject it.

Expiry is deliberately NOT handled here. itsdangerous can time-limit a
signature itself, but AuthSession.expires_at (the DB row) is ADR-0010's
actual source of truth for "is this session still good" — adding a second,
signature-based expiry clock would just be two answers that can disagree.
app/dependencies.py checks expires_at; this file only answers "is this
signature genuine and un-tampered".
"""

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from itsdangerous import BadData, URLSafeSerializer

from app.config import settings

_hasher = PasswordHasher()
_signer = URLSafeSerializer(settings.session_secret, salt="session-cookie")


def verify_password(password: str) -> bool:
    """True if `password` matches the configured AUTH_PASSWORD_HASH.

    Never a plaintext comparison — argon2's `verify` re-hashes `password`
    with the parameters embedded in the stored hash and compares in
    constant time, which is what makes a timing attack on the password
    infeasible.

    Catches `Argon2Error`, not just `VerifyMismatchError` (a wrong
    password) — confirmed the hard way that a malformed AUTH_PASSWORD_HASH
    (e.g. a copy-pasted placeholder that was never replaced with a real
    generated hash) raises `VerificationError`, a sibling exception, not
    `VerifyMismatchError`. A narrower catch would have let a config mistake
    surface as an unhandled 500 on every login attempt instead of a clean
    rejection — worse than "wrong password" behavior, since it can leak a
    stack trace and gives an attacker a way to distinguish "misconfigured"
    from "just wrong" from the outside.
    """
    try:
        _hasher.verify(settings.auth_password_hash, password)
    except Argon2Error:
        return False
    return True


def sign_session_id(session_id: str) -> str:
    """Wrap a raw AuthSession.id for the Set-Cookie header.

    `session_id` alone is what the database looks up by; the signature
    wrapped around it here is what a client can't forge or edit.
    """
    return _signer.dumps(session_id)


def unsign_session_id(cookie_value: str) -> str | None:
    """Reverse of sign_session_id.

    Returns the raw session id if the signature is genuine, or None on
    anything else — missing, malformed, or tampered. The caller
    (app/dependencies.py) treats None exactly like "no session cookie at
    all": a straightforward 401, not a special case to handle differently.
    """
    try:
        return _signer.loads(cookie_value)
    except BadData:
        return None
