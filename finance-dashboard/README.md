# Finance Dashboard

Self-hosted personal budgeting dashboard. Python/FastAPI + React/Vite + PostgreSQL,
containerized with Docker Compose.

- **Scope:** [docs/architecture/scope/finance-dashboard.md](docs/architecture/scope/finance-dashboard.md)
- **Build spec + drift log:** [docs/spec.md](docs/spec.md)
- **Backlog (user stories):** [docs/backlog.md](docs/backlog.md)
- **Test plan:** [docs/testing/finance-dashboard.md](docs/testing/finance-dashboard.md)
- **Decisions:** [docs/architecture/decisions/](docs/architecture/decisions/)

## Status: walking skeleton

The controlled-experiment slice from the spec. It proves the full stack is wired:
Compose → Postgres → Alembic migration (all five tables + seeded categories) →
FastAPI (`/api/accounts`, `/api/transactions`, `/health`) → Vite/React SPA that shows an
API health badge, a transactions table, and an add-transaction form.

Not yet built: auth (S1), account edit/archive + derived balances (S2), category management
(S3), transaction edit/delete + filtering (S4), CSV import (S5), budgets (S6), the dashboard
with charts (S7).

## Run it

```bash
cp .env.example .env        # optional; defaults work for local dev
docker compose up --build
```

- SPA:      http://localhost:5173
- API docs: http://localhost:8000/docs
- Postgres: localhost:5432  (finance / finance)

Create an account so the transaction form has something to point at:

```bash
curl -X POST localhost:8000/api/accounts \
  -H 'content-type: application/json' \
  -d '{"name":"Checking","type":"checking","starting_balance":"1000.00"}'
```

## Layout

```
backend/          FastAPI app, SQLAlchemy 2.0 models, Alembic migrations, pytest
  app/
    config.py     env-driven settings (pydantic-settings)
    db.py         engine + session + declarative Base
    models/       Account, Category, Transaction, Budget, ImportBatch
    schemas/      Pydantic request/response models
    routers/      accounts, transactions
    main.py       app assembly + CORS + /health
  migrations/     Alembic (0001 = full schema + seeded categories)
  tests/          unit tests (dedupe hash)
frontend/         Vite + React + TypeScript + Tailwind
  src/
    api/client.ts axios wrapper + typed API calls
    pages/        Transactions
    App.tsx       shell + health badge
compose.yaml      db + backend + frontend
```

## Local dev without Docker

Backend needs `uv` (`pip install uv`), a running Postgres, and `DATABASE_URL` pointing at
it; then `uv run alembic upgrade head && uv run uvicorn app.main:app --reload`.
Frontend: `cd frontend && npm install && npm run dev` (proxy target in `vite.config.ts`
assumes the compose network — change it to `localhost:8000` for host-only dev).

## Conventions

Money is `Numeric(14,2)` in Postgres and `Decimal` in Python, serialized to JSON as a
string. Never `float`. Account balances are derived, not stored. See ADR 0001.
