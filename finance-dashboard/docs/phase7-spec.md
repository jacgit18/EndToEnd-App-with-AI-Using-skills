# Phase 7 spec — S7 dashboard

Written 2026-09-25 via `spec-drift-gate`. Decisions: ADR-0017 (Visx), ADR-0018 (no component library). Story text and acceptance criteria: `backlog.md` S7.

## Problem
See where you stand for one month at a glance, and trust it: every figure reconciles with the transactions list.

## Definitions (settled with the owner)
- **Month** = `YYYY-MM`, same validation as budgets (bad month is 422). Range is `[first, first of next)`.
- **Income / expense by category kind.** Income = sum of amounts in `income`-kind categories. Expense = minus the sum of amounts in `expense`-kind categories. So a refund on an expense category reduces expense; a void nets its original to zero.
- **Uncategorized rows** (`category_id` null): summed together; a negative sum counts as expense, a positive sum as income. Shown as an "Uncategorized" line in the category chart only when it counts as expense (net negative); a positive net is income and has no chart line. (Refined in slice 1 from "when nonzero", since the chart shows spend.)
- **Net** = income - expense = the plain sum of every amount in the month. This is the reconciliation invariant.
- **Category chart** rows: every expense-kind category that has a budget row or a nonzero net spend that month. Budget-only rows show 0 actual; spend-only rows show budget `null` ("no budget"). Archived categories with spend are included.
- Reversals are ordinary ledger rows: included in totals and in the recent list.

## In scope
- `GET /api/dashboard?month=`: `{month, income, expense, net, categories[], recent[]}`; recent = last 10 transactions in the month (date desc, id desc).
- `GET /api/dashboard/trend?month=`: net per month for the 6 months ending at `month` (oldest first, months with no rows are `0.00`).
- Raw SQL, money as strings, no migration.
- Dashboard page: month picker (default current month), tiles, category bar chart (Visx), trend chart (Visx), recent list. Every charted value is also visible as text.
- Tests: backend reconciliation (dashboard net == sum of `/api/transactions?month=`), frontend component tests with mutation checks.

## Out of scope
Chart-to-transactions drill-down, custom date ranges, export, transfers as a type, budgets on income categories, migrations.

## Slices
1. `/api/dashboard` (tiles, categories, recent) + reconciliation tests. Cheap first slice: if the definitions are wrong it shows here.
2. `/api/dashboard/trend`.
3. Dashboard page: month picker, tiles, recent list.
4. Category bar chart, then trend chart (Visx; check React 18.3 peer deps first).
5. Docs, browser check, deploy on a fresh "deploy to prod".

## Tripwires (stop and ask)
- A dashboard figure that can't be made to equal the transactions list.
- A category with spend that no rule above places.
- Anything needing a migration.

## Progress
- Slice 1 done: `GET /api/dashboard` (`app/routers/dashboard.py`), 25 tests in `tests/test_dashboard.py`, 9 mutations tried and all caught. Found by tests: `COALESCE(x, 0)` returned an integer `0` for budget-only rows, so amounts are quantized to 2 decimals in the router. Not yet run against real data or in a browser.
- Slice 2 done: `GET /api/dashboard/trend?month=` (same router), 12 more tests (37 in `tests/test_dashboard.py`, 485 backend total). Includes the year-boundary window, empty months, and trend net == `/api/dashboard` net per month. 8 mutations tried: 7 caught, 1 equivalent (dropping the SQL upper date bound; out-of-window rows are discarded when matched to the month list, so the bound is only a scan-size optimization). Found by tests: `MONTH_PATTERN` starts at year 1000, so the window clamps at 1000-01. Not yet run against real data or in a browser.
- Slice 3 done: `/dashboard` page (`frontend/src/DashboardPage.tsx`): month picker (local current month, no request while cleared), income/expense/net tiles as the API's strings, recent list, loading/error/empty states; nav link "Dashboard" on the home page; client types + `api.dashboard` / `api.dashboardTrend` (trend not consumed yet). 7 tests (77 frontend total), 9 mutations tried, all caught. `/` stays the Transactions page. Category table + charts come in slice 4. Not yet checked in a real browser.
- Slice 4 done: Visx 4.0.0 (`@visx/axis`, `group`, `scale`, `shape`; peers accept React 18 and 19, so Recharts fallback not needed; `@visx/responsive` skipped, charts are fixed-viewBox SVG that scale with width). `DashboardCharts.tsx`: category bars with a budget tick (red when over budget, "no budget" text when none) and a 6-month net bar chart (green/red by sign, zero line); each chart has a table of the API's own strings under it. Trend query is separate, so a trend failure leaves the rest of the page up. 89 frontend tests (12 new here); 11 mutations tried, 1 survived (trend query key ignoring the month), test added, now caught. Bundle 93.6 kB gzip. Colour is only used for over-budget/negative and always paired with the text table. Not yet checked in a real browser.
- Slice 5b done (2026-09-25): owner checked `/dashboard` in a real browser on the dev stack with real data: tiles, both charts and recent list render; net tile matches the Transactions list; month change refetches; narrow width fits. No detailed per-figure record kept. Found: the dev frontend container's `node_modules` volume predated Visx, so Vite failed to resolve `@visx/axis`; fixed with `docker compose exec frontend npm install` (container only, no repo change; prod builds install from `package.json`). Not on prod yet.
