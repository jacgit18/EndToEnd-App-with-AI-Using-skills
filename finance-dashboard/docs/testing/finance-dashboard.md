# Test plan — Personal Finance Dashboard

> Produced by `Testing/test-strategy`. Contested calls are in
> `../architecture/decisions/0001-stack-and-money-representation.md`.

## Surface and seams

One small FastAPI service + its Postgres schema + a React SPA. Seams:
- SQLAlchemy ↔ Postgres
- the CSV parser
- the JWT auth dependency
- the REST boundary the SPA consumes (single consumer, same repo)

## Highest failure cost

**Silent wrong numbers** — a dedupe miss that double-imports, a sign error on amounts, an
aggregation that doesn't reconcile with the ledger. Everything else is cosmetic / low cost.

## Test mix

| Level | Share | Notes |
|---|---|---|
| Unit | ~55% | Money math (balance derivation, sign convention), dedupe-hash construction, CSV row → transaction mapping, budget-vs-actual aggregation. Pure functions, no DB. |
| Integration | ~40% | FastAPI `TestClient` + a real Postgres, transactional rollback per test. Each router's CRUD; auth-required → `401` without a token; CSV import end-to-end incl. the skip-duplicates count; dashboard aggregation endpoints reconciling with inserted rows. |
| Contract | none | Single consumer in the same repo — revisit if a second client appears. |
| E2E | ~5% | One Playwright path: log in → add a transaction → see it on the dashboard. |
| Smoke | yes | `/health` + the E2E path, run before a release. |

## Pipeline placement

- **PR CI:** unit + integration, budget < 3 min. `alembic upgrade head` against a scratch DB.
- **Local / pre-release:** E2E smoke (no CI browser infra for the MVP).

## Technique & data

- Grey-box — know the schema and the seams, test through the API.
- Fixtures / factory helpers, plus a couple of committed sample bank CSVs for the import tests.

## Non-functional

**None — accepted.** Single user, self-hosted; no load, performance, or security-scan tests
in v1 beyond "auth is required on protected routes".

## Workflow

Test-after with disciplined naming. **BDD rejected** — no non-developer will read `.feature` files.

## Deferred

Coverage % and its CI enforcement → `Testing/coverage-policy` later · Playwright vs Cypress ·
contract tests if a second client ever appears · CI-cost sizing.
