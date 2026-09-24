---
name: entry-point-first
description: Gets a user stalled before starting to a first move: one small rep, then a forced re-evaluate. Use for "I don't know where to start", "can't get started", "overwhelmed by this codebase". A plain "I'm building X, where do I start" with no stall is `design-scoping`. Not prioritization (`ticket-evaluation`) or a live bug (`debugging-layer-selection`).
---

# Entry Point First

Being stuck at the door is a different problem from being stuck in the room. The instinct — Claude's included — is to answer "where do I start?" with "the most important thing", which sounds responsible and is exactly what keeps the user frozen: the highest-value piece is usually the one with the most context, the most stakes, and the most ways to do it wrong. This skill answers the question that was actually asked: *what is the easiest thing to pick up right now?*

Two variables, kept apart:

- **Resistance** decides whether you start at all.
- **Impact** (immediate vs long-term) decides what to do once you are moving and can judge.

They are independent. Sometimes the easiest entry is also valuable — a bonus. Never plan around that overlap, and never wait for the "right" starting point.

## Step 1 — Does this skill apply?

| The user is… | Route |
|---|---|
| Unable to begin ("don't know where to start", "overwhelmed", "putting it off") | **This skill** |
| Already moving and asking what to do *next* / what matters most | Not here — Step 4 hand-off |
| Knows where to start and wants it done | Execution. Do it, no gate. |
| Facing a live bug or unexplained symptom | `debugging-layer-selection`, then `problem-solving-gates` Rubber Duck |
| Asking to be taught a concept | `learning-gate` |
| Stalled on a decision between options they already have | `problem-solving-gates` Options Generator |

If the stall is really *undefined scope* ("build me something for X" and no idea what X includes), the entry rep is a scoping rep, so still run this skill's Step 2, but the rep is "write three bullets", and the follow-on goes to `spec-drift-gate` / `design-scoping`, not to code.

One question only if the target is unclear: **"What is the thing you're stuck on getting into?"** Do not open with a clarifying list.

## Step 2 — Find the entry point (resistance only)

Propose **2–3 candidate entries yourself** — a stalled user should not be asked to generate them. Score each on resistance and nothing else:

| Resistance test | Low-resistance looks like |
|---|---|
| Size | Finishable in ~15–20 minutes |
| Stakes | Reversible; nothing shipped, nothing anyone reviews |
| Clarity | The first physical action is obvious (open this file, run this command) |
| Context needed | Little; doesn't require understanding the whole thing first |

Typical entries: read one file end-to-end and write two sentences on it; run the app / the tests and note what fails; fix a typo-grade or lint-grade issue in the area; write the first three bullets of the spec; open the ticket and list the questions it raises; rename one confusing thing. The same shape works outside code — write three bullets of what the piece has to answer; read one source and write two sentences on it; list the five sources you already know you'll use; run the "hello world" of a new tool once.

**Pick one** and say why it is easy — not why it is important. Do not rank by value here. If a candidate is obviously the most valuable, note it as *parked*, not chosen. It comes back at Step 4.

## Step 3 — Do one rep, then re-evaluate (the exit condition)

The user does the rep (or Claude does the mechanical part alongside if that lowers the bar — reading, running, listing). Set the exit condition when you pick the entry:

- **One completed rep, or about 20 minutes** — whichever comes first — triggers re-evaluation. Say this up front so the easy thing has an end.
- **Re-evaluate = look around from inside the work**: "What did you notice? What now looks like it matters — visibly changes your day-to-day? What did the rep make clearer or worse than you expected?" Ask this; do not answer it for them.
- **Two entry reps with no re-evaluation between them** is the avoidance failure — a string of easy things that never lead anywhere. Stop and force Step 4, whatever the mood.

If the first rep doesn't land (still frozen), the entry was too big — halve it. Don't escalate to the important thing.

## Step 4 — Hand off the value call

Once the user is immersed and immediate-impact options are visible, the choice is a different kind: immediate impact against slower, higher-ceiling value. Often the right answer is to deliberately deprioritize the immediate-impact item. That is a prioritization call, and it is not made here:

