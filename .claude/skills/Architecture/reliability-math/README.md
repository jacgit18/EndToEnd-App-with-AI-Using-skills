# reliability-math skill

A **live-telemetry interpretation procedure** — five small pieces of arithmetic that
separate a confident read of production numbers from a fooled one: check percentiles before
trusting an average, use Little's Law (`L = λ × W`) to connect concurrency/arrival-rate/
latency instead of discussing them abstractly, convert an SLO percentage into actual
downtime minutes and compute the real burn during an active incident, read a utilization
number against the non-linear queueing-collapse curve instead of by gut feel, and run a
five-point checklist against any graph before believing what it shows.

Built from `SRE math every engineer should know.md` — a well-organized practical guide with a
genuine worked incident walkthrough (percentiles → utilization/queueing → error-budget burn
→ queue depth). The source note already had the content; the skill adds the forcing
function — computed numbers on the user's actual figures, not a fluent restatement of the
concepts — the same failure mode `technical-cost-decision` targets for cost reasoning
("cost reasoning fails at the division, not at the concepts").

## Where it sits

This is a **procedure skill, not a decision-gate** — the same shape as
`failure-mode-analysis` and `document-page-check`. It doesn't withhold analysis pending a
user rep; it runs the math on whatever numbers are in front of it and names precisely what's
missing to compute the rest.

```
reliability-math   →  read the live numbers correctly: percentiles, Little's Law,
                       error-budget burn, utilization vs. the collapse curve, graph pitfalls
      │
      ├─ a hypothesis becomes reachable   →  problem-solving-gates (Rubber Duck)
      ├─ a bottleneck gets a number       →  problem-solving-gates (Optimization) — that
      │                                       number is the "measurement" its gate requires
      ├─ a pressure is now quantified     →  resilience-strategy (picks the mechanism)
      └─ headroom/observability-stack $   →  technical-cost-decision
```

Nearest neighbours, and the boundary held with each:

- **`capacity-estimation`** — a-priori sizing for a system that doesn't exist yet, from
  stated assumptions. This skill assumes a *live* system with real telemetry. Its
  `target_utilization ~0.6–0.7` figure is the number `reliability-math`'s Rule 4 explains the
  mechanism behind (the queueing-collapse curve) — this skill doesn't re-derive a different
  target, it cites that one.
- **`observability-strategy`** — decides *which* signals and SLOs to instrument in the first
  place. This skill assumes the SLI/SLO already exists and does the live arithmetic against
  it (Rule 3's error-budget-to-minutes conversion, in particular).
- **`resilience-strategy`** — picks the protection mechanism (shedding, rate limiting, circuit
  breakers) once a pressure is named and quantified. This skill's Rule 4 utilization/queueing
  reading is exactly the quantified pressure that skill's gate asks for — feeds it, doesn't
  duplicate it.
- **`problem-solving-gates`** (Rubber Duck / Optimization) — both require the user to already
  have a hypothesis or a measurement before Claude engages. `reliability-math` is what runs
  *before* either exists, when the raw dashboard numbers are the only input — it produces the
  hypothesis-forming read or the bottleneck number those gates then require.

## The shape

Not a gate — it needs live numbers to work with (a percentile breakdown or at least an
average to challenge, an arrival rate and/or latency, a stated or observed utilization, an
SLO and an incident's elapsed time), and asks for whichever of those are missing rather than
inventing them, but it never says "show me your own analysis first."

The walk: percentiles first → utilization/queueing read → Little's Law arithmetic →
error-budget burn (if an incident is active) → graph/cross-reference check → a diagnosis
stated plainly, with a handoff to whichever skill owns what comes next.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The five rules with their formulas and worked arithmetic, the walk order, the output block, red flags, a condensed worked incident example. |

Single-file skill — the five rules are compact enough that a separate reference file would
just be the same content moved, unlike `capacity-estimation` or `resilience-strategy`'s
larger worked-example/mechanism catalogs.

## Output

A single output block in chat: the symptom, computed percentiles (or a flag that only an
average was available), the utilization reading against the collapse curve, the Little's Law
computation and what it implies, the error-budget burn (or `n/a` outside an active incident),
any graph-literacy flags raised, a plain-language diagnosis, and a named handoff to whichever
skill owns the next step. Writes no files.

## Deliberately out of scope

- **A system with no live traffic** — a-priori sizing → `capacity-estimation`.
- **Deciding what to instrument** — → `observability-strategy`.
- **Picking a protection mechanism** — → `resilience-strategy`.
- **A debugging session with an existing hypothesis, or an optimization with an existing
  profile** — → `problem-solving-gates`, directly; this skill is for before either exists.
- **The dollar cost of headroom or the observability stack** — → `technical-cost-decision`.

## Using it in another repo

Repo-agnostic and self-contained — writes nothing, reads no `docs/` tree.

```
cp -r ".claude/skills/Architecture/reliability-math" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Screened and tested 2026-09-05 — see project memory for the isolation-screen result and the
`skill-interaction-testing` scenarios run against `capacity-estimation`, `observability-
strategy`, `resilience-strategy`, and `problem-solving-gates`.
