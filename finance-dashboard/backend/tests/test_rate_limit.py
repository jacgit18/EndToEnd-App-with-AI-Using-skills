"""Login rate limiter: client key under a spoofed X-Forwarded-For, and bounded memory.

No database needed: the proxy-header handling is exercised with uvicorn's own
middleware on a bare ASGI app, using the FORWARDED_ALLOW_IPS value that
compose.prod.yaml really sets.
"""

import asyncio
import re
import time
from pathlib import Path

from starlette.requests import Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import rate_limit

COMPOSE_PROD = Path(__file__).resolve().parents[2] / "compose.prod.yaml"

# What the backend sees in prod: Caddy (private) connects; the header holds what the
# visitor sent, then the visitor address Cloudflare appended, then cloudflared's
# address appended by Caddy.
CADDY = ("172.18.0.5", 40000)
REAL_VISITOR = "203.0.113.9"


def _prod_allowed_ips() -> str:
    text = COMPOSE_PROD.read_text()
    match = re.search(r'^\s*FORWARDED_ALLOW_IPS:\s*"([^"]*)"', text, re.MULTILINE)
    assert match, "FORWARDED_ALLOW_IPS not found in compose.prod.yaml"
    return match.group(1)


def _key_seen_by_limiter(allowed_ips: str, forwarded_for: str) -> str:
    seen = {}

    async def app(scope, receive, send):
        seen["key"] = rate_limit._client_key(Request(scope))

    scope = {
        "type": "http",
        "client": CADDY,
        "headers": [(b"x-forwarded-for", forwarded_for.encode())],
    }
    asyncio.run(ProxyHeadersMiddleware(app, trusted_hosts=allowed_ips)(scope, None, None))
    return seen["key"]


def test_prod_config_does_not_trust_every_forwarded_entry():
    assert _prod_allowed_ips() != "*"


def test_spoofed_leftmost_entry_does_not_change_the_client_key():
    allowed = _prod_allowed_ips()
    keys = {
        _key_seen_by_limiter(allowed, f"198.51.100.{i}, {REAL_VISITOR}, 172.18.0.2")
        for i in range(20)
    }
    assert keys == {REAL_VISITOR}


def test_star_would_let_a_rotating_header_dodge_the_limit():
    """Documents why '*' is wrong: the visitor-controlled leftmost entry becomes the key."""
    keys = {
        _key_seen_by_limiter("*", f"198.51.100.{i}, {REAL_VISITOR}, 172.18.0.2")
        for i in range(20)
    }
    assert len(keys) == 20


def test_expired_clients_are_swept_so_keys_cannot_pile_up(monkeypatch):
    rate_limit._attempts.clear()
    old = time.monotonic() - rate_limit.WINDOW_SECONDS - 1
    for i in range(rate_limit.SWEEP_THRESHOLD + 50):
        rate_limit._attempts[f"10.0.{i // 250}.{i % 250}"].append(old)

    request = Request({"type": "http", "client": ("203.0.113.1", 1), "headers": []})
    rate_limit.limit_login_attempts(request)

    assert list(rate_limit._attempts) == ["203.0.113.1"]
    rate_limit._attempts.clear()
