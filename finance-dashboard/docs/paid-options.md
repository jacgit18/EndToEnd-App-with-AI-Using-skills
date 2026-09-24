# Where money could come in

Standing preference: keep this project free. Every place a cost *could* appear is listed here,
with the free choice in use and the paid one to pick if this were a real product. Add a row
whenever you add a service, dependency or tier. **Prices are from memory (2026-09-24) and not
re-verified — check the provider's pricing page before relying on a number.**

| Area | Free choice in use | What could cost money | Paid option if serious | Where it shows up |
|---|---|---|---|---|
| Hosting | Your own machine, Docker | Electricity; the app is down when the machine is off | Small VPS (Hetzner, DigitalOcean), ~$5–7/mo | `compose.prod.yaml`, `deploy.md` |
| Public URL / HTTPS | Cloudflare quick tunnel (no account) | Nothing today. Quick tunnels are "for testing", no uptime promise, URL changes on restart | Own domain (~$10–12/yr) + named tunnel (free with the domain) or A record + Caddy's Let's Encrypt | `Caddyfile.prod`, `compose.prod.yaml` |
| Error tracking | Sentry free Developer plan, code inert until `SENTRY_DSN` is set | Past the monthly error quota, events are dropped or an upgrade is prompted; 1 seat only | Sentry Team, ~$26+/mo | `app/config.py`, `app/main.py` |
| Database | Postgres in a container | Nothing | Managed Postgres with point-in-time restore (Neon/Supabase free tiers exist; paid ~$10–25+/mo) | `compose.prod.yaml` |
| Backups | `pg_dump` cron to local disk | Off-box storage beyond a free allowance (Backblaze B2: first 10 GB free, then per-GB) | Managed backups / VPS snapshot add-on (~20% of VPS price) | `scripts/backup-db.sh` |
| Uptime alerts | None yet (ADR-0013 names UptimeRobot free) | Free plan has a check interval limit and no SMS | Paid monitor, ~$7+/mo | not built |
| CI | None (no CI in the repo) | GitHub Actions is free for public repos; private repos have a monthly minutes cap | Paid minutes / self-hosted runner | not built |
| Container images | Docker Hub pulls (postgres, caddy, cloudflared, node) | Anonymous pull rate limits, free with an account | Docker Pro / a registry mirror | `compose*.yaml` |
| Auth | Single owner login, argon2 + sessions | Nothing | Hosted auth (Auth0/Clerk) only if multi-user; free tiers exist | ADR-0010 |
| Bank connectivity | None (manual entry / CSV import) | Plaid and similar charge per connected account after a trial | Plaid, ~usage-based | not in scope |

**Signup traps:** some "free" tiers ask for a card up front. Decline and pick another, or use a
virtual card with a limit. Nothing in Phase 1 needs one.

**Privacy note tied to cost:** the Sentry setup sends no request bodies, no PII and no traces
(`app/main.py`), because transaction descriptions and amounts must not leave the machine. Turning
those on for richer debugging is a paid-tier-adjacent decision as well as a privacy one.
