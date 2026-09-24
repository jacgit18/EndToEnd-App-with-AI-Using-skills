---
name: decision-journal
description: Two modes: Log a judgment call with reasoning, alternatives, stated confidence, a falsifiable prediction and review-by date; or Review it later to compare outcome to prediction and calibrate. Use when "log this decision", "add this to my decision journal", "how calibrated am I". Not a live gate. NOT `problem-journal` (bug post-mortem), NOT `tech-decision-walkthrough` (makes the choice/ADR), NOT `session-handoff`.
---

# Decision Journal

A decision made without a written prediction can't be wrong, so it can't teach anything: in hindsight every outcome looks like what you expected. This skill closes that loop for judgment calls — record the call with a confidence and a falsifiable prediction, then come back and compare. The aim is to learn how often *your* calls hold, and why they miss, not to keep records for anyone else.

| Ask | Mode |
|---|---|
| "log this decision", "I decided X — record why", "write this down so I can check it later" | **Log** — one entry in `.claude/_Prompts/decisions-log.md` |
| A logged review-by has come due; "review my decision from …", "did that pan out", "how good are my calls" | **Review** — fill in the outcome on the entry, then a calibration read |

If it's unclear which, ask in one line. Do not run both unless asked.

## When it applies (and when it doesn't)

It applies when the user *wants* a decision recorded or reviewed. It does not fire because a decision was made, and Claude does not offer it unprompted — a decision journal that logs everything is a decision journal nobody reviews. It also does not apply to:

