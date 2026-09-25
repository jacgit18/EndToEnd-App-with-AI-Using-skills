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

   `finance-dashboard/.env.prod`  (NOT `.env` — Compose auto-loads `.env` for the dev stack too)
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

2. **Start.** `scripts/prod.sh up -d --build` (migrations run on backend start).
3. **Find the URL.** `scripts/prod.sh logs cloudflared | grep trycloudflare`
4. **Smoke test.** `curl https://<that-url>/health` → `{"status":"ok","db":"connected"}`, then sign in in a browser.
   Local check without the tunnel: `http://localhost:8080`.
5. **Stop.** `scripts/prod.sh down` (keeps the database volume; `down -v` deletes it).

## What was verified (2026-09-24, dev credentials, torn down after)

Stack came up healthy; `/health` reported `db: connected` locally and through a live tunnel;
`/login` (SPA route) returned 200; `/api/accounts` without a session returned 401; login set a
`HttpOnly; Secure; SameSite=lax` cookie. Not verified: a browser sign-in through the tunnel,
the backup restore below, or any long-running behaviour.

## Backups

```bash
scripts/backup-db.sh        # dumps to ./backups, keeps the newest 14
```
Scheduled nightly (02:30) on the owner's machine since 2026-09-25; logs in `backups/backup.log`. Cron example is in the script header. **Restore drill — do this once:**
```bash
gunzip -c backups/finance-<stamp>.sql.gz | scripts/prod.sh exec -T db psql -U finance -d finance_restore_test
# (create it first: scripts/prod.sh exec db createdb -U finance finance_restore_test)
```
Also copy `backups/` somewhere off this machine (USB / another computer / `rclone` to Backblaze B2's
free 10 GB) and keep `backend/.env.prod` in a password manager. A backup on the same disk is not a backup.

## Balance reconciliation (Phase 2)

`accounts.balance` is a maintained figure; ADR-0005 says it must equal
`starting_balance + SUM(transactions.amount)`. `app/reconcile.py` checks that for every account
(archived too). It is read-only: it reports drift, it never repairs it.

```bash
scripts/prod.sh exec -T backend uv run python -m app.reconcile
```
Exit code **0** = all match, **1** = drift (WARN lines name each account, its stored and expected
balance), **2** = the job itself could not run (DB down, or zero accounts, which usually means the
wrong database). Run it nightly after the backup and alert on any non-zero exit, e.g.
`30 2 * * * cd /path/to/finance-dashboard && scripts/prod.sh exec -T backend uv run python -m app.reconcile || <your alert>`.
On drift, read the WARN lines and decide which side is right by hand before touching anything.

**Installed 2026-09-25:** cron runs this at 02:40 (after the backup) and appends to `backups/reconcile.log`; there is no push alert, so check that log. Cron only fires while the machine is on.

**Applying Phase 4 to prod:** it adds migration `0004` (one-reversal-per-row index, reversal-link CHECK). Run `scripts/backup-db.sh` first, then `scripts/prod.sh up -d --build`. The migration fails (and rolls back) if prod already holds a row that breaks the CHECK; none should, since nothing could create a reversal before.

**Applying Phase 5 to prod:** it adds migration `0005` (`import_batches.account_id`, `rejected_count`). Run `scripts/backup-db.sh` first (check the dump has data), then `scripts/prod.sh up -d --build`, check `alembic current` = 0005, `/health`, and a reconcile. The upload limit (2 MB) is enforced in the app *after* Starlette has buffered the body; a hard cap belongs in `Caddyfile.prod` (`request_body { max_size 3MB }` on the `/api/imports*` route) — not yet added.

**Applying Phase 2 to prod:** it adds migration `0002` (account `type`, `starting_balance`), so run
`scripts/prod.sh up -d --build` once after merging.

## Error tracking (Sentry) — optional, free tier

The backend initialises Sentry only when `SENTRY_DSN` is set; without it nothing is sent anywhere.
To turn it on: create a free account at sentry.io (no card should be needed — decline if asked),
create a Python/FastAPI project, copy its DSN into `backend/.env.prod` as `SENTRY_DSN=https://...`,
and restart the backend. Options are locked to finance-safe values: no request bodies, no PII, no
tracing. Free-tier limits and the paid alternative are in [`paid-options.md`](paid-options.md).
Without a DSN, `scripts/prod.sh logs backend` is the error log.

## If you were serious about this

Every cost decision in the project is tracked in [`paid-options.md`](paid-options.md); this table is the deploy slice of it.

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
