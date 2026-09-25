# Talking points — finance dashboard, Phase 3 (categories)

_Status: documented, **not posted** (owner's call, 2026-09-24). Drafts only; every claim traces to the Evidence Block. Run any LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| Category management: list, create, rename, archive | 2026-09-24 | Migration 0003 adds `categories.is_archived` and a database CHECK on `kind` (income/expense). API has no DELETE: an unwanted category is archived, and past transactions keep pointing at it. `kind` cannot be edited, because flipping it would silently re-bucket every past transaction | Categories can be managed from the UI without ever rewriting history | Number: 147 backend and 45 frontend tests passing (re-run 2026-09-24). Eight deliberate breakages of the backend each failed at least one test; one frontend breakage failed exactly one test | PR #74; `backend/app/routers/categories.py`, `tests/test_categories.py`, `frontend/src/CategoriesPage.tsx` |
| A 500 turned into a 404, found while building | 2026-09-24 | Posting a transaction with a nonexistent `category_id` hit the foreign key at commit and returned a server error. The router now looks the category up first: 404 if missing, 409 if archived. The lookup reads the row `FOR SHARE` so an archive cannot commit between the check and the insert | A typo'd id gets a readable rejection, not a server error, and an archived category can't sneak in a new transaction | Number: 2 tests (404, 409) each fail when their check is removed. The 500 was reproduced by the subagent's probe before the fix | PR #74; `backend/app/routers/transactions.py` |
| Workflow: strongest model writes the migration and API, I verify | 2026-09-24 | Opus subagent wrote migration 0003, router, schemas and tests from a self-contained brief; I read the diff and re-ran the suite myself | The load-bearing part got the careful writer and an independent check | Design property, one use so far. My re-run matched the subagent's report (147 passed) | Session; PR #74 |

**Not verified (say these before someone asks):** prod has not been migrated to 0003 yet; there is no category picker on the transaction form, so "hidden from pickers" is enforced only by the API default and the 409; the concurrency guard (`FOR SHARE`) has no dedicated race test, unlike the Phase 2 balance lock; no CI.

## Plain-language summary

Phase 3 lets me manage the labels on transactions (Groceries, Rent, Salary). The design choice worth talking about: there is no delete. A category I stop using gets archived, so the old transactions keep their label and the history never changes.

## Conversation script

**Opener.** I'm building a finance app slowly on purpose. This week I added categories, and the interesting part was what I left out: you can't delete one.

**If they go technical.** Transactions reference categories by foreign key, so deletion means either orphaned history or cascading loss. Archive-only keeps the ledger append-only in spirit. `kind` is immutable through the API for the same reason. While building it I found a nonexistent category id returned a 500 instead of a 404, and fixed it with a row lock so an archive can't slip in between the check and the insert.

**If they stay non-technical.** When you stop using a label, the app hides it instead of erasing it, so your old records still make sense.

**Follow-up line.** Wrote up what I chose not to build and why. Happy to share.

## LinkedIn draft (rough, not run through brand/de-AI passes; not posted)

I added categories to my finance app this week. The design decision I care about is what it can't do: it can't delete one.

Every transaction points at a category. Delete the category and you either lose the label on old records or break them. So an unwanted category gets archived: hidden from the pickers, still attached to its history. The type (income or expense) is locked after creation for the same reason, since changing it would quietly move past transactions into a different bucket.

Building it also turned up a bug in code I had already shipped: posting a transaction with a category id that didn't exist returned a server error instead of "not found." It's fixed, and two tests fail if I take the fix out.

147 backend tests and 45 frontend tests pass. Not done yet: the app isn't updated in production, and the transaction form has no category dropdown, so the hiding is enforced by the API for now.
