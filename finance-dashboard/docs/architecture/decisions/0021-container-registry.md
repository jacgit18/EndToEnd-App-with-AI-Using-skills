# ADR 0021 — Container registry

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 8).

## Context

Phase 8 needs a registry for CI-built, SHA-tagged images ahead of the Compose deploy (ADR-0020).
The owner leaned toward AWS ECR.

## Decision

**GitHub Container Registry (GHCR).**

## Alternatives considered

- **AWS ECR.** Rejected for now. Storage (~$0.10/GB-month) and egress cost is trivial at this
  image count/pull volume, so cost wasn't the blocker — the blocker is that it requires an AWS
  account, an IAM policy scoped to push/pull, and AWS credentials held in CI secrets, for a
  deployment target (a plain VPS, ADR-0020) that otherwise never touches AWS. That's new
  surface area with no capability gained. Revisit if a later decision puts real infrastructure
  on AWS (e.g. the EKS side-track going further, or RDS) — at that point the IAM work already
  exists for other reasons and ECR becomes close to free to add.
- **Docker Hub.** Rejected — free tier is rate-limited (100 anonymous / 200 authenticated
  pulls per 6 hours), which can break a deploy under retries, with no advantage over GHCR to
  offset it.

## Consequences

- Free and unlimited for a public repo; no new account.
- Authenticates via `GITHUB_TOKEN` already available in Actions — no extra secret to manage.
- CI pushes `ghcr.io/<owner>/<image>:<sha>`; the Compose deploy pulls that tag.
