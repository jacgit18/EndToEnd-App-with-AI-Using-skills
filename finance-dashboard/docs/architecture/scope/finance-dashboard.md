# Scope — Personal Finance Dashboard (v1 MVP)

> Living document. Produced by `Architecture/design-scoping`. Update it when scope moves;
> each deep-dive decision gets its own ADR under `../decisions/`.

## Purpose

A self-hosted personal budgeting dashboard — see accounts, categorized spending, and
budget-vs-actual without a spreadsheet or a SaaS subscription.

## Audience

One user (the owner), self-hosted, desktop web browser, single region. No sign-up flow;
credentials come from environment configuration.

## In scope (v1)

- Accounts (checking / savings / credit card / cash) with a starting balance
- Transactions: manual create/edit/delete **+ CSV import** (upload → map columns → dedupe → categorize)
- Categories: flat list, `income` / `expense` tag, ~15 seeded
- Budgets: one monthly amount per category
- Dashboard: month income/expense/net, spending-by-category vs budget, 6-month cash-flow
  trend, recent transactions
- Single-user login (env-configured email + password → JWT)

## Explicitly out (v1)

- Bank / Plaid / brokerage sync
- Investments, holdings, net-worth tracking
- Recurring-transaction detection; rules / auto-categorization engine
- Multi-currency
- Multi-user, households, sharing, roles
- Mobile app / native clients
- Alerts, notifications, email digests
- Forecasting; budget rollover / carry-over logic

## Non-functional targets

| Dimension | Target |
|---|---|
| Throughput | Not constrained — single user, accept the simple design |
| Concurrency | 1–2 sessions |
| Latency | Not constrained — sub-second on all views is trivially met at this data volume |
| Availability | Not constrained — local / self-hosted, a restart is acceptable |
| Error budget | Not constrained |
| Cost cap | ~$0 — runs on the owner's machine or a small VPS |

## Constraints

- **Team:** solo (the owner).
- **Timeline:** none stated.
- **Stack:** open — no technology is fixed. Every choice is being derived decision-by-decision
  through `Architecture/tech-decision-walkthrough`, each recorded as an ADR under
  `../decisions/`. The owner's earlier picks (Python / FastAPI · React / Vite · PostgreSQL ·
  Docker Compose · `uv` · Tailwind) are archived at `../decisions/_archived/0001-…` as prior
  input, not a constraint.
- **Platforms:** desktop browser only.
- **Compliance:** none — the owner's own data, self-hosted, no third-party data handled.

## Deep-dive decisions (to be derived)

These are the choices worth reasoning through deliberately, in `tech-decision-walkthrough`;
each ends in an ADR under `../decisions/`. The list is the *significance-filter output* — the
answers are not decided here.

1. **Data model + money representation** — load-bearing. Whole-data-model blast radius:
   changing the money type or the account-balance approach later needs a migration and a data
   rewrite. Sub-questions: how currency amounts are represented; whether an account balance is
   stored or derived; the transaction dedupe key.
2. **Datastore** — load-bearing (migration cost to change).
3. **Auth approach** — single-user-from-env vs. a user table vs. a hosted IdP.
4. Language / runtime, web framework, data-access layer, frontend approach, API style,
   packaging, deployment target — structural or routine; walked at proportionate depth.

## Acknowledged, deferred (decide during implementation)

CSV column-mapping UX · exact dedupe-hash field set · auth token lifetime / refresh ·
chart library choice · dashboard aggregation query approach.

## Sequence

1. `Business/user-story-decomposition` on the in-scope list → `docs/backlog.md` ✅
2. `Testing/test-strategy` on the mix → `docs/testing/finance-dashboard.md` ✅
3. `Architecture/tech-decision-walkthrough` on the stack → an ADR per decision under
   `../decisions/` (supersedes the archived `_archived/0001-…`).
4. `Skill Development/spec-drift-gate` — fold the ADRs into `docs/spec.md`.
5. Build — `Skill Development/incremental-build-pacing`, walking skeleton first (see
   `docs/spec.md`), then the backlog in MoSCoW order.
