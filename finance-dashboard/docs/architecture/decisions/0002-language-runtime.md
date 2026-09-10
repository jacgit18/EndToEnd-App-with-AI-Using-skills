# ADR 0002 — Language / runtime

- **Status:** Accepted
- **Date:** 2026-09-09
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 1 of the stack

## Context

Greenfield self-hosted personal finance dashboard, solo maintainer, no deadline, ~$0 hosting,
desktop browser only. The backend does the API, CSV parsing, money arithmetic, and schema
migrations. The maintainer's prior programming exposure is mostly Python (test-writing more than
application development) and the stated goal of the project is to learn application development
by building it slowly. The runtime is decided first because it constrains the web framework, the
data-access layer, and the packaging tool.

## Decision

**Python**, floor `requires-python = ">=3.13"`, run on 3.13 or 3.14.

## Alternatives considered

- **Node / TypeScript** — lost on *learning runway*: the maintainer has far more traction in
  Python. Its genuine win — one language and shared types across backend and frontend — did not
  outweigh that, and JavaScript's floating-point default is a hazard for money code.
- **Go** — lost on *learning runway* and *money + migration ecosystem fit* (no decimal type in
  the standard library, more boilerplate for plain CRUD). Its genuine win — a tiny static-binary
  container and the simplest deploy — was weighted below learning value at 1–2 users.

## Consequences

- Money arithmetic uses `decimal.Decimal`; a stray `float` in the money path is a bug to catch
  in review and tests (carried forward from archived ADR-0001, which reached the same call).
- The deployment image is the heaviest of the three candidates. Accepted — revisit only if
  hosting cost or cold-start ever becomes a real constraint (it is currently "not constrained").
- The codebase is two languages (Python backend + whatever the frontend decision picks).
  Accepted as a normal daily context-switch.
- Schema migrations have a mature tool available (Alembic) — confirmed or overridden in the
  data-access-layer decision, not here.
