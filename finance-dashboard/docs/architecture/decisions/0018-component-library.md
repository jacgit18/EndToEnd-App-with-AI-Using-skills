# ADR 0018 — Component / UI library

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** the owner
- **Derived via:** `tech-decision-walkthrough` (Phase 7). Resolves the "component/UI library (lean Mantine/shadcn)" item deferred in `spec.md`.

## Context

Nine pages are built (accounts, categories, transactions, import, budgets, login and tests) with no shared UI library. The dashboard adds summary tiles, a month picker and two charts. The Budgets page already has a month picker.

## Decision

**No component library.** Keep the current approach and add a small tile component. Reuse the existing month-picker pattern.

## Alternatives considered

- **Mantine** — full kit with date pickers; adding it means restyling or living with two looks across nine pages. Lost on *migration cost* for a tile row and a select.
- **shadcn/ui** — copy-in components on Tailwind + Radix; needs Tailwind set up. Lost on *setup cost* and *consistency with existing pages*.

## Consequences

- No design system: consistency stays manual, and any new widget (date range, modal) is ours to build.
- No new dependency, no restyling of existing pages.
- Revisit if a feature needs a complex control (date-range picker, data grid) that costs more to hand-build than a library.
