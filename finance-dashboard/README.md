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

## Run without Docker

The app runs natively; only the database needs Postgres. Two ways to get one:

**A — Postgres in a single container** (works even if `docker compose build` can't reach
the internet, as long as the `postgres:16` image is already pulled):

```bash
docker run -d --name fd-db \
  -e POSTGRES_USER=finance -e POSTGRES_PASSWORD=finance -e POSTGRES_DB=finance \
  -p 5432:5432 postgres:16
```

**B — no Postgres at all:** use the SQLite fallback by setting
`DATABASE_URL=sqlite+pysqlite:///./finance.db` in the backend step below. Fine for a quick
look; the real target is Postgres (ADR 0001).

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://finance:finance@localhost:5432/finance"   # or the SQLite URL
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

API at http://localhost:8000 , docs at `/docs`. Run the tests with `.venv/bin/pytest -q`.

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api and /health to localhost:8000
```

`vite.config.ts` proxies to `http://localhost:8000` by default; compose overrides that with
`VITE_API_PROXY=http://backend:8000`.

### Create an account so the form works

```bash
curl -X POST localhost:8000/api/accounts -H 'content-type: application/json' \
  -d '{"name":"Checking","type":"checking","starting_balance":"1000.00"}'
```

## Conventions

Money is `Numeric(14,2)` in Postgres and `Decimal` in Python, serialized to JSON as a
string. Never `float`. Account balances are derived, not stored. See ADR 0001.
