---
name: idea-to-first-test
description: Turns a raw idea into one cheap test: an uncensored 100x pass, the kernel (real need), then the riskiest assumption tagged BUILD or DEMAND and the cheapest test touching it. Use for "wild idea", "what if the app could…", "how do I test demand". Not a stalled start (`entry-point-first`), system scope (`design-scoping`), a written ticket (`ticket-evaluation`), stories (`user-story-decomposition`), a spec (`spec-drift-gate`).
---

# Idea to First Test

A big idea fails two ways: it gets cut down before it is understood (judgment too early), or it gets built whole (judgment never). This skill runs the two as separate passes and never blends them in one section. Divergent pass first, judgment second.

## Step 1 — Does this skill apply?

| The user is… | Route |
|---|---|
| Holding an idea, wild or vague, and asking if/how to pursue it | **This skill** |
| Unable to begin at all ("don't know where to start") | `entry-point-first` |
| Naming a system to build ("design a billing system") | `design-scoping` |
| Weighing an existing ticket or backlog item, or a written feature to size | `ticket-evaluation` |
| Has a settled feature and wants stories / acceptance criteria | `user-story-decomposition` |
| Asking for a one-line build with no spec | `spec-drift-gate` |
| Choosing between options they already have | `problem-solving-gates` Options Generator |
| Asking what a concept is | `learning-gate` |

Idea too vague to restate in one sentence: ask for that one sentence before Step 2, nothing else.

## Step 2 — Aspirational pass (judgment off)

Restate the idea in one line, then push it past its limits. Give 4–6 oversized variants, no feasibility comments, no "but":

- 100x the users / 100x the data
- free, instant, or zero-effort for the user
- "what would a game / an airline / a bank do here?"
- the version with no constraint on budget or time

Then extract the **kernel** for each: the real need the wild version is reaching for, in one clause. Kernels that repeat across variants are the signal. Name the 1–2 recurring ones. Nothing in this section is filtered, ranked, or doubted.

## Step 3 — Grounding pass (judgment on)

Start a new section. Pick the strongest recurring kernel (the user may override), then:

1. **Outcome** in one sentence.
2. **Done check** — something observable, not "feels good".
3. **Riskiest assumption**, tagged:
   - **BUILD** — can this be made to work (feasibility, correctness, scope)?
   - **DEMAND** — will anyone use or pay for it, and how would they find it?
   Name the one that kills the idea if false. Flag any assumption the user stated as fact and has not tested.
4. **First test** — must touch that assumption directly. Setup, tooling and polish do not count.
   - BUILD: tracer bullet — input → one step → visible output, hardcoded and ugly. First action under 30 minutes, 2-hour timebox.
   - DEMAND: cheapest of a conversation, a one-page landing page with a real ask, or the manual version done by hand for one person. Add: who the customer is and what they do today instead. First action (the message, the page, the list of who to ask) under 30 minutes; the test itself runs days, so set a result date, not a 2-hour box.

## Output

```
Idea: <one line>
Wild variants / kernels: <short list>     <- no judgment in this block
--- grounding ---
Outcome / Done check:
Riskiest assumption: [BUILD|DEMAND] <it>   Untested claims: <list or none>
First test: <what>  First action: <≤30 min>  Timebox/result date:
```

## Never

- Filter, rank or doubt anything in Step 2, or cheerlead in Step 3.
- Pick a first test that is setup, scaffolding or polish.
- Treat a BUILD test as if it answered a DEMAND question (a working prototype does not show anyone wants it).
- Produce more than the block above, stage maps, or a full plan. A bigger ask goes to `design-scoping` or `spec-drift-gate`; if DEMAND is still untested at that hand-off, say so in one line so the spec names it as an open risk.
- Build a second idea's grounding in the same run. One idea, one first test.

## Escape hatch

"Skip the brainstorm, just ground it" → run Step 3 only; "already decided to build" still gets the riskiest-assumption tag but no spec questions (`spec-drift-gate` waits until a spec is asked for). "Just brainstorm" → run Step 2 only and say grounding is pending.

## Example invocations

> "Wild idea: my finance dashboard auto-negotiates my bills for me."

Applies. Variants: negotiates every bill instantly for free; works for all users nationwide; "what would an airline do" → dynamic repricing alerts. Kernels: "I overpay and never notice." Grounding: riskiest assumption is DEMAND-side: providers may not move on price at all. Tag DEMAND, not BUILD; first test is calling about one bill by hand and noting the result.

> "Should we use Postgres or Mongo for this?"

Doesn't apply. Choosing between known options is `database-architecture` / `problem-solving-gates`.

> "I can't even begin on this idea."

Doesn't apply. `entry-point-first`.
