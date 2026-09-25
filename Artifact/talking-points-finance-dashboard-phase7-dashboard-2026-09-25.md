# Talking points — finance dashboard, Phase 7 (dashboard)

_Status: documented, **not posted** (owner's call). Drafts only; run any LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| Dashboard API: month totals, per-category actual vs budget, recent 10 | 2026-09-25 | Raw SQL; money stays a 2-decimal string end to end; a category shows if it has a budget or nonzero spend | One call answers "where do I stand this month" | Number: 25 tests, 9 mutations caught; a test caught `COALESCE(x, 0)` returning integer `0` for budget-only rows | PR #90; `routers/dashboard.py` |
| 6-month net trend API | 2026-09-25 | Window of 6 months ending at the chosen month, empty months `0.00`, clamps at 1000-01 | Cash-flow direction at a glance | Number: 12 tests; 8 mutations, 7 caught, 1 equivalent (an SQL bound that is only a scan-size optimization) | PR #91 |
| Dashboard page | 2026-09-25 | Month picker, tiles, recent list; `Number()` only for drawing and colour, never for displayed figures | Figures on screen are the exact strings the API sent | Number: 7 component tests, 9 mutations caught | PR #92; `DashboardPage.tsx` |
| Category and trend charts | 2026-09-25 | Visx bars with a budget tick; red only for over-budget or negative and always paired with a text table | Charts without a component library (ADR-0017, ADR-0018) | Number: 12 tests, 11 mutations, 1 survived and was fixed; bundle 93.6 kB gzip | PR #93; `DashboardCharts.tsx` |

**Not verified (say these before someone asks):** everything ran only under pytest and Vitest; nothing has run against real data or in a real browser yet; Phase 7 is not on prod; the "net equals the transactions list" check is tested on fixtures, not on the real ledger.

## Plain-language summary

Pick a month and see income, spending and net, spending by category against budget, the last six months of cash flow, and the latest transactions. Every number on a chart also appears as text, and the totals are tested to match the transactions list.

## Conversation script

**Opener.** The dashboard's main rule was that every figure has to equal the transactions list. I wrote that as a test first, and it caught a type bug before any UI existed.

**Follow-up line.** Happy to walk through why I drew the charts with Visx instead of a component library.
