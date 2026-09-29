# ADR 0022 — Feature flags

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 8).

## Context

The owner wants a feature-flag mechanism as part of the release-strategy hardening (gradual
rollout / kill switch for new dashboard features going forward).

## Decision

**Roll our own** — a `feature_flags` table (flag name, enabled bool, optional rollout
percentage) plus a small admin toggle endpoint, checked from application code at the relevant
call sites.

## Alternatives considered

- **LaunchDarkly.** Rejected. Market-leading name recognition, but the free tier is thin
  (limited seats/MAU) and real pricing scales with monthly active users into the hundreds of
  dollars a month — a cost dimension only justified at team/company scale, not a solo project
  with no real users yet.
- **Unleash (open source).** A reasonable middle ground — free to self-host or use on its free
  hosted tier — but more setup (a service to run, an SDK to wire in) than a flags table
  delivers for a single-app, single-operator project. Named here so the tradeoff is on record;
  revisit if flags need to be shared across multiple services later.

## Consequences

- No new infrastructure or recurring cost.
- Teaches the actual mechanism (rollout percentage, kill switch) rather than a vendor's SDK —
  the transferable part of "feature flags" as a concept.
- If the project later needs flags shared across multiple independent services or
  non-technical stakeholders toggling flags via a UI, revisit Unleash at that point.
