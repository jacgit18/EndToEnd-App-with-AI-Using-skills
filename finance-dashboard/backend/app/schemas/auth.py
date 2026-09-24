"""Pydantic schemas for the auth API.

Just the shapes of the login exchange. The session cookie itself never
appears here — it travels in the Set-Cookie header (HttpOnly, so page
JavaScript can't read it), not in a JSON body.
"""

from pydantic import BaseModel, SecretStr


class LoginRequest(BaseModel):
    """POST /api/auth/login body.

    Single-user v1 (ADR-0010): the router compares `email` to the one
    configured AUTH_EMAIL and `password` to AUTH_PASSWORD_HASH. `SecretStr`
    keeps the password out of logs and error reprs; the router reads it
    with `.get_secret_value()`.
    """

    email: str
    password: SecretStr


class LoginResponse(BaseModel):
    """What a successful login returns.

    `csrf_token` is the one value the frontend needs to hold on to: unlike
    the HttpOnly cookie, page JavaScript must be able to read it, so it can
    echo it back in a header on state-changing requests (increments 8 and
    14). How the server derives and later verifies it is decided in
    increment 8 — this schema only fixes that it travels in the body.
    """

    csrf_token: str
