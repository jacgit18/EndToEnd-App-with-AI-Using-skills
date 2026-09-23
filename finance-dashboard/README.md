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

Two ways to run this, same app either way:

- **Option 1** — Postgres in Docker, backend and frontend on the host. Faster edit-reload
  loop (native `--reload`/HMR), what you want day to day.
- **Option 2** — the whole stack in Docker via Compose. Closer to how it'll actually deploy
  (ADR-0012), and how `docs/spec.md`'s Phase 0 walking skeleton is defined — use this to
  sanity-check that a change works outside your one dev machine's native setup.

## Option 1: Native (Postgres in Docker, backend/frontend on the host)

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

## Option 2: Full stack in Docker (Compose)

Four services (`db`, `backend`, `frontend`, `caddy`) defined in `compose.yaml`. If Option 1's
containers/processes are already running, stop them first. All three host ports differ
between the options, so other local containers don't collide with either one: Option 1 is
`db`→`5432`, `backend`→`8000`, `frontend`→`5173`; Option 2 (this one) is `db`→`5433`,
`backend`→`8001`, `frontend`→`5174`.

```bash
docker stop finance-dashboard-db   # if you'd been running Option 1's standalone container
```

From `finance-dashboard/` (this directory):

```bash
docker compose up -d --build
```

First time (and after any new migration), run it against this stack's database — **not** the
same container Option 1 uses, even though the port number looks familiar:

```bash
docker compose exec backend uv run alembic upgrade head
```

No `PYTHONPATH=.` needed here, unlike Option 1's native command — the backend image sets
`PYTHONPATH=/app` itself (see `backend/Dockerfile`), since Alembic doesn't get uvicorn's
trick of adding the working directory to `sys.path` automatically.

Three equivalent ways to reach the running app, all backed by the same containers:

| URL | What answers |
|---|---|
| `http://localhost:8001/health` | the backend container directly |
| `http://localhost:5174` | the frontend container's own Vite dev server + proxy |
| `http://localhost` | Caddy (`Caddyfile`) — the single-origin path production will actually use, reverse-proxying `/api/*` and `/health` to `backend:8000` and everything else to `frontend:5173` (these are the containers' internal ports, unaffected by the host-side remaps above) |

Inside this network, containers reach each other by **service name**, not `localhost` —
`compose.yaml` sets `DATABASE_URL` to `db:5432` and the frontend's `BACKEND_URL` to
`http://backend:8000` for exactly this reason (`localhost` inside a container means that
container itself). Customize the Postgres credentials via `finance-dashboard/.env` (copy from
`.env.example`) if you want; the compose file's defaults match Option 1's either way.

Logs and teardown:

```bash
docker compose logs -f [service]   # tail one service, or omit for all
docker compose down                # stop and remove containers (add -v to also drop the db volume)
```

## Connecting with Beekeeper Studio (or any Postgres client)

| Field | Value |
|---|---|
| Connection type | PostgreSQL |
| Host | `localhost` |
| Port | `5432` (Option 1's standalone container) or `5433` (Option 2's Compose stack) |
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
