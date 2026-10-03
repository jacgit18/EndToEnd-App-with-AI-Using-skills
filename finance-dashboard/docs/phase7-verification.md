# Phase 7 verification record (S7 dashboard)

Closes the gap noted in `phase7-spec.md` slices 5b/5c ("no detailed per-figure record kept").

## What can be verified from the repo

| Figure | Invariant | Evidence |
|---|---|---|
| Net tile | net = income - expense = plain sum of the month's amounts | Backend reconciliation tests in `backend/tests/test_dashboard.py` (dashboard net equals the sum of `/api/transactions?month=`); trend net per month equals `/api/dashboard` net |
| Expense tile | minus the sum of expense-kind amounts; refunds reduce it, voids net to zero | same test file, 9 mutations tried and caught in slice 1 |
| Category rows | budget-only rows show 0 actual, spend-only rows show budget `null` | same file |
| Trend | 6 months oldest-first, empty months `0.00`, year boundary | same file, 8 mutations (7 caught, 1 equivalent) |
| Page renders the API's strings unchanged | no client-side arithmetic | `DashboardPage.test.tsx`, `DashboardCharts.test.tsx`, 11 mutations tried, 1 survived and was fixed |

## What was checked by the owner on real data

Slice 5b (dev stack) and 5c (prod), 2026-09-25: tiles, both charts and the recent list render; the net tile matched the Transactions list; the month picker refetches; narrow width fits. **No per-figure numbers were written down at the time and cannot be reconstructed.** They are not claimed here.

## Still to do (optional, owner, needs the real login)

Low priority while the data is static (2026-10-03: one manually uploaded file, no automated import). Until this table is filled in, the dashboard figures are backed by tests only.

Pick one month with real data and fill this in. It takes about five minutes and closes the item.

| Month | Dashboard net | Sum of Transactions list for the month | Match? | Income tile | Expense tile | Each category actual vs list | Date checked |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Mark any mismatch as a tripwire per `phase7-spec.md` (stop and ask).
