# ADR 0015 — Frontend test tooling

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 13 (closeout audit)

## Context

React + Vite SPA (ADR-0008). The test plan (`docs/testing/finance-dashboard.md`) already set
the mix — unit ~55%, integration ~40%, one Playwright E2E path (~5%). This decision picks the
frontend unit/component layer and confirms the E2E tool. Backend tests are `pytest` (implied by
ADR-0002/0006; not separately contested).

## Decision

- **Vitest + React Testing Library** for unit / component / hook tests.
- **Playwright** for the single E2E smoke: log in → add a transaction → see it on the dashboard.
- Run in CI (ADR-0016): `vitest run` + `tsc --noEmit` + `vite build` on every PR; Playwright
  runs locally pre-release (no CI browser infra for the MVP, per the test plan).

## Alternatives considered

- **Jest + React Testing Library** — the long-time standard, but needs its own transform config
  separate from Vite (babel/ts), runs slower, and adds setup friction in a Vite project. Lost
  on *Vite integration* and *setup friction*.
- **Playwright for component tests too (one tool)** — Playwright component testing exists but
  spins a real browser per test and is less mature for unit-level work than Vitest + RTL. Lost
  on *speed* for the bulk unit layer; kept for E2E where a real browser is the point.

## Consequences

- Vitest shares Vite's config and transform pipeline — near-zero extra setup — and its API is
  Jest-compatible, so RTL patterns and docs apply directly.
- Vitest is younger than Jest but is now the default for Vite projects and stable.
- The CSV-parser normalization function, the money/`Decimal` helpers, and the dashboard
  aggregation math are backend `pytest` units (test plan) — this ADR covers the React side.
