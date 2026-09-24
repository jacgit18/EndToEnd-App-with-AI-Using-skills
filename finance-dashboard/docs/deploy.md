# Deploying (free path)

Runs the app on your own machine and reaches it from the internet through a Cloudflare
**quick tunnel**. Costs nothing, needs no account, no domain, no open router ports.
Files: [`compose.prod.yaml`](../compose.prod.yaml), [`Caddyfile.prod`](../Caddyfile.prod),
[`frontend/Dockerfile.prod`](../frontend/Dockerfile.prod), [`scripts/backup-db.sh`](../scripts/backup-db.sh).
This amends ADR-0012 (VPS + domain) — see the spec's drift log.

**Limits you are accepting:** the app is up only while this machine and Docker are; the tunnel
URL (`https://<random>.trycloudflare.com`) changes every time the `cloudflared` container
restarts; Cloudflare documents quick tunnels as for testing, with no uptime guarantee.

## First run

1. **Secrets.** Two gitignored files (nothing in them is ever committed):

   `finance-dashboard/.env`
   ```
   POSTGRES_PASSWORD=<generate: python3 -c "import secrets; print(secrets.token_urlsafe(24))">
   ```

   `finance-dashboard/backend/.env.prod` — same format as `.env.docker.example`, and the same
   rule: **double every `$` in the argon2 hash** (`$$argon2id$$v=19...`) or Compose mangles it.
   ```
   AUTH_EMAIL=you@example.com
   AUTH_PASSWORD_HASH=<hash of a NEW password, $ doubled>
   SESSION_SECRET=<generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
   ```
   Hash: `cd backend && uv run python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('your-password'))"`.
   **Use a real password, not the dev `devpassword`** — this stack is reachable from the internet.

2. **Start.** `docker compose -f compose.prod.yaml up -d --build` (migrations run on backend start).
3. **Find the URL.** `docker compose -f compose.prod.yaml logs cloudflared | grep trycloudflare`
4. **Smoke test.** `curl https://<that-url>/health` → `{"status":"ok","db":"connected"}`, then sign in in a browser.
   Local check without the tunnel: `http://localhost:8080`.
5. **Stop.** `docker compose -f compose.prod.yaml down` (keeps the database volume; `down -v` deletes it).

## What was verified (2026-09-24, dev credentials, torn down after)

Stack came up healthy; `/health` reported `db: connected` locally and through a live tunnel;
`/login` (SPA route) returned 200; `/api/accounts` without a session returned 401; login set a
`HttpOnly; Secure; SameSite=lax` cookie. Not verified: a browser sign-in through the tunnel,
the backup restore below, or any long-running behaviour.

## Backups

```bash
scripts/backup-db.sh        # dumps to ./backups, keeps the newest 14
```
Schedule nightly with cron (example line is in the script header). **Restore drill — do this once:**
```bash
gunzip -c backups/finance-<stamp>.sql.gz | docker compose -f compose.prod.yaml exec -T db psql -U finance -d finance_restore_test
# (create it first: docker compose -f compose.prod.yaml exec db createdb -U finance finance_restore_test)
```
Also copy `backups/` somewhere off this machine (USB / another computer / `rclone` to Backblaze B2's
free 10 GB) and keep `backend/.env.prod` in a password manager. A backup on the same disk is not a backup.

## Error tracking (Sentry) — not wired yet

ADR-0013 picked Sentry's free tier. The backend does not have the SDK or a `SENTRY_DSN` setting
yet; it is a small separate increment (add `sentry-sdk`, a `sentry_dsn: str | None` in
`config.py`, init in `main.py` only when set). Until then, `docker compose -f compose.prod.yaml logs backend`
is the error log.

## If you were serious about this

| Free choice here | Upgrade | Roughly |
|---|---|---|
| Runs on your machine | Small VPS (Hetzner, DigitalOcean) — delete `cloudflared`, publish Caddy on 80/443 | $5–7/mo |
| Random `trycloudflare.com` URL | Your own domain + a named Cloudflare tunnel (free once you own the domain) or an A record + Caddy's automatic Let's Encrypt | $10–12/yr |
| `pg_dump` cron to local disk | Managed Postgres with point-in-time restore (Neon, Supabase, RDS) or VPS snapshots | free tiers exist; paid ~$10–25+/mo |
| Manual `docker compose up` | CI deploy (GitHub Actions is free for public repos, limited minutes for private) | $0 |

## Rate limiter and client IPs

The login limiter keys on `request.client.host`. `Caddyfile.prod` trusts `X-Forwarded-For` from
private ranges and `compose.prod.yaml` sets `FORWARDED_ALLOW_IPS="*"`, so uvicorn sees the real
visitor. That `"*"` is only safe because the backend publishes no port — do not add a `ports:`
entry to `backend`. Limiter state is in memory, so restarting the backend resets the counters.
