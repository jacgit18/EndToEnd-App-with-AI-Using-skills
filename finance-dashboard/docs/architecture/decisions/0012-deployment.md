# ADR 0012 — Deployment target

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 10 (`deployment-strategy`
  lens; scope constraints mostly fix it)

## Context

Scope: self-hosted, ~$0 cost cap, single region, "a restart is acceptable" (no HA). ADR-0010
adds: **public URL over HTTPS** and **login rate limiting**. Owner goal: go through the whole
deployment process hands-on, not have it abstracted. Components: Postgres, FastAPI backend,
built React static files.

## Decision

**Single small VPS (~$5–7/mo) running Docker Compose, with Caddy as the reverse proxy and TLS
terminator.**

- Compose services: `db` (Postgres + named volume), `backend` (FastAPI via `uv`), `caddy`
  (reverse proxy).
- Caddy auto-provisions and renews a Let's Encrypt certificate; it serves the built React
  static files and proxies `/api` + `/health` to the backend — one origin, which ADR-0010's
  cookie auth needs.
- Login rate limiting: Caddy `rate_limit` (or FastAPI middleware) on `POST /api/auth/login`.
- Backups: `pg_dump` on a cron (or a volume snapshot), dumps stored off-box.
- Deploys: `docker compose pull && docker compose up -d` (rolling). A brief restart is
  acceptable per scope.
- A registered domain (~$12/yr) with an A record to the VPS.

## Alternatives considered

- **PaaS (Render / Railway / Fly.io)** — genuinely removes the ops burden (TLS, deploys, DB
  backups). Lost on *learning value* (abstracts the mechanics the owner wants to do) and
  *dev/prod parity*; free tiers sleep/throttle, ~$7–20/mo for always-on + a DB.
- **Serverless (Lambda + API Gateway + Aurora Serverless, or Cloud Run)** — lost on *fit to
  scope* (not self-hosted), plus an awkward Lambda↔Postgres connection story and heavy vendor
  surface for one user.
- **Bare metal on the VPS (systemd, no containers)** — lost on *dev/prod parity* (ADR-0004
  valued the same image both places) and *ops fiddliness*.

## Cost perspective

- **This plan:** ~$5–7/mo VPS + ~$12/yr domain. Caddy makes TLS free and automatic. The real
  cost is owner time: OS patching, the backup cron, disk monitoring — the burden a PaaS would
  absorb, accepted here because doing it is the goal.
- **Realistic scale (~50k MAU):** re-platform off a single box — PaaS or a small ECS/Kubernetes
  setup with managed Postgres + a load balancer + a CDN for the static frontend. Dominant
  lines: DB pair $250–600/mo (per ADR-0004), app compute (2–4 instances) $50–200/mo,
  CDN/egress $20–100/mo. A deliberate future migration, not provisioned now.

### Re-platform path, in more depth (not provisioned — reference only)

If the single-VPS approach were ever outgrown, the move is staged, not a single jump:

1. **RDS (managed Postgres)** first. Highest value for lowest effort — it removes the box's
   single point of failure and hands off backups/patching/failover, which is most of what the
   owner currently does by hand (`backup-db.sh`, the reconcile cron, OS updates). ~$60–200/mo
   for a small Multi-AZ instance, well below the $250–600/mo "DB pair" figure above, which
   assumes a heavier read-replica setup than this app needs at first.
2. **ECS Fargate (not EKS), behind an ALB.** Same Docker images already built for Compose run
   as Fargate tasks with no Dockerfile changes. An ALB replaces Caddy as the TLS terminator/LB;
   Fargate autoscales task count on CPU/request count instead of the "a restart is acceptable"
   posture this ADR accepts today.
3. **S3 + CloudFront** for the built React static files, replacing Caddy's static-file serving.
   Route53 for DNS instead of the current A record.
4. **Kubernetes (EKS) is deliberately skipped in this path.** One backend service + one
   database does not need an orchestrator — ECS Fargate gives the same rolling-deploy and
   autoscaling value with a fraction of the operational surface (no control plane version
   upgrades, no cluster-level IAM/networking, no YAML beyond a task definition). EKS would only
   earn its keep if the app split into several independently-deployed services, needed
   multi-cloud portability, or joined a fleet of apps sharing one platform team's tooling —
   none of which applies to a single owner running one FastAPI service. Per
   `microservices-decision`, adopting an orchestrator ahead of that need is complexity bought
   before it's owed.

**Trigger, not schedule:** none of this is time-boxed to a phase number. The signal to start
step 1 is the VPS's ops burden (patch cadence, backup verification, a reboot outage) actually
costing more than ~$60–200/mo would save, or a real uptime requirement appearing — not
reaching a particular feature milestone.

## Consequences

- Owner operates the box: updates, backups, disk. No HA — a reboot means a short outage
  (accepted).
