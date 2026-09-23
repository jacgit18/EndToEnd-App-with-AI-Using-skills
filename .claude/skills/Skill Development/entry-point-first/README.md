# entry-point-first

A getting-started gate. When the user is stuck *before* starting — can't get in the door — this
skill withholds the "start with the most important thing" answer and instead proposes the
lowest-resistance entry point, has the user do one rep, then forces a re-evaluate from inside the
work. The value-vs-payoff prioritization call is handed to the skills that already own it.

It is a **gate**: it withholds a value-ranked answer until the user has done one entry rep, and it
withholds a *second* easy rep until the re-evaluate has happened (the avoidance guard).

## Where it sits

| Boundary | Skill | Split |
|---|---|---|
| The prioritization call once the user is moving | `ticket-evaluation`, `user-story-decomposition`, `problem-solving-gates` Options Generator, `design-scoping` | Those weigh immediate impact against long-term value. This skill only makes the user capable of judging, then hands off in one line. |
| Whether the user wants to learn; the assistance ceiling | `learning-gate` | A stalled start is an activation problem, not a learning-vs-execution one. `learning-gate` routes here from its Step 3 table; this skill does not ask its "what have you concluded?" question. |
| A live bug / "where do I even start" on a broken thing | `debugging-layer-selection` → `problem-solving-gates` Rubber Duck | There the stall is about *evidence location*, and a hypothesis is the rep. Here nothing is broken. |
| A build with no written spec | `spec-drift-gate` | The entry rep is at most "write three bullets", never code that commits to a structure. |
| A whole system to scope | `design-scoping` | Entry rep can be a scoping rep; the follow-on goes there. |
| Delivery pace of a specced build | `incremental-build-pacing` | The user there is mid-flow. This skill is for the door, that one is for the corridor. |
| Choosing a stack | `tech-decision-walkthrough` | A decision, not an activation problem. |
| Mapping a repo | `anthropic-skills:repo-scanner` | Can chain in as the entry rep when the entry is "get a map of this codebase". |

## Files

| File | Role |
|---|---|
| `SKILL.md` | Apply check, entry-point selection (resistance only), the one-rep + exit condition, the hand-off table, Never list, escape hatch, examples. |

## Design choices

- **Two axes, deliberately separated.** Resistance governs starting; impact governs choosing once
  immersed. Conflating them is how people stall waiting for the right start, or start easy and
  never arrive anywhere.
- **Claude proposes the entries.** Most gates make the user generate the rep. Here the user is
  frozen, so requiring them to invent entry candidates recreates the stall. The rep the user owns
  is doing the entry and reading their own re-evaluation.
- **Exit condition is load-bearing.** "Start easy" without an end becomes permanent avoidance. One
  rep or ~20 minutes triggers re-evaluation; two reps without it forces it.
- **Doesn't restate prioritization.** Step 4 is a routing table. The skill's only claim there is
  the timing fact — the user can now judge because they are inside the work.
- **Narrow trigger.** Fires on being stuck at the door, not on "what should I do next".

## To try it

- "I don't know where to start with this repo" → proposes entries, picks by resistance, sets the exit.
- "Overwhelmed by this ticket, can't get started" → entry rep is reading + listing questions, then re-evaluate.
- "Which of these two tickets first?" → doesn't apply; `ticket-evaluation`.
- "I know exactly what to do, just do it" → execution; drop the skill.
