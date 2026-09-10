# ADR 0009 — Frontend state management

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 7b (sub-decision of the
  frontend, ADR-0008)

## Context

React + Vite SPA (ADR-0008) against a REST/JSON API (ADR-0007). Single user, one browser
client. The app's state is dominated by server data (accounts, transactions, dashboard
aggregations); genuinely global non-server client state is minimal (the authed user, a
notification/toast queue, maybe a theme).

## Decision

**No dedicated global-state library.** State is handled per category:

| Category | Tool |
|---|---|
| Server state / cache | **TanStack Query** (already in ADR-0008) — caching, refetch, loading/error, invalidate-on-mutation |
| URL state (selected month, account filter, page) | **React Router** — the URL is the state; keeps views bookmarkable and back-button-correct |
| Local UI state (form fields, open modal, CSV wizard step) | React `useState` / `useReducer` |
| Global client state (authed user, toasts, theme) | `useContext` + `useState` |

**Zustand** may be added later *only if* a concrete pain appears — some genuinely global client
state that Context makes awkward. Not adopted pre-emptively.

## Alternatives considered

- **Zustand (or Jotai / Nano Stores)** — minimal (~1 KB), low boilerplate. Lost on *fit*:
  there is currently no global-client-state problem for it to solve. It is the designated
  low-cost upgrade if one emerges.
- **Redux Toolkit** — industry standard for large apps, best devtools, most transferable as a
  résumé skill. Lost on *fit*, *boilerplate/concept load*, and *weight* — overkill for an app
  whose state is ~80% server cache (handled by TanStack Query) plus a little local UI state.
  Deferring it is deliberate: learning Redux on an app that doesn't need it teaches the
  boilerplate, not the judgement of when to reach for it.
- **Jotai / Recoil (atomic state)** — elegant for fine-grained reactivity; no such need here.

## Consequences

- One tool per state category; no single global store to funnel everything through.
- If the app grew (more views with shared client state, or offline support), revisit — Zustand
  first, Redux only if devtools/middleware/time-travel become genuinely useful.
- Backend note (raised in the same discussion): there is no equivalent "state library"
  decision on the backend — a well-built API keeps request handlers stateless and pushes
  durable state to the database; server-side session storage (if chosen in ADR-0010 auth) is
  the one deliberate piece of backend state.