- HTTPS + one origin are in place from first deploy, which ADR-0010's cookie auth requires.
- `deployment-strategy` proper (rollout mechanics, blue/green, etc.) is out of scope at one
  box / one user — revisit with the scale re-platform.
- Observability approach is ADR-0013 (decision 11).

## Amendment (2026-10-03): what was actually built, what was learned, and the hobby-to-business path

**What changed from the decision above.** The VPS was replaced by the owner's own machine, reached
through a Cloudflare named tunnel on a free domain (`findash.us.ci`), to keep the cost at $0.
Everything else (Compose, Caddy, Postgres, migrations on start) is as decided. Operating detail
is in `docs/deploy.md`.

### What was learned

- **"Deployed" is not "production-grade."** Production means being reachable and doing its job
  with the user not watching. This stack is reachable. It is not yet unattended: it is up only
  while one machine, Docker and `cloudflared` are, and nothing alerts when it isn't.
- **A backup is not a backup until it has been restored.** Dumps were scheduled nightly from
  2026-09-25 but the cron job never fired (found 2026-10-03; see `~/Documents/TODO.md`), so the only dumps are
  manual ones, and the restore was never exercised. An untested backup is a hope, not a recovery plan.
  - **Restore drill:** restore the newest dump into a scratch database (never over live data),
    then check it matches: row counts per table, and one known dashboard figure for a month,
    against prod. Record the date, the dump used and the result in `docs/deploy.md`. Repeat on a
    schedule, and always after changing the backup script or the schema tooling.
- **A restore drill measures two things:** that the data comes back, and how long it takes
  (the real recovery time, which nobody knows until they have done it once).
- **Secrets and config failures are quiet.** Doubled `$` in argon2 hashes and a quoted `*` in a
  shell `-c` string both failed without an error. Only a real-environment check caught them, so
  each prod change needs a smoke test, not just passing unit tests.
- **Free infrastructure has hidden dependencies.** A quick tunnel's random URL died when the
  connection dropped. The domain, its nameservers and the tunnel token are now single points of
  failure with no support behind them.
- **Verification records need numbers written down at the time.** The Phase 7 dashboard check
  has no per-figure values and cannot be reconstructed (`docs/phase7-verification.md`).

### Hobby-grade prod vs real-world prod

| Concern | Here (hobby grade) | Typical real-world prod |
|---|---|---|
| Hosting | One home machine | Cloud hosts across 2+ zones, or a managed platform |
| Availability | Up while the machine is; no target | Stated SLO (e.g. 99.9%), measured |
| Database | Containerized Postgres, one volume | Managed Postgres, Multi-AZ failover, point-in-time restore |
| Backups | Nightly dump to the same machine's disk, restore untested | Off-site, encrypted, automated restore tests, defined RPO/RTO |
| Environments | Dev and prod only | Dev, staging that mirrors prod, prod |
| Deploys | Manual `scripts/prod.sh up -d --build` on the host | CI/CD pipeline, versioned images, rollback in minutes |
| Monitoring | None beyond `/health` by hand | Uptime checks, metrics, alerting, on-call |
| Secrets | Gitignored `.env.prod` files | Secret manager, rotation, audit log |
| Access control | One owner, one login | Least-privilege roles, MFA, audit trail |
| Security upkeep | Manual OS and image updates | Automated patching, dependency and vulnerability scanning |
| Domain / DNS | Free domain, no support | Paid registrar, auto-renew, registrar lock |
| Change process | Owner decides | Review, change log, incident process and postmortems |

### Path from hobby grade to business grade

Order by risk removed per effort. The trigger rule above still applies: do a step when its cost
is justified, not on a calendar.

1. **Prove recovery:** run the restore drill, record RTO, and copy dumps off the machine.
   Costs nothing and removes the worst failure (permanent data loss).
2. **Know when it's down:** a free external uptime check on `/health`, with an email or push alert.
3. **Always-on host:** move the same compose file to a ~$5-7/mo VPS (this ADR's original
   decision). This removes "my laptop is off" as an outage cause.
4. **Staging environment:** a second copy of the stack to rehearse deploys and migrations.
5. **Automated deploys:** CI builds and pushes a versioned image (ADR-0016, ADR-0021) and a
   pipeline deploys it, with a one-command rollback.
6. **Managed database:** RDS or equivalent with point-in-time restore, per the re-platform path above.
7. **Real observability:** metrics, logs, alerts and a written SLO (ADR-0013).
8. **Secrets and access:** a secret manager, rotation, MFA everywhere, least-privilege roles.
9. **Redundancy and load balancing:** the ECS Fargate + ALB step above, only when an uptime
   requirement exists.
10. **Process:** a runbook, an incident template and postmortems. This is the step hobby projects
    skip, and it is much of what separates "business grade" from "bigger hobby."

Business grade is a set of promises (an uptime target, a recovery time, who gets paged), not a
set of technologies. Define the promises first and pick only the tooling that keeps them.
