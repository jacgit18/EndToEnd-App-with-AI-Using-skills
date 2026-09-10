# Backlog — Personal Finance Dashboard (v1)

> Produced by `Business/user-story-decomposition` from the in-scope list in
> `docs/architecture/scope/finance-dashboard.md`.

- **Epic:** Personal budgeting dashboard (v1)
- **Actor:** the account owner (single user)
- **Format:** User Story — single actor, no alternate paths worth pre-documenting as use cases
- **Prioritization:** MoSCoW, tagged per story

---

## S1 — Login (Must)

> As the owner, I want to log in with my configured credentials, so that the dashboard
> isn't open to anyone who reaches the URL.

**Acceptance criteria**
- Credentials come from env vars (`AUTH_EMAIL`, `AUTH_PASSWORD`); no signup endpoint.
- Correct credentials → a signed JWT; wrong → `401`.
- All API routes except `/health` and `POST /api/auth/login` require a valid token.
- Token expiry is configurable (`JWT_EXPIRE_MINUTES`).

**Explicitly not covered:** signup, password reset, multiple users, refresh tokens.

---

## S2 — Manage accounts (Must)

> As the owner, I want to create and edit accounts with a type and starting balance, so
> that transactions have somewhere to live.

**Acceptance criteria**
- Create / list / edit / archive.
- `type` ∈ {checking, savings, credit_card, cash}; `starting_balance` is a decimal.
- Archived accounts are hidden from pickers but keep their transactions.
- Displayed balance = `starting_balance + sum(transactions)`.

**Explicitly not covered:** close/reopen semantics beyond archive; inter-account transfers as a first-class type.

*Skeleton delivers list + create; edit/archive + derived balance remain.*

---

## S3 — Category list (Must)

> As the owner, I want a seeded category list I can add to and archive, so that spending
> can be classified.

**Acceptance criteria**
- ~15 categories seeded by the initial migration; each has `kind` ∈ {income, expense}.
- Create / rename / archive.
- Archived categories are hidden from pickers; existing transactions keep the reference.

**Explicitly not covered:** subcategories, per-category colors/icons.

*Skeleton delivers the seed; the management UI remains.*

---

## S4 — Manual transactions (Must)

> As the owner, I want to add, edit and delete transactions by hand, so that I can record
> cash spending and corrections.

**Acceptance criteria**
- Fields: `date`, `amount` (decimal; sign convention documented — negative = money out),
  `description`, `account` (required), `category` (optional).
- List view filterable by month + account.
- Delete asks for confirmation.

**Explicitly not covered:** split transactions, attachments/receipts, bulk edit.

*Skeleton delivers add + list; edit/delete + filtering remain.*

> **Amended 2026-09-10 (ADR-0005):** the ledger is append-only. "Edit and delete" becomes
> **add + void** — a void posts a reversing entry; there is no in-place edit or hard delete.
> AC and this story text to be reworded at build time.

---

## S5 — CSV import (Must) — large, splittable

> As the owner, I want to import a bank CSV by mapping its columns, so that I don't retype
> statements.

**Acceptance criteria**
- Upload CSV → preview first rows → map file columns to {date, amount, description}.
- Choose the target account.
- Import creates an `import_batch`; rows whose dedupe hash already exists are skipped and counted.
- Imported rows land uncategorized.

**Explicitly not covered:** saved per-bank mappings, auto-categorization rules, OFX/QIF, multiple accounts in one file.

**Split if needed:** S5a import with fixed column names → S5b column-mapping UI.

---

## S6 — Monthly budgets (Should)

> As the owner, I want to set a monthly budget amount per category, so that I have
> something to compare spending against.

**Acceptance criteria**
- Set / edit an amount for a `(category, month)` pair.
- Copy-forward from the previous month.
- No row = no budget line for that category that month.

**Explicitly not covered:** rollover of unspent amounts, weekly/annual budgets, per-account budgets.

---

## S7 — Dashboard (Must) — large, splittable per widget

> As the owner, I want a dashboard for a chosen month showing income/expense/net, spending
> by category vs budget, a 6-month cash-flow trend, and recent transactions, so that I can
> see where I stand at a glance.

**Acceptance criteria**
- Month picker (defaults to current month).
- Summary tiles: income, expense, net.
- Per-category bar: actual vs budget.
- Line/bar: net cash flow for the last 6 months.
- Last ~10 transactions.
- Every figure reconciles with the transactions list.

**Explicitly not covered:** chart→transactions drill-down, custom date ranges, dashboard export.

---

## Deferred (Won't-have this time)

S8 recurring-transaction detection · S9 auto-categorization rules · S10 investments / net
worth · S11 multi-currency.

## Definition-of-Ready gaps

- Sizing is rough. S5 and S7 are the large stories — both have a stated split.
- No load-bearing architecture decision surfaced beyond the already-settled data model.
