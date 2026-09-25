# Talking points — finance dashboard, Phase 6 (monthly budgets)

_Status: documented, **not posted** (owner's call). Drafts only; run any LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| Set a monthly budget per category | 2026-09-25 | An upsert keyed on (category, month); setting again edits, clearing deletes the row, so "no row" means "no budget" | One rule for "no budget" instead of a zero that means two things | Number: 38 backend tests, 6 mutations caught | PR #84; `routers/budgets.py` |
| Copy last month forward | 2026-09-25 | One SQL statement copies rows and never overwrites; archived categories are skipped and counted | Start a month in one click without clobbering edits | A test caught a real bug: the driver's row count is -1 for this statement shape, so the copied count now comes from RETURNING | PR #84 |
| Budgets page | 2026-09-25 | Month picker, per-category set/clear, copy-forward button | Editing budgets without touching the API | Number: 9 frontend tests, 8 mutations tried, 1 survived and was fixed in the test | PR #86; `BudgetsPage.tsx` |

**Not verified (say these before someone asks):** the page has only run under Vitest, not in a real browser; the API has only run under pytest against the dev database; prod does not have Phase 6 yet; the UI shows expense categories only while the API accepts any non-archived category.

## Plain-language summary

You can set how much you plan to spend per category each month, and copy last month's plan forward. Nothing gets overwritten by the copy.

## Conversation script

**Opener.** The budgets feature was small, but a test caught a bug I would have shipped: the database driver reports -1 rows for one statement shape, so my "copied N" count was wrong.

**Follow-up line.** Happy to walk through how I decided that "no row" means "no budget".
