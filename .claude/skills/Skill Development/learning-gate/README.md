# learning-gate

A traffic controller for how much thinking Claude does on a request. Built from `learning Gate.md`.

It sits *above* `problem-solving-gates`: this skill decides **whether** you should perform the
reasoning yourself right now; `problem-solving-gates` defines **what** the reasoning is for
debugging, architecture decisions, and understanding checks. This skill does not modify that one
— they coexist.

## The four steps

1. **Classify intent** — reference / execution / learning / ambiguous. Only `learning` (or an
   explicit request) gets gated. Reference lookups and execution work are answered directly.
2. **Determine learning state** — S0 no exposure, S1 thinks they know, S2 attempting, S3
   consolidating.
3. **Name the next rep** — the piece of reasoning you can reasonably do yourself; require it
   before supplying it. Thin pointer table hands off to the domain skill.
4. **Set the assistance level** — 0 Socratic → 5 Execution, defaulted from the state, overridable
   by you ("stay at level 1").

## Files

| File | Role |
|---|---|
| `SKILL.md` | The four steps, the Never list, the escape hatch, examples. |
| `concept-learning.md` | The S0 path this skill owns end to end: teach → example → contrast → scenario → retrieval. |
| `guided-walkthrough.md` | The S0–S2 delivery protocol for a multi-step task the user performs themselves: map the path, coach one step at a time, verify each before revealing the next. |
| `assistance-levels.md` | The 0–5 scale, what's allowed at each, defaults per state. |

## Design choices

- **Broad trigger, intent check first.** Fires on learnable material but its first act is to check
  whether you actually want to learn it or just want the answer. On execution/reference it gets
  out of the way — the doc is emphatic about not being paternalistic.
- **Coexists with problem-solving-gates**, doesn't absorb it.
- **Assistance levels are user-facing** — you can set a ceiling by number for a thread — and also
  internal calibration language. No persistent config file; the ceiling resets per thread.
- **Owns concept-learning and guided walkthroughs, defers the rest.** State S0 (learning a new
  concept) and S0–S2 step-by-step walkthroughs of a task the user performs themselves are fully
  handled here. Debug / architecture / test / db reps get a one-line pointer and defer to the
  domain skill.

## How to steer it

| You say | Effect |
|---|---|
| "learning mode" / "I'm trying to learn this" | Apply the gate; default to a low assistance level. |
| "just tell me" / "execution mode" / "I know this, implement it" | Stop gating for the rest of the thread. |
| "stay at level 1" / "level 3 is fine here" | Set the assistance ceiling for the thread. |
| "what have I done already? nothing" | Routes you to S0 — teach the prerequisite, then a rep. |

## Not built

The doc sketches a larger tree (Practice Gates for code/test/database as siblings of
problem-solving-gates). Not in scope here. If practice-oriented gating for implementation work
starts needing its own rubric, that becomes a sibling skill this one points to from the Step 3
table.


## The anti-paternalism guardrails (per the doc's warnings)
First action is always the intent check — execution and reference work bypass the gate entirely.
"just tell me" / "execution mode" switches it off mid-thread, no argument.
Never list explicitly bans: manufacturing difficulty, withholding prerequisites, leading questions that reveal the answer, treating time-stuck as a rep, gating routine production work.

## To try it
"What is a bloom filter?" with no other signal → should ask "what have you already done or concluded?" before teaching.
"What's the syntax for a Postgres partial index?" → should just answer, no gate.
"I think I understand bloom filters — [explanation]. Check me?" → should test with a scenario, not re-explain (hands to problem-solving-gates).
One thing to check: problem-solving-gates/SKILL.md doesn't reference learning-gate back. Optional, but a one-line "this is the concept-learning / intent-routing layer above these modes" cross-link would make the pair discoverable from either direction. Want that added?
