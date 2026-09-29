# ADR 0020 — Release / hosting platform

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 8).

## Context

Phases 1-7 are deployed via Docker Compose on a single VPS. For Phase 8 the owner proposed
Kubernetes as the release strategy, citing the existing Docker setup and the learning/hiring
value of K8s experience. Project is solo, public, currently has no real user data (owner is
experimenting), and free-first is a standing constraint alongside learning value.

## Decision

**Docker Compose on the existing VPS stays the real deployment target.** Images are built in
CI, tagged by commit SHA, pushed to a registry (ADR-0021), and deployed via
`docker compose pull && up -d` over SSH from CI (deploy trigger; see Consequences).

For Kubernetes learning/hiring-signal reps specifically: run **k3s** (lightweight Kubernetes)
as a **side track** — either on a second small VPS or the same one — used for practice
(`kubectl`, Helm, rolling updates), not for the real app's production traffic.

## Alternatives considered

- **k3s as the real deployment.** More operational surface (control plane + node components)
  than a single low-traffic service needs; kept as the side-track option instead of the
  production path.
- **AWS EKS.** Rejected as the production target. EKS's control-plane fee is a flat
  ~$0.10/hr (~$73/month) before any workload runs, plus EC2 worker nodes (~$15-30/month) and
  a load balancer (~$18/month) — realistically $100-150+/month minimum. That cost exists
  regardless of traffic. Teams adopt Kubernetes when they have many services and multiple
  teams sharing a platform; a single-service solo app on EKS is the textbook example of
  infrastructure sized ahead of the problem — itself something interviewers probe for. Not
  revisited unless the project grows into several independently-scaled services.
- **PaaS (Fly.io / Render).** Not evaluated in depth — doesn't serve the stated learning goal
  (K8s exposure), and the VPS is already paid for and working.

## Consequences

- Deploy trigger: SSH from CI to the VPS with a deploy key, matching ADR-0016/0019's plan.
  **The runner stays GitHub-hosted** — it SSHes out, rather than a self-hosted runner
  listening on the VPS, to avoid exposing the deploy target to a public repo's CI jobs.
- k3s side-track: free software on a $5-7/month VPS (no control-plane fee), separate from the
  production app; gives real `kubectl`/Helm reps for the resume without EKS's bill or the
  operational load of running the actual finance-dashboard on it.
- Revisit EKS/managed K8s only if the app splits into multiple independently-scaled services
  that justify a shared orchestration platform.
