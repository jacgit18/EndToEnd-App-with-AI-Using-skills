# ADR 0017 — Charting library

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 7, S7 dashboard). Resolves the "charting library (lean Recharts)" item deferred in `spec.md` and ADR-0008.

## Context

S7 needs two charts: per-category actual vs budget (bars) and a 6-month net cash-flow trend. A dozen data points each, one user. Every figure must reconcile with the transactions list, so exact values should be visible as text. Frontend tests run in Vitest + jsdom (ADR-0015), which has no layout engine. Cost cap: free only; every candidate is MIT and $0.

## Decision

**Visx** (`@visx/scale`, `@visx/shape`, `@visx/axis`, and others only as needed), rendered as SVG with explicit `width`/`height`. Charts are written as small components that take plain data and render their own value labels.

## Alternatives considered

- **Recharts** — the ADR-0008 lean. Fastest for these two charts (roughly a third of the code), but its responsive container measures width, which is 0 in jsdom, so tests need a size shim; larger bundle. Lost on *testability* and *weight*; it stays the fallback.
- **Chart.js** — canvas output has no DOM to assert on. Lost on *testability* and *accessibility*.
- **Hand-rolled SVG** — smallest dependency, but two charts with axes, negative values and a trend line mean owning scale and tick maths. Lost on *effort*.

## Consequences

- More chart code than Recharts (estimated 80-120 lines per chart, not measured), and layout choices (margins, ticks, tooltip) are ours.
- No jsdom size shim; fixed-size SVG is assertable and fits the mutation-test habit.
- **Check before installing:** Visx's peer-dependency range against React 18.3. If it doesn't fit, revisit this ADR rather than forcing it.
- If the bar chart alone costs more than about a day of layout work, reopen and consider Recharts.
- Charts use the `dataviz` skill for colour and layout so figures stay legible and accessible.
- Cost: $0, no paid alternative needed.
