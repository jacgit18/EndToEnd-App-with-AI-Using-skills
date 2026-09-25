# Talking points — finance dashboard, Phase 4 (transactions: add and void)

_Status: documented, **not posted** (owner's call). Drafts only; every claim traces to the Evidence Block. Run any LinkedIn draft through `software-carpentier-brand` and `delete-ai-words` before posting._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| "Delete" that never deletes: void posts a reversing entry | 2026-09-24 | Transactions are an append-only ledger. Voiding one inserts a second row with the amount negated, the same account and category, and the original's date, so that month nets to zero. The original row is never touched. Voiding a void is refused (you re-post the entry instead) | The history always shows what was recorded and when it was undone, and every balance still equals the sum of its rows | Number: 54 new backend tests; the balance invariant is checked by direct SQL after each void, not just by the HTTP status | PR #77; `backend/app/routers/transactions.py`, `tests/test_transactions.py` |
| A row can be voided once, even if two requests arrive together | 2026-09-24 | Two layers: a pre-check under the account row lock, and a partial unique index on `reverses_transaction_id` (migration 0004) that makes a second reversal fail in the database; the router turns that failure into a 409 | A double-click or retry can't undo the same entry twice | Measured with mutations: with the pre-check removed, all 54 tests still pass because the index catches it; with the pre-check and the catch both removed, the double-void and race tests fail with a raw `UniqueViolation`. So each layer is independently proven | PR #77; migration `0004`; subagent mutation table, re-checked by me for the lock case |
| The account lock, re-proven by a mutation | 2026-09-24 | A void and a new post on the same account both change the balance. Removing the `FOR UPDATE` lock from void makes the void-vs-post race test fail | The stored balance stays equal to its ledger under concurrent writes (the Phase 2 rule, now covering voids) | Number: with the lock removed, the race test failed 3 runs out of 3 (I ran it myself); restored, 54 of 54 pass | PR #77; `tests/test_transactions.py` |
| Stricter input at the door | 2026-09-24 | Create now rejects zero amounts (checked after rounding, so `-0` and `0.00` too), blank or control-character descriptions, and unknown fields. A zero row moves no money and can't be told apart from its own void | Bad entries get a readable 422 instead of silently entering the ledger | Number: 6 new money cases; one older test relied on the lax behaviour and was moved, not deleted | PR #77; `schemas/transaction.py`, `tests/test_money.py` |
| Transactions page: category picker, month and account filters, confirmed void | 2026-09-24 | React page; archived categories never reach the picker; voided rows are struck through and their reversal marked; Void asks for confirmation | Recording and correcting spending from the UI | Number: 207 backend and 53 frontend tests passing (re-run 2026-09-24). Two frontend mutations tried; one exposed a test that passed for the wrong reason (it checked before the async call happened), and I fixed the test | PR #77; `frontend/src/Transactions.tsx` |

**Not verified (say these before someone asks):** prod is on migration 0003, not 0004, so none of this is deployed yet; the void confirmation is a plain browser dialog; the owner checked void by hand in the dev app (not on prod, and not by an automated browser test); the mutation results for the backend other than the lock case are the subagent's report; the filters have been tested at month boundaries in the API but not with real data; no CI.

## Plain-language summary

You can't delete a transaction in this app. You void it, which adds a second entry that cancels the first. Nothing is erased, the totals come out right, and doing it twice by accident is impossible.

## Conversation script

**Opener.** I built a finance app where you can't delete anything. A mistake gets a cancelling entry instead.

**If they go technical.** Append-only ledger: a void is a reversal row pointing at the original, on the original's date. The hard part is the concurrency: two voids at once, or a void racing a new post. I put the balance update under a row lock and a partial unique index in the database as a backstop, and proved each layer by removing it and watching a test fail.

**If they stay non-technical.** It works like a paper ledger: you don't scratch out a line, you write a line that cancels it. Then anyone can see what happened.

**Follow-up line.** Wrote up how I tested the double-void case by breaking the code on purpose. Happy to share.

## LinkedIn draft (rough, not through brand/de-AI passes; not posted)

My finance app doesn't let you delete a transaction. You void it.

A void adds a second entry that cancels the first, on the same date, so that month adds up as if it never happened. The original stays. Anyone reading the history can see what was recorded and when it was undone.

The interesting part was making it safe when two things happen at once. Two voids of the same entry, or a void landing while a new transaction posts to the same account. I handled it with a row lock plus a database rule that allows only one cancelling entry per transaction.

Then I checked that each protection is real. I removed the lock and the concurrency test failed 3 times out of 3. I removed the pre-check and the database rule still caught the double void.

207 backend and 53 frontend tests pass. Not done yet: it isn't deployed to my production copy, so the database there is one migration behind.
