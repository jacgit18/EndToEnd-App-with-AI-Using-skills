"""Login rate limiting (ADR-0010 "forces into later ADRs").

A sliding-window counter per client IP, kept in process memory. That is
enough here because the app is one uvicorn process on one VPS (ADR-0012);
a second worker or a restart would each get its own (or an empty) counter.
If the app ever scales past one process, swap `_attempts` for Redis or a DB
table — the dependency's signature would not change.

Every login attempt counts, successful or not. For a single-user app that
costs the owner nothing, and it keeps the router free of "record a failure /
clear on success" bookkeeping.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 15 * 60

# client key -> monotonic timestamps of attempts still inside the window
_attempts: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    # Behind Caddy this is Caddy's address unless uvicorn runs with
    # --proxy-headers and --forwarded-allow-ips set to the proxy, in which
    # case it is the real client IP. Without that, every visitor shares one
    # bucket. Sort that out in the deploy phase.
    return request.client.host if request.client else "unknown"


def limit_login_attempts(request: Request) -> None:
    """FastAPI dependency: 429 once a client exceeds MAX_ATTEMPTS per window."""
    now = time.monotonic()
    attempts = _attempts[_client_key(request)]

    while attempts and now - attempts[0] >= WINDOW_SECONDS:
        attempts.popleft()

    if len(attempts) >= MAX_ATTEMPTS:
        retry_after = int(WINDOW_SECONDS - (now - attempts[0])) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    attempts.append(now)
