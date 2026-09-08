# failure-mode-analysis skill

A **structured FMEA / pre-mortem procedure** over a design, workflow, or service graph the
user describes. It walks every component and every interaction, enumerates how each can
fail across **nine categories** (functional, availability, performance, consistency,
integration, dependency, security, operational, human/process), records each as
`cause → manifestation → impact` with a blast radius, **scores and ranks** them
(RPN = severity × occurrence × detection, or a lighter severity × likelihood grid), and
emits a **prioritized failure-mode register** plus a high-severity watchlist and a set of
handoffs.

Built from `Architecture/01. System Design/Failure Modes.md` (the nine categories and the
failure-mode / bug / incident distinction) plus the chaos / fault-injection thread in
`Architecture/Monitoring & Observability.md`. The source note explains *what* failure modes
are but gives **no repeatable procedure, no scoring rubric, and no register format** — the
skill adds all three (`SKILL.md` the walk order, `scoring-and-register.md` the rubric and
layout, `nine-categories.md` the per-category probe questions).

## Where it sits

This is a **procedure skill, not a decision-gate** — the same shape as
`Documents/document-page-check`. It does not withhold analysis pending a user rep; it runs a
walk and produces an artifact, and the only thing it asks the user is *register-only* vs
*block-sign-off-until-triaged*.

```
failure-mode-analysis   →  enumerate + rank EVERY way this design can fail, proactively, all 9 categories   (this skill)  → register
      │
      ├─ dependency / overload / cascade rows   →  resilience-strategy   (pick the protection mechanism)
      ├─ impact ranking + detection-gap rows    →  observability-strategy (what to alert on)
      ├─ ranked rows as a target list           →  test-strategy         (fault-injection / chaos scope)
      ├─ functional / consistency logic rows    →  engineering backlog
      └─ non-trivial security rows              →  a real threat-modelling pass
```

`failure-mode-analysis` runs **when nothing is on fire**. Its counterpart
`problem-solving-gates` (Rubber Duck) runs when **one** thing is on fire and there's a
hypothesis. Its counterpart `resilience-strategy` runs when **one** pressure is already
known and needs a mechanism — this skill is what surfaces those pressures in the first
place.

## The shape

Not a gate. It needs a system to analyze — a component inventory, an interaction inventory,
a scope boundary, an altitude, a definition of "severe" for this system, and a rough note
of what detection exists today. If those are missing it asks for them (it won't invent an
architecture to critique), but it never says "show me your own analysis first".

The walk:

1. Frame the system (restate the two inventories, draw the scope boundary).
2. Choose the scoring scheme — RPN (rigorous, long-lived/regulated) or the 5×5 grid (fast
   design-review pass).
3. Walk each **component** × the nine categories.
4. Walk each **interaction** × the interaction-heavy categories (integration, dependency,
   consistency, performance, availability; async adds loss / dup / reorder / poison / lag).
5. Record each mode as `cause → manifestation → impact + blast radius`.
6. Score, rank, and apply the **severity override** (max-severity modes go on a watchlist
   regardless of RPN).
7. Emit the register + the handoff lists.
8. Ask: register-only, or block sign-off until every watchlist / above-threshold row has an
   owner and a decision.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Inputs the procedure needs, the 8-step walk, the output block, the register-only vs block-sign-off ask, worked invocations. |
| `nine-categories.md` | The nine categories, each with probe questions, distributed-systems / async specifics, and an example `cause → manifestation → impact` row. A table of which categories to weight per component type. |
| `scoring-and-register.md` | Scheme A (RPN — S/O/D 1–10 scales, action thresholds), Scheme B (5×5 severity × likelihood grid), the severity override, the register / watchlist / acceptance-log table formats, and worked scoring examples. |

## Output

1. A summary block + the full register table and watchlist in chat.
2. On request or in block-sign-off mode: a **living document** at
   `docs/architecture/failure-modes/<system-slug>.md` (not the ADR tree — this is tracked
   and updated as the design changes), including an acceptance log where each triaged row
   records owner + decision + date + revisit trigger.

Stops before designing the mitigations, the alerts, or the tests.

## Interaction with sibling skills

- **Feeds `resilience-strategy`** — the dependency / overload / cascade rows are its input.
  Boundary: this skill *enumerates and prioritizes every mode across the whole design and
  all nine categories*; `resilience-strategy` *picks the protection mechanism for one
  already-known overload or dependency failure*. Reciprocal note added there.
- **Feeds `observability-strategy`** — the impact ranking and the rows with a bad detection
  score are where its alerting design starts (its SKILL already says "start from the SLIs
  and the top failure modes"). Reciprocal note added there.
- **Feeds `test-strategy`** — the ranked register is its fault-injection / chaos target
  list, and its "cost of failure per area" gate input. Reciprocal note added there.
- **Distinct from `problem-solving-gates` (Rubber Duck)** — that is one bug, one hypothesis,
  happening now. This is proactive and exhaustive, run when nothing is on fire.
- **Hands the threshold to `capacity-estimation`** — when a mode's trigger is "load exceeds
  capacity", the number (what it can take, what binds first) is that skill's; this skill
  records the mode.
- **Coarse security only** — the security category is a sweep for obvious gaps; a real
  threat model / STRIDE / pen-test is a separate, deeper exercise.

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `resilience-strategy` (enumerate-all vs mechanism-for-one), `problem-solving-gates`
(proactive vs one-bug-now), and `test-strategy` (target list vs test mix).

## Using it in another repo

Repo-agnostic. Writes a living register to `docs/architecture/failure-modes/`.

```
cp -r ".claude/skills/Architecture/failure-mode-analysis" /path/to/other-repo/.claude/skills/
```
