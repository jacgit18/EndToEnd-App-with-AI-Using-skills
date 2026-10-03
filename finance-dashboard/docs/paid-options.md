# Where money could come in

Standing preference: keep this project free. Every place a cost *could* appear is listed here,
with the free choice in use and the paid one to pick if this were a real product. Add a row
whenever you add a service, dependency or tier. **Prices are from memory (2026-09-24) and not
re-verified — check the provider's pricing page before relying on a number.**

| Area | Free choice in use | What could cost money | Paid option if serious | Where it shows up |
|---|---|---|---|---|
| Hosting | Your own machine, Docker | Electricity; the app is down when the machine is off | Small VPS (Hetzner, DigitalOcean), ~$5–7/mo | `compose.prod.yaml`, `deploy.md` |
| Public URL / HTTPS | Cloudflare named tunnel (free account), host systemd `cloudflared`, on the free DNSHE domain `findash.us.ci` (from 2026-10-03; before that a quick tunnel) | Free-domain providers can change terms or reclaim names. Registered 2026-10-03, **expires 2027-10-03 15:05**; renewal is free and opens 180 days before expiry (from about 2027-04-06), then 30 days grace and 30 days redemption. Calendar reminders set for 2027-04-06 and 2027-09-19. Site is down whenever this machine or the service is | Own domain (~$10–12/yr) + named tunnel (free with the domain) or A record + Caddy's Let's Encrypt | `Caddyfile.prod`, `compose.prod.yaml` |
| Error tracking | Sentry free Developer plan, code inert until `SENTRY_DSN` is set | Past the monthly error quota, events are dropped or an upgrade is prompted; 1 seat only | Sentry Team, ~$26+/mo | `app/config.py`, `app/main.py` |
| Database | Postgres in a container | Nothing | Managed Postgres with point-in-time restore (Neon/Supabase free tiers exist; paid ~$10–25+/mo) | `compose.prod.yaml` |
| Backups | `pg_dump` cron to local disk | Off-box storage beyond a free allowance (Backblaze B2: first 10 GB free, then per-GB) | Managed backups / VPS snapshot add-on (~20% of VPS price) | `scripts/backup-db.sh` |
| Uptime alerts | None yet (ADR-0013 names UptimeRobot free) | Free plan has a check interval limit and no SMS | Paid monitor, ~$7+/mo | not built |
| CI | GitHub Actions, free for public repos (ADR-0016, reaffirmed ADR-0019) | Private repos have a monthly minutes cap | Paid minutes, or a self-hosted runner (rejected for this repo — public-repo security exposure, see ADR-0019) | `.github/workflows/` (Phase 8) |
| Container registry | GHCR, free and unlimited for a public repo (ADR-0021) | Nothing today; would need a private-repo minutes-style cap or a switch to a paid registry | AWS ECR (~$0.10/GB-mo storage + egress) — only worth it once other infra is already on AWS | Phase 8 CI workflow |
| Container images (base images) | Docker Hub pulls (postgres, caddy, cloudflared, node) | Anonymous pull rate limits, free with an account | Docker Pro / a registry mirror | `compose*.yaml` |
| Kubernetes reps | k3s side track on the existing/a second $5-7/mo VPS, free software (ADR-0020) | Nothing beyond the VPS already budgeted for hosting | AWS EKS: ~$0.10/hr control plane (~$73/mo) + worker nodes (~$15-30/mo) + load balancer (~$18/mo) ≈ $100-150+/mo minimum, regardless of traffic — not adopted; revisit only if multiple independently-scaled services exist | not built |
| Feature flags | Roll-your-own `feature_flags` table + admin toggle, free (ADR-0022) | Nothing | Unleash self-hosted (free) as a middle step, or LaunchDarkly (free tier thin; real pricing scales with MAU into the hundreds/mo) if flags ever need to be shared across services or non-technical stakeholders | not built |
| Auth | Single owner login, argon2 + sessions | Nothing | Hosted auth (Auth0/Clerk) only if multi-user; free tiers exist | ADR-0010 |
| Bank connectivity | None (manual entry / CSV import) | Plaid and similar charge per connected account after a trial | Plaid, ~usage-based | not in scope |

**Signup traps:** some "free" tiers ask for a card up front. Decline and pick another, or use a
virtual card with a limit. Nothing in Phase 1 needs one.

**Privacy note tied to cost:** the Sentry setup sends no request bodies, no PII and no traces
(`app/main.py`), because transaction descriptions and amounts must not leave the machine. Turning
those on for richer debugging is a paid-tier-adjacent decision as well as a privacy one.
