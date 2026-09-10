# tech-decision-walkthrough

A coached, conversational **procedure** for choosing a build's technologies out loud — one
decision at a time, system-design-interview style — with alternatives, axes, and tradeoffs made
explicit, ending each decision in a recommendation, the user's call, and an ADR. It is not a
withholding gate; `learning-gate` sets the assistance level and this skill runs the loop at it.

## Where it sits

| Boundary | Skill | Split |
|---|---|---|
| Scope: purpose, audience, non-functional targets, *which* 1–2 decisions get deep design | `design-scoping` | Upstream. It produces the decision list; this skill walks it. A whole-system one-liner goes there first. |
| The inverse stance — make the user bring candidates + a lean, withhold Claude's list | `problem-solving-gates` (Options Generator) | That gate forces the user to generate. This skill teaches the option space. If the user wants to be gated into committing first, hand to Options Generator. |
| Interview *rehearsal* — practice defending a choice, mock system-design interview, "poke holes, don't tell me the answer" | `system-design-communication` (esp. Mode 3, Tradeoff Defense) | That skill is rehearsal on a hypothetical or already-made choice, names no winner, writes nothing. This skill makes real not-yet-made decisions, recommends, and records an ADR each. |
| The deep design of one load-bearing decision | `api-interface-style`, `microservices-decision`, `database-architecture`, `access-control-modeling`, `deployment-strategy`, `serverless-execution-model`, `bff-gateway-placement`, `migration-cutover`, `config-and-secrets-management`, `cloud-iam-boundary`, `capacity-estimation` | This skill routes into them for load-bearing decisions and folds their output into the ADR. A single already-isolated decision with its inputs ready goes straight to the specialist. |
| The recurring-cost axis of one decision | `technical-cost-decision` | This skill invokes it as one axis among several when a choice has real per-unit or volume cost. |
| Building the already-chosen stack, file by file, paced to comprehension | `incremental-build-pacing` | Chains after. This skill chooses; that one builds. |
| Whether the user wants to learn this at all, and how much reasoning Claude does | `learning-gate` | Routes here from its Step 3 table; its assistance level picks the register (collaborative vs interviewer). |

## The chain

```
design-scoping           →  what to build, which decisions matter
tech-decision-walkthrough →  walk each decision, write ADRs   ← this skill
spec-drift-gate           →  fold the ADRs into a build spec
incremental-build-pacing  →  build it slowly, file by file
```

## Files

| File | Role |
|---|---|
| `SKILL.md` | Preconditions, decision ordering, the per-decision loop, depth control, registers, Never list, escape hatch, examples. |
| `decision-loop.md` | The loop in detail, the two registers, axes libraries for the common build decisions (runtime, framework, datastore, data-access, frontend, API style, auth, async, packaging, deployment), the ADR shape, anti-patterns. |
| `library-vetting.md` | Axes + how-to-check for a "which package for X" decision — the supply-chain read (weight, transitive deps, maintenance, bus factor, license, security patch latency, API churn, exit cost) the generic axes libraries don't carry. Depth-tiered. |

## Design choices

- **Procedure, not a gate.** It doesn't withhold an answer pending preconditions — it runs a
  coached loop calibrated by `learning-gate`. The one hard line is the inverse-of-Options-
  Generator boundary: this skill generates and teaches the option space; it never withholds the
  list to force the user to produce it (that's a different skill).
- **Depth scales with blast radius.** A full loop for the datastore; one line for the formatter.
  Reuses `design-scoping`'s significance axis so the two agree on what "load-bearing" means.
- **Every loop lands a decision.** The failure mode it exists to prevent is equally the silent
  fully-formed stack *and* the comparison lecture with no verdict — Step 6 (recommendation +
  because) is mandatory.
- **Two registers.** Collaborative by default (Claude presents and recommends); interviewer on
  request (user proposes and defends, Claude probes). Same skill, different assistance level.

## To try it

- "Walk me through the stack for this app like a system design interview" → collaborative, ordered
  decision list, one loop per decision, an ADR each.
- "I think Postgres is right, talk me out of it" → single loop, honest score, likely-agree with a
  because.
- "Just pick a linter" → escape hatch, one line, no loop.
- "Give me the auth options and make me choose" → `problem-solving-gates` Options Generator, not
  here.
