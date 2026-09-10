# ADR 0007 — API style

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 6 of the stack
  (`api-interface-style` lens applied; inputs confirmed from scope + earlier ADRs, gate not
  re-run from zero)

## Context

- **Surface:** the desktop-browser SPA talking to the FastAPI backend — one surface, two ends.
- **Consumers:** one client type, same repo, release controlled by the owner. No public,
  external, or mobile consumers (mobile is explicitly out of scope).
- **Interaction shape:** request→response only — resource CRUD, CSV upload, dashboard
  aggregation reads. No server push, no streaming, no real-time need (data changes only when
  the single user changes it; poll-on-refresh suffices).
- **Query shape:** fixed resources, known screens; over/under-fetching is not an observed
  problem. Dashboard endpoints are computed reads, not resources.
- **Stability:** internal, single consumer, free to churn.

## Decision

**REST / HTTP-JSON**, with an OpenAPI description.

- Resource endpoints: `/api/accounts`, `/api/transactions`, `/api/categories`,
  `/api/budgets`, `/api/imports`.
- A small set of **computed read-model endpoints** for the dashboard
  (e.g. `GET /api/dashboard?month=YYYY-MM` returning the summary tiles, category-vs-budget,
  and the 6-month trend) — a view, not a resource, which is normal within REST.
- FastAPI generates the OpenAPI spec; a typed TypeScript client is generated from it for the
  frontend (recovers some of the end-to-end type safety a single-language stack would give).

**Serialization:** JSON. Money fields are strings (per ADR-0005).

**Deferred (named, not decided here):** URL versioning scheme, auth scheme (→ ADR-0009,
decision 8), pagination conventions for the transactions list.

## Alternatives considered

- **GraphQL** — lost on *query-variability payoff*: one known client with fixed screens gets no
  value from client-specified query shapes, while paying for a resolver layer, N+1 and
  depth/cost-limiting concerns, and a second schema to maintain.
- **gRPC / gRPC-web** — lost on *fit to consumer*: browsers cannot speak gRPC without a proxy
  layer; it is a service-to-service tool, not a browser-edge one.
- **WebSocket / SSE** — not applicable: no real-time requirement.

## Consequences

- The API is conventional REST — lowest operational weight, native FastAPI support, auto docs.
- The dashboard is served by purpose-built aggregation endpoints (raw SQL / Core per ADR-0006),
  not by the client assembling many resource calls.
- If a second, materially different client ever appears (out of scope now), revisit — REST +
  OpenAPI + a generated client is still a reasonable base for that case.