| Situation | Route |
|---|---|
| Still choosing between options | `tech-decision-walkthrough` (whole build's stack) or `problem-solving-gates` Options Generator (user has candidates + a lean) |
| A resolved bug and whether it's worth learning from | `problem-journal` |
| A trade | `anthropic-skills:trading-decision-journal` |
| Saving context to resume later | `session-handoff` |
| Turning shipped work into something to post or say | `explaining-my-work` |

Routine choices (a variable name, a lint rule) aren't worth an entry. If it's unclear whether a decision is big enough, ask in one line rather than logging it.

## Mode: Log

Run the gate before writing. Every field must come from the user, not from Claude:

1. **The decision** — one sentence, in their words.
2. **The reasoning** — why, in a sentence or two. Claude may restate it back to check it; it does not improve it.
3. **Alternatives rejected** — what else was on the table and the one reason each lost. "None considered" is a valid, honest entry.
4. **Confidence** — a percentage that this will turn out to be the right call. A range is fine; "pretty sure" is not — ask for a number.
5. **A falsifiable prediction** — something that will be observably true or false later if the call was right ("p95 stays under 300 ms after the migration", "we won't add a second data store this quarter", "the team ships the v1 without a rewrite"). If the user can't produce one, ask "what would be true in N weeks if this was the right call?" — Claude may offer the *shape* of a prediction (a metric, a behavior, a timeframe), never its content.
6. **Review-by** — a date or an observable trigger ("after the first prod incident on this path"). Without one, the entry never gets reviewed.

If a field is missing, say which and stop; do not fill it in (the Escape hatch below is the one explicit override). Once all six are present, write the entry. Write dates out in full — a review-by given without a year ("Nov 15") is written as the next occurrence with the year (`2026-11-15`).

**If the decision already has an ADR** (`tech-decision-walkthrough` records these to `docs/architecture/decisions/NNN-<slug>.md`), link it and do not copy it. The journal entry adds only what the ADR lacks: confidence, prediction, review-by. Take the decision, alternatives and reasoning from the ADR by reference.

### Retrospective entry (the decision has already played out)

When the user asks to log a decision whose outcome is already known ("the retry storm was my March call — log this so I learn from it"), the prediction can't be blind. The six-field gate above does not apply; instead:

1. Ask the user for what they believed *at the time* — their confidence then and what they expected to be true — and take "I didn't think about it" as a valid answer. Don't reconstruct these for them.
2. Record the outcome they already know, and set `Status: retrospective` and `Review by: n/a (already played out)`.
3. Once they've answered, write the entry and ask the Review's "what did your reasoning assume that didn't hold?" question in the same turn — that is the whole point of the entry.

Retrospective entries are **excluded from the calibration count** (a prediction made after the outcome isn't a calibration data point). If the trigger was a bug, the bug's symptom / cause / fix still goes to `problem-journal` — offer it in one line.

### Entry format

Append to `.claude/_Prompts/decisions-log.md` (create it with a `# Decision Journal` heading if absent):

```markdown
## D-2026-09-23-<slug> — <short decision title>

**Decision:** <one sentence>
**Reasoning:** <why>
**Rejected:** <alternative — why it lost | none considered>
**ADR:** <docs/architecture/decisions/NNN-slug.md | none>
**Confidence:** <NN%>
**Prediction:** <falsifiable statement>
**Review by:** <date or trigger>
**Status:** open

### Review
_(filled in later)_
```

Report one line: the entry ID and the review-by. Do not restate the entry back.

## Mode: Review

Start by finding the entry: by ID, or by the most recent open entry whose review-by has arrived. Then:

1. **Outcome first, from the user.** Ask what actually happened relative to the prediction. If they don't know, that is itself the finding — the prediction wasn't checkable — and the entry closes as such.
2. **Compare, plainly.** State hit or miss against the stated prediction, and the confidence next to it ("you said 75%; it missed"). A miss is the useful result — name it as one, no consolation, no scolding.
3. **Ask, don't grade.** "What did your reasoning assume that did or didn't hold?" The user answers. Claude may ask a follow-up that points at a stated assumption; it does not supply the explanation, and it does not say whether the original decision was "good" — a good decision can miss and a bad one can hit.
4. **Write the review into the entry:** outcome, hit/miss, the user's stated assumption that held or broke, and set `Status: reviewed`.
5. **Calibration read, from the record.** Count reviewed entries by grepping `decisions-log.md` — how many reviewed, how many hit, and how the hits split by confidence band (≥80%, 50–79%, <50%). Count only `Status: reviewed` entries — `retrospective` and `none stated` entries are excluded. Report the real numbers ("6 reviewed: 3 of 4 at ≥80% hit, 1 of 2 below 80%"), and say plainly when the sample is too small to mean anything. Never assert "you're overconfident" or "well-calibrated" without the count behind it, and not from fewer than ~5 reviewed entries. This is the same rule `problem-journal` applies to a worth-learning verdict.

**A bug that exposed a bad decision** (from `problem-journal` Journal mode) can spawn a decision entry for the call that caused it — a Retrospective entry above if it was never logged, or a Review if it was. That entry records the decision's outcome; the bug's own symptom / cause / fix stays in `problems-log.md`.

## Open reviews

Whenever this skill runs in either mode, scan `decisions-log.md` for entries with `Status: open` whose review-by has passed and list them in one line ("2 reviews due: D-…, D-…"). That is the only nudge. The skill does not poll and does not interrupt other work; an automated reminder would be a hook, and that is a separate decision.

## Never

- Invent the confidence, the prediction, or the review-by for the user.
- Log a decision because one was made. Only when the user wants it recorded.
- Grade the original decision as good or bad from the outcome alone.
- Copy an ADR into the entry.
- Write a calibration claim without the count, or from a handful of entries.
- Backfill: don't reconstruct confidence or a prediction for a decision made in an old session. Ask the user to state them, and use the Retrospective path — the prediction is no longer blind, which the calibration read must respect.
- Let the log become documentation. If an entry is being written for someone else to read, that is `explaining-my-work` or an ADR.

## Escape hatch

If the user says "just write it down, I don't have a number", log the decision, reasoning and rejected alternatives with `Confidence: none stated` and `Prediction: none stated`, set no review-by, and say once that such an entry can't be reviewed later. Don't argue and don't fill the blanks yourself.

## Example invocations

> "I decided to keep Postgres for the ledger instead of adding a time-series store. Log it — I'm about 80% sure we won't regret it, and I expect we won't need a second store this quarter. Check me at the end of Q4."

All six fields present. Write the entry with the confidence, the prediction ("no second data store needed by end of Q4") and review-by end of Q4. One-line report.

> "Log that we're moving to a queue for webhooks."

Missing confidence, prediction and review-by. Say which are missing and stop; don't propose them.

> "It's the end of Q4 — did my Postgres decision pan out?"

Review. Ask what actually happened against "no second store this quarter"; compare to the 80%; ask what the reasoning assumed; write the review in; give a calibration count only if enough entries are reviewed.

> "The retry storm we just fixed — was that worth learning from?"

Not this skill. `problem-journal`.

## Portability

Repo-agnostic. Assumes only `.claude/_Prompts/` (also used by `problem-journal` and `prompt-archive`); the ADR link works with any ADR convention — drop the `tech-decision-walkthrough` path if that skill isn't present. Copy the `decision-journal/` directory into another repo's `.claude/skills/` to use it there.

## Routing boundaries (full)

- Two modes, picked by what's being asked.
- Mode Log — the user has made (or is committing to) a non-trivial engineering or judgment call and wants it recorded so it can be checked later — "log this decision", "I decided to X, record why", "add this to my decision journal", "write this down so I can check it in a month" — writes a short entry to `.claude/_Prompts/decisions-log.md` with the decision, the reasoning, the alternatives rejected, a stated confidence (%), a concrete falsifiable prediction, and a review-by date or trigger.
- Mode Review — the review-by date or trigger has arrived, or the user asks "review my decision from last month", "did that decision pan out", "how good are my calls", "how calibrated am I" — compares what actually happened to the prediction and the confidence, names the hit or miss, and asks the user what their reasoning assumed that did or didn't hold; the user does that reasoning, Claude does not grade it for them.
- Purpose is calibration of the user's own judgment over time, not documentation for other people.
- The prediction and the confidence must come from the user — Claude never invents them.
- NOT a live gate and NOT on every decision: it fires only when the user wants a decision recorded or reviewed, or a logged review-by has come due; it never interrupts a decision in progress.
- NOT `problem-journal` — that is the resolved-bug post-mortem (symptom / cause / fix / worth-learning verdict); a bug that exposed a bad decision may spawn a Review here, but the bug's own record stays there.
- NOT `tech-decision-walkthrough` — that chooses the option and writes the ADR; this records a calibration layer (confidence, prediction, review-by) on a choice already made and reviews it later, so an ADR is a natural Log input and is linked, not copied.
- NOT `problem-solving-gates` Options Generator (making the decision) and NOT `learning-gate`.
- NOT `anthropic-skills:trading-decision-journal` — the same idea for trades only; a trade goes there, not here.
- NOT `session-handoff` (in-progress context to resume later) and NOT `explaining-my-work` (public writeups of what shipped).
- NOT `prompt-archive` (raw prompt logs).
