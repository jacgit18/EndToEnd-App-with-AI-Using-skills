# ADR 0019 — CI provider, reaffirmed (GitHub Actions only)

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 8). Reopens ADR-0016 at the owner's
  request to consider adding Jenkins; re-confirms the original decision.

## Context

ADR-0016 chose GitHub Actions alone. For Phase 8 the owner proposed adding Jenkins alongside
it for the CI/CD hardening pass, partly for the resume/hiring signal. Repo is solo-maintained
and public.

## Decision

**GitHub Actions only.** ADR-0016's workflow plan stands (lint, pytest with a Postgres service
container + `alembic upgrade head`, frontend `tsc`/`vitest`/`build`). No Jenkins in this repo.

## Alternatives considered

- **GitHub Actions + Jenkins.** Rejected. Running two pipelines for one solo repo means
  maintaining two configs that can drift, plus operating a self-hosted Jenkins instance
  (patching, plugins, uptime). A self-hosted Jenkins runner reachable from a public GitHub
  repo is also a real attack surface — a malicious PR's CI job can reach that box unless
  carefully gated. The hiring-signal gain is thin: "ran two CI systems on one small repo"
  reads as noise, not depth.
- **Jenkins only.** Rejected for the same self-hosting/security reasons, with no Actions
  layer to fall back on.

## Consequences

- No added infrastructure or cost; stays free and unlimited on a public repo.
- Jenkins exposure, if wanted for hiring signal, gets pursued as a **separate throwaway
  project** (e.g. a local Jenkins container building a toy app) rather than wired into this
  repo's real pipeline.
