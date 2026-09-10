# ADR 0003 — Web framework

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 2 of the stack

## Context

Python was chosen in ADR-0002. This decision picks the Python web framework that serves the
HTTP API — routing, request parsing, response shaping. It determines how much is assembled by
hand (data-access layer, migrations, auth, admin UI) versus provided, so it feeds decisions 5
(data-access) and 8 (auth). The app's shape from the scope doc: a JSON API consumed by a
separate single-page frontend, single user, small CRUD + CSV import + dashboard aggregations.

## Decision

**FastAPI**, floor tracked with the project's dependency lockfile.

## Alternatives considered

- **Django + DRF** — lost on *concept load* and *fit to shape*: it is the largest framework to
  learn up front, its serializer layer is a second sub-system, and its main draws (built-in
  admin CRUD UI, built-in auth, server-rendered pages) are weakened by the scope's separate-SPA
  architecture. Its genuine win — batteries included, less to assemble — was outweighed.
- **Flask** — lost on *validation at the money / CSV boundary*: no typed request parsing in the
  box. Its genuine win — the most direct "wire every piece yourself" learning — did not outweigh
  losing free, enforced input validation in a finance app.

## Consequences

- Request/response bodies are typed Pydantic models — enforced validation at the money and CSV
  input boundary, for free. This is the main reason for the choice.
- No admin UI and no auth come with the framework. Auth is real work (decision 8). Any
  "eyeball the records" need is met by the database tooling or hand-built CRUD screens.
- `async`/`await` is in the programming model from the start, before a 1–2 user app strictly
  requires it — accepted as worth learning early.
- The data-access layer and migration tool are a separate choice (decision 5), not bundled.
- Note: this pick is also the framework a learning-neutral analysis reaches for "Python behind
  an SPA" — the learning consideration did not materially move this decision (it moved
  ADR-0002's language pick).