| What's on the table | Goes to |
|---|---|
| Tickets / backlog items to weigh against each other | `ticket-evaluation` |
| A feature or epic that needs breaking into stories | `user-story-decomposition` |
| A decision where the user now has candidates and a lean | `problem-solving-gates` Options Generator |
| A whole system needing scope | `design-scoping` |
| A build with no written spec | `spec-drift-gate` |
| Wants to build it file by file to understand it | `incremental-build-pacing` |
| Now wants a concept taught (e.g. "now explain ownership") after the rep | `learning-gate` |
| Non-engineering work (a thesis, a plan, a household project) | No sibling owns it — the value call stays in chat: ask the re-evaluate question, then help them weigh immediate impact against long-term value directly |

State the hand-off in one line and stop — do not re-derive their logic. What this skill contributes is the timing fact: the user can now judge value, because they are inside the work. If the entry rep is done and the work is a multi-file or multi-session build with no written spec, hand to `spec-drift-gate` for the spec before continuing.

## Never

- Answer "I don't know where to start" with "start with the most important thing" — that is the failure this skill exists to fix.
- Choose the entry by impact, or present the highest-value piece as the easy one.
- Ask a stalled user to come up with their own entry candidates first. Propose them.
- Stack a question wall — one question at most before proposing.
- Let an easy rep become the whole session. The exit condition is not optional.
- Moralize about procrastination or diagnose why they are stuck.
- Commit the user to an architecture, a plan, or a multi-file build through the entry rep. It stays small and reversible.

## Escape hatch

If the user says "I know what matters most, I just need to do it", they are not stuck — execution intent, drop this skill and help. If they want the value-first answer despite being stuck, give the entry point and name the high-value piece as parked; don't argue, don't withhold it.

## Example invocations

> "I just inherited a 200-file Django monolith and I'm overwhelmed. I don't know where to start. The ticket is to fix billing reconciliation."

Applies. Propose entries: run the test suite and list what fails; read the one file that exports the reconciliation entry point and write two sentences on it; find where the ticket's error string appears. Pick the first (zero context needed, reversible) and say so. Park "trace the whole reconciliation flow" as the high-value one. Exit: one rep or 20 minutes, then "what did you notice?".

> (after the rep) "Tests: 14 fail, 11 are the same missing env var. Reconciliation is in `ledger/sync.py`."

Re-evaluate step reached. Ask what now looks like it matters. They now hold enough to weigh "fix the env var (immediate, unblocks everyone)" against "trace reconciliation (the ticket)". That weighing is a prioritization call → one-line hand-off (`ticket-evaluation` if it is a ticket comparison), not restated here.

> "What should I prioritise this sprint — the refactor or the bug backlog?"

Doesn't apply. The user is not stuck at the door; that is `ticket-evaluation`.

## Portability

Repo-agnostic. Writes no project files; the entry proposals and re-evaluate prompt happen in chat. Copy the `entry-point-first/` directory into another repo's `.claude/skills/` to use it there; the Step 4 hand-off table names sibling skills that may not exist there — drop the rows for skills you don't have.

## Routing boundaries (full)

- Triggers on "I don't know where to start", "can't get started", "I keep putting this off", "overwhelmed by this codebase", "this is too big to even begin", "where do I even begin with this", "I've been staring at this all morning", "just inherited this repo and I'm lost".
- NOT `tech-decision-walkthrough` (choosing a build's stack) and NOT `incremental-build-pacing` (slowing the delivery of an already-specced build) — the user there is not stalled, they are mid-flow.
- NOT `learning-gate`, which classifies whether the user wants to learn and sets the assistance ceiling; a stalled start is an activation problem, not a learning-vs-execution one, and this skill routes from its Step 3 table.
- NOT `problem-solving-gates` Rubber Duck for a live bug or symptom ("where do I even start" on a broken thing is `debugging-layer-selection` first, then Rubber Duck).
- NOT `spec-drift-gate` — if the work is a multi-file build with no written spec the entry rep is at most "write three bullets of the spec", not code.
- NOT the prioritization call itself — once the user is moving and the question becomes "which of these matters most / immediate payoff vs long-term value", that is `ticket-evaluation` (a ticket), `user-story-decomposition` (an epic or feature to break down), or `problem-solving-gates` Options Generator (a decision where the user has candidates and a lean); this skill hands off to them and does not restate their logic.
