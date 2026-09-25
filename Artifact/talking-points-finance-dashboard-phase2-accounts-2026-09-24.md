# Talking points — finance dashboard, Phase 2 (accounts and balances)

_Built from the repo, the session history and the handoff files. Drafts only: nothing here has been posted. Every claim traces to the Evidence Block. Run the LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| A race condition in the account balance, found and closed | 2026-09-24 | `accounts.balance` is a maintained column (opening balance plus the sum of transactions). Two writers read the balance, added their change and wrote it back, so one update was lost. Fixed by locking the account row (`SELECT ... FOR UPDATE`) in every code path that writes the balance | The number the app shows for an account stays equal to what its transactions add up to, even when two requests arrive together | Number, measured before the fix: 58 of 60 two-edit races and 26 of 60 edit-versus-new-transaction races left the balance wrong. After the fix: 0 of 60 in both. Now a permanent test: removing the lock fails it 3 runs out of 3 | PR #69 (commit e25e62b); `backend/tests/test_accounts.py`; handoff file for increments 1-5. The 58/60 and 26/60 figures come from throwaway scripts in the session scratchpad that no longer exist; only the test remains |
| A balance drift check (cron line documented, not yet scheduled) | 2026-09-24 | `app/reconcile.py` compares each account's stored balance to opening balance plus ledger sum in one SQL statement (one snapshot, so a transaction posting mid-run cannot cause a false alarm). Read-only: it reports, it never repairs. Exit 0 all match, 1 drift, 2 could not run or no accounts | If the balance and the ledger ever disagree, I find out the next time it runs, with the account named, instead of when a number looks wrong | Number: 7 tests; 3 deliberate breakages of the job (never flag drift, drop the join, drop the empty-database guard) each failed the tests. Ran once against the live prod database: exit 2, "no accounts", as designed. Not yet run against real data, and not yet on a schedule | PR #70 (commit a4099e1); `tests/test_reconcile.py`; `docs/deploy.md` |
| Money limits enforced at the door | 2026-09-24 | The money type allowed a 13 or 14 digit whole number sent as a JSON number, because the check ran before rounding and counted all digits; Postgres NUMERIC(14,2) then rejected it, so the API answered 500. Now checked after rounding for every input form (string, int, Decimal) and returns 422 | A typo'd amount gets a readable rejection, not a server error | Number: 13 rejected-input cases plus the boundary value `999999999999.99` accepted in 4 forms. Bug was pinned by an expected-failure test until fixed | PR #70; `backend/app/schemas/_money.py`, `tests/test_money.py` |
| Account types, editable opening balance, archive, and the accounts page | 2026-09-24 | Type as a CHECK-constrained column, not an enum; migration 0002 leaves existing rows at 0.00 opening balance on purpose so old drift stays visible; archived accounts refuse new transactions (409); React page with list, create, edit, archive, "show archived" and an inline money check that mirrors the server rule | Accounts can be set up and retired from the UI without touching the database | Number: 104 backend and 38 frontend tests passing (re-run 2026-09-24); four deliberate breakages of the page each failed exactly one test | PRs #69, #70, #71; `frontend/src/AccountsPage.tsx` |
| Prod updated | 2026-09-24 | Started only the prod database, took a `pg_dump` backup, confirmed 0 accounts and migration 0001, then rebuilt the stack; migration 0002 applied | The deployed app is on the same code as `main`, with a backup taken first | Design property: backup-then-migrate order, followed once. `/health` returned ok on localhost through the prod stack. Not verified through the public tunnel URL | This session's commands; `docs/deploy.md` |
| Skill change from this phase | 2026-09-24 | `model-routing-decision` now says in-session: the strongest model writes load-bearing code, a cheap model does mechanical low-risk steps, and I read every diff and re-run the checks myself | Money and locking code gets the careful writer; I still verify | Number: 5 test scenarios, 3 wording fixes applied, fixes not re-run. Design property, not yet measured in real use | PR #70; `.claude/skills/model-routing-decision/SKILL.md` |
| **The set as a whole** | 2026-09-24 | 15 increments across 3 PRs (#69, #70, #71): backend, then frontend, then docs | Accounts and balances I can trust, with a check that tells me when I shouldn't | Number: 104 + 38 automated tests; 0 of 60 races failing after the fix | git log; PRs #69-#71 |

**Not verified (say these before someone asks):** the public tunnel URL has not been loaded from outside; the reconcile job has only seen an empty prod database and test data and is not scheduled; the race numbers are from scripts that no longer exist, so treat them as my measurement, not a reproducible benchmark; the accounts page was checked by hand by you, not by an automated browser test; the model-routing edit's fixes were not re-run; there is no CI.

## Plain-language summary

I'm building a personal finance app slowly enough to explain every part. This phase was accounts and balances. The number the app shows for an account is stored, not recalculated each time, so it can drift from the transactions behind it. I found a way two simultaneous edits could make it wrong, fixed it, and added a check I can run on a schedule that says so if the two ever disagree.

## Conversation script

**Opener.** I'm building a finance app where every balance has to add up. This month I found a bug where two edits at once could make a balance wrong, and fixed it.

**Their question, your read.** "Do you work on the backend side or more the product side?" Then:

**If they go technical.** The balance is a maintained column, so two writers doing read, add, write lose an update. I measured it: 58 of 60 paired edits broke the invariant before I locked the row with `FOR UPDATE`, 0 of 60 after. The lock is now under a concurrency test that fails if I remove it. A read-only reconcile job checks the invariant in a single statement so a mid-run insert can't false-alarm.

**If they stay non-technical.** An account's total was saved as a number instead of added up fresh, and two changes arriving together could make it wrong. I made the app handle one at a time, and I built a check that tells me if any account's total stops matching its history.

**Follow-up line.** Wrote up the balance bug from this month: how I measured it, the fix, and the check I added. Happy to share the details.

## LinkedIn draft

An account balance in my finance app could end up wrong if two edits arrived at the same moment.

I measured it before fixing it. Two simultaneous edits broke the balance 58 times out of 60. An edit racing a new transaction broke it 26 times out of 60. The cause was two requests reading the same balance and each writing back its own answer.

The fix was to lock the account while its balance is being changed. After it, 0 of 60 in both cases. That lock now sits under a test that fails if I remove it, and a job compares every balance to its transaction history and names any account that disagrees.

This shipped in September 2026. The job has only run on test data and an empty production database so far, and it is not on a schedule yet, and the 60-run numbers come from scripts I didn't keep.

What do you check before you trust a stored total?

