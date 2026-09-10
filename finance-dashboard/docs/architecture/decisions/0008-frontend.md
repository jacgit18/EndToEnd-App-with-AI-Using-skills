# ADR 0008 — Frontend approach

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 7 of the stack

## Context

Separate frontend deployable (scope), REST/JSON API (ADR-0007), one desktop-browser client.
The demanding UI is the CSV import wizard (upload → preview → map columns → confirm) and the
dashboard charts — genuinely stateful client-side UI. The owner has prior **React** experience,
has **not** used Vite, and rates frontend as their weaker area.

## Decision

**React + Vite** (with TypeScript).

- Vite provides the dev server (hot module replacement) and the production static build, and
  the dev proxy that forwards `/api` to the FastAPI backend so dev is single-origin (no CORS).
- Data fetching via TanStack Query (React Query).

## Alternatives considered

- **Vue + Vite** — gentler learning curve, less boilerplate. Lost on *transferability* (React
  is the dominant skill and the owner already has React experience) and *ecosystem* (React's
  chart/table/form library selection is the deepest, which matters for a dashboard-heavy app).
  The reasonable override if "gentlest path to a working UI" outweighed "build on existing
  React experience."
- **Svelte / SvelteKit** — least boilerplate, smallest runtime. Lost on *ecosystem* (thinnest
  of the three) and *transferability*; SvelteKit also pulls in a server model not needed here.
- **Server-rendered + htmx** — rejected: the CSV column-mapping wizard is exactly the rich
  local state htmx is not built for, and the scope wants a separate frontend.
- **Meta-framework (Next.js / Remix)** — rejected: reintroduces a Node server just for the
  frontend, on top of the Python backend — two servers where one SPA + one API is simpler.

## Consequences

- Steepest learning curve of the three SPA options — hooks and the render model are real study
  time. Mitigated by the owner's existing React exposure.
- A separate build toolchain and container for the frontend (accepted; the scope wants this).
- **Feeds two build-time decisions** (already on the scope's "decide during implementation"
  list): a component/UI library (e.g. Mantine, shadcn/ui) to avoid hand-rolling primitives,
  and a charting library with sane defaults (e.g. Recharts) rather than raw D3 — both weighted
  toward "batteries included" given the weaker-frontend-skills constraint.
- The `incremental-build-pacing` build phase is expected to go especially slowly on the
  frontend files.
