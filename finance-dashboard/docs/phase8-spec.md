# Phase 8 spec — CI/CD + prod-hardening

Written 2026-09-29 via `spec-drift-gate`. Decisions: ADR-0019 (CI reaffirmed: GitHub Actions
only), ADR-0020 (release platform: Compose+VPS stays prod, k3s side-track for K8s reps),
ADR-0021 (registry: GHCR), ADR-0022 (feature flags: roll-your-own table). Tradeoffs for each
were already weighed via `tech-decision-walkthrough` and are recorded in those ADRs — not
re-derived here.

**Build has not started.** The owner asked for this spec written now, explicitly to hold
before beginning any slice.

## Problem

Phases 1-7 shipped by hand: no automated checks run before code reaches `main`, and every
deploy is a manual SSH session on the VPS. A broken change can land on `main` unnoticed, and
there is no repeatable, auditable path from "commit merged" to "running in prod." Secondary
goal, made explicit by the owner: build real, resume-worthy CI/CD and (lightweight) Kubernetes
experience, without provisioning infrastructure this single-owner, no-real-data app doesn't
need (ADR-0020's rejection of AWS EKS as the production target).

## Scope boundary

### In scope
- **CI workflow** (`.github/workflows/ci.yml`, ADR-0019): on every PR and push to `main` —
  backend (`uv sync`, `ruff check` + `ruff format --check`, Postgres service container +
  `alembic upgrade head`, `pytest -q`) and frontend (`npm ci`, `tsc --noEmit`, `vitest run`,
  `vite build`) as two jobs. Confirm `ruff` is actually configured in
  `backend/pyproject.toml` before assuming the lint step exists.
- **Image build + push** (ADR-0021): on merge to `main`, build the backend and frontend
  images and push to GHCR tagged by commit SHA.
- **Deploy trigger** (ADR-0020): a workflow, triggered manually (`workflow_dispatch`) — not
  automatically after a green build — that SSHes from a GitHub-hosted runner to the VPS with a
  deploy key and runs `docker compose pull && up -d` against the new SHA tag. Manual trigger
  matches the standing "a prod deploy needs an explicit fresh 'deploy to prod'" constraint;
  automatic deploy-on-merge is explicitly not being adopted this phase.
- **Feature flags** (ADR-0022): a `feature_flags` table (name, enabled bool, optional rollout
  percentage) with a migration, plus a small admin-only endpoint to list/toggle flags. No
  flags gate any real feature yet — this phase ships the mechanism, not a flagged feature.
- **k3s side-track** (ADR-0020): install k3s on a VPS (the existing one or a second cheap one,
  owner's call at build time) for hands-on `kubectl`/Helm practice. Explicitly **not** wired to
  serve the real finance-dashboard traffic.
- **Pre-commit config** (mentioned in the prior handoff): fast local mirror of the CI lint/
  typecheck steps, informational only — CI stays the authority.
- **Docs**: `docs/architecture/stack-walkthrough.md` gets a Phase 8 row; `backlog.md` gets a
  Phase 8 "Built" note once slices land; `paid-options.md` already updated with this phase's
  free/paid lines (done in the ADR PR, #103).

### Out of scope (this phase)
- AWS ECR, AWS EKS, Jenkins, LaunchDarkly, Unleash — all rejected in the ADRs; not revisited
  here.
- Auto-deploy after a green build (kept manual; revisit as a later decision if wanted).
- Rollback automation — a deliberate rollback *drill* is named in the prior handoff's ladder
  but is its own slice, not bundled into the deploy-trigger slice.
- Uptime/error alerting beyond what ADR-0013 (Sentry) already covers.
- Backups / restore drill — deprioritized per the prior handoff (no real data yet).
- Any flag actually gating a shipped feature — that's a future phase's decision once the
  mechanism exists.
- Domain/DNS/TLS changes — unrelated to this phase's ADRs.

## Controlled-experiment slice

The CI workflow itself is the uncertain piece — first time wiring GitHub Actions with a
Postgres service container against this repo's Alembic migrations and test suite. Slice 1 is
**CI only, no build/push/deploy step** — cheap to discard or fix if the workflow doesn't
actually catch what it should, before committing to the rest of the pipeline on top of it.

## Slices

1. `.github/workflows/ci.yml` — lint + backend tests (Postgres service container,
   `alembic upgrade head`, `pytest -q`) + frontend (`tsc`, `vitest`, `vite build`). Verify it
   actually fails on a deliberately broken commit before trusting it.
2. Add the build-and-push-to-GHCR job, gated to `main` only, tagged by commit SHA.
3. `feature_flags` table (migration) + admin toggle endpoint + tests.
4. Deploy-trigger workflow (`workflow_dispatch`, SSH + `docker compose pull && up -d`) —
   dry-run against a non-prod path or a deliberate throwaway tag before pointing it at real
   prod.
5. k3s side-track setup, kept separate from the real deploy path; basic `kubectl`/Helm reps.
6. Pre-commit config mirroring CI's fast checks.
7. Docs: stack-walkthrough row, backlog note, real verification (a broken commit actually
   blocked, a real deploy actually run through the new trigger once), then closeout per
   `incremental-build-pacing`.

**Build does not start on slice 1 until the owner says go** — this spec is written ahead of
that decision, per the owner's explicit request this session.

## Tripwires (stop and ask)

- `ruff` turning out to not be configured in `backend/pyproject.toml` (ADR-0016/0019 assumed
  it exists) — a real config decision, not a default to pick silently.
- Any step that would require a self-hosted runner (public-repo security exposure named in
  ADR-0019/0020) — stop and confirm before adding one, don't default to it for convenience.
- The deploy-trigger workflow needing anything beyond a deploy key + `docker compose` commands
  (e.g. secrets rotation, multi-host targeting) — that's new scope, not this slice's default.
- Any point where auto-deploy-on-merge looks tempting "since it's already green" — that's the
  explicitly-rejected default; stays manual unless the owner reopens ADR-0020's Consequences.

## Progress

Not started. ADRs 0019-0022 merged (PR #103, `main` at `8040768`). This spec written and held
per the owner's request.
