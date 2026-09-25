# Talking points — finance dashboard, Phase 5 (CSV import)

_Status: documented, **not posted** (owner's call). Drafts only; every claim traces to the Evidence Block. Run any LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| Import a bank CSV by mapping its columns | 2026-09-25 | Upload, preview the first 10 rows, pick which column is the date, amount and description, then import. The file is parsed by a pure, unit-tested module; the API writes the batch, the rows and the balance change in one database transaction | No retyping statements; a crash mid-import leaves nothing behind | Number: 410 backend tests (359 before the multi-account work, 207 before Phase 5); 60 frontend | PR #80; `backend/app/importer.py`, `routers/imports.py` |
| One file, many accounts | 2026-09-25 | My own bank export holds 16 accounts in one file. The mapping takes an account column plus a value-to-account map (or "leave these rows out"); one import batch per account; the accounts are locked in ascending id order so two overlapping imports can't deadlock | The real export imports in one pass instead of being split by hand | Measured with a mutation: removing the sort made the opposite-order concurrent test fail with a real `DeadlockDetected` in round 0 | PR #80; `tests/test_imports.py` |
| Re-importing the same file adds nothing | 2026-09-25 | Each row gets a hash of date, amount, description and its occurrence number within its account in the file; the database's unique constraint skips repeats. Two identical same-day purchases both import, a second import of the file skips all | Safe to re-run an export that overlaps the last one | Mutation: making the occurrence count per file instead of per account failed 3 tests | PR #80; `importer.py` |
| Refuses to guess money | 2026-09-25 | Amounts with more than 2 decimals or odd commas are rejected, not rounded ("1,50" might be 1.50 or 1,500 in another locale). The date format (`YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`) must be chosen; it is never inferred. Bad rows are listed with line numbers instead of failing the file | A wrong guess would silently misfile a month or scale an amount by 1000 | Tested on synthetic files only | PR #80; `importer.py`, `ImportPage.tsx` |
| Import page that can't skip a decision | 2026-09-25 | The Import button stays off until every account value in the file has an explicit choice, and the date format has no default | No value silently lands in a default account | Number: 60 frontend tests; 3 mutations tried, each caught by a test | PR #80; `frontend/src/ImportPage.tsx` |

**Not verified (say these before someone asks):** my real SoFi export has not been run through the app; every test file is synthetic; an import can duplicate a hand-entered row (those have no hash); there is no way to undo a whole import, only voiding rows one by one; the 2 MB upload limit is enforced after the server buffers the file, and a hard cap in the reverse proxy isn't added; the backend was written by a subagent, and I reviewed it, re-ran the tests and ran one mutation myself; no CI. Prod status: see the deploy line below.

**Deploy status:** Deployed to prod 2026-09-25 (migration 0005): backup first (dump checked to contain the 5 real accounts), `alembic current` = 0005, `/health` ok, reconcile exit 0 ("5 accounts match the ledger"), import route answers 401 without a session. Not done on prod: importing a real file through the browser.

## Plain-language summary

You can now feed the app a bank export. It shows you the first rows, you say which column is what and which account each row belongs to, and it imports them. Running the same file twice adds nothing. Anything it can't read safely it lists back to you instead of guessing.

## Conversation script

**Opener.** I taught my finance app to read my bank's CSV, and the design rule was: never guess about money.

**If they go technical.** Dedupe is a hash plus a unique constraint, not a "does it exist" check, so two imports racing can't double-insert. The subtle part was the occurrence index: two identical coffees on one day are both real, so the hash includes which repeat it is, counted per account. My export had 16 accounts in one file, so I added a per-value account map and locked the accounts in a fixed order to avoid deadlocks, then proved that by removing the ordering and watching a real deadlock.

**If they stay non-technical.** It's the difference between a tool that guesses what your statement means and one that asks. It won't pick a date format or round an odd amount for you.

**Follow-up line.** Happy to share how I checked the concurrency by breaking it on purpose.

## LinkedIn draft (rough, not through brand/de-AI passes; not posted)

I added CSV import to my finance app. The rule I set was: never guess about money.

It won't infer a date format, because 03/04 is March 4th in one bank's file and April 3rd in another's. It won't round "1,50", because that could be one dollar fifty or fifteen hundred. Rows it can't read are listed with line numbers instead of quietly dropped.

Running the same file twice adds nothing. Two identical coffees on the same day both import, because the dedupe key counts which repeat it is.

My real export has 16 accounts in one file, so I added a per-value account map. Two imports touching the same accounts could deadlock, so accounts are locked in a fixed order. I removed that ordering to check: a real deadlock, first round.

410 backend and 60 frontend tests pass. Not done: undoing a whole import (today it's row by row), and I haven't run my actual export through it yet.
