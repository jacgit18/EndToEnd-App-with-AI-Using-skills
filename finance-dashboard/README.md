# Finance Dashboard

Personal finance dashboard — FastAPI backend, Postgres, React/Vite frontend.
Currently Phase 0 (walking skeleton): backend health check + empty
accounts/transactions endpoints, DB schema in place, frontend scaffolded.
See `docs/spec.md` and `docs/architecture/decisions/` for the full design.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (runs Postgres locally)
- [uv](https://docs.astral.sh/uv/) (Python dependency/venv manager — `pip install --user uv`
  if you don't have it; it fetches the right Python version itself, no separate install needed)
- Node.js + npm (for the frontend)

## Running locally

### 1. Postgres (Docker)

First time:

```bash
docker run -d --name finance-dashboard-db \
  -e POSTGRES_USER=finance -e POSTGRES_PASSWORD=finance -e POSTGRES_DB=finance \
  -p 5432:5432 postgres:16-alpine
```

Subsequent times (after a reboot or `docker stop`):

```bash
docker start finance-dashboard-db
```

Check it's actually accepting connections:

```bash
docker exec finance-dashboard-db pg_isready -U finance
```

### 2. Backend (FastAPI)

`finance-dashboard/backend/.env` (create once, gitignored):

```
DATABASE_URL=postgresql+psycopg://finance:finance@localhost:5432/finance
ENV=dev
```

From `finance-dashboard/backend/`:

```bash
uv sync                               # first time / after dependency changes
PYTHONPATH=. uv run alembic upgrade head   # first time / after new migrations
uv run uvicorn app.main:app --reload
```

Backend serves on `http://localhost:8000`. Smoke test: `curl http://localhost:8000/health`
should return `{"status":"ok","db":"connected"}`.

### 3. Frontend (Vite/React)

From `finance-dashboard/frontend/`:

```bash
npm install    # first time / after dependency changes
npm run dev
```

Opens on `http://localhost:5173` (Vite's default). The dev server proxies `/api/*` and
`/health` to `localhost:8000`, so the backend must already be running (see `vite.config.ts`).

## Connecting with Beekeeper Studio (or any Postgres client)

| Field | Value |
|---|---|
| Connection type | PostgreSQL |
| Host | `localhost` |
| Port | `5432` |
| User | `finance` |
| Password | `finance` |
| Database | `finance` |
| SSL | off |

These are local dev-only credentials from the `docker run` command above — not used
anywhere else, fine to keep as-is for local work.

### Sample queries

Schema as of migration `0001_initial` (see `backend/app/models/`):

```sql
-- List all tables
\dt

-- Accounts and their cached balances
SELECT id, name, balance, is_archived, created_at
FROM accounts
ORDER BY name;

-- Categories seeded by the initial migration
SELECT id, name, kind
FROM categories
ORDER BY kind, name;

-- Most recent transactions, with account + category names
SELECT t.id, t.date, a.name AS account, c.name AS category, t.amount, t.description, t.type
FROM transactions t
JOIN accounts a ON a.id = t.account_id
LEFT JOIN categories c ON c.id = t.category_id
ORDER BY t.date DESC, t.id DESC
LIMIT 50;

-- Spending by category for a given month (expenses are negative amounts)
SELECT c.name AS category, SUM(-t.amount) AS spent
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE c.kind = 'expense'
  AND date_trunc('month', t.date) = date_trunc('month', DATE '2026-09-01')
GROUP BY c.name
ORDER BY spent DESC;

-- Sanity check: does the ledger sum match each account's cached balance?
SELECT a.id, a.name, a.balance AS cached_balance, COALESCE(SUM(t.amount), 0) AS ledger_sum
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
GROUP BY a.id, a.name, a.balance
HAVING a.balance != COALESCE(SUM(t.amount), 0);

-- Budgets set for a given month
SELECT c.name AS category, b.month, b.amount
FROM budgets b
JOIN categories c ON c.id = b.category_id
ORDER BY b.month DESC, c.name;
```

The database starts empty (no accounts/transactions seeded) — the balance-reconciliation
query and the spending-by-category query will return no rows until you've created data via
the API or a CSV import.
