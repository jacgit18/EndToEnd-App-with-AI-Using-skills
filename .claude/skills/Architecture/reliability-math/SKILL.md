---
name: reliability-math
description: Use when interpreting live production telemetry during an active investigation — a dashboard that shows a fine average while users report a problem, judging whether a stated CPU/utilization number is dangerous, converting an SLO percentage into actual downtime minutes and checking error-budget burn during an ongoing incident, reasoning about how latency and throughput/concurrency relate (Little's Law), or reading a graph, heatmap, or dashboard that might be misleading (an average standing in for a percentile, a smoothed time window, a log-scale axis). Forces the actual arithmetic — a percentile breakdown, an L=λ×W computation, an error-budget-to-minutes conversion, a utilization reading against the queueing-collapse curve — instead of a qualitative discussion of the concepts, the same failure mode `technical-cost-decision` targets for cost reasoning. This is a live-system interpretation procedure, not a gate — it doesn't withhold analysis pending a user rep. It is not `problem-solving-gates`'s job: once this analysis makes a hypothesis reachable, form and test it there (Rubber Duck); once a bottleneck is identified with a number, that number is the measurement Optimization mode needs — this skill produces the numbers those gates then require, it doesn't replace them. Not for a system that doesn't exist yet and has no live traffic (a-priori sizing) — that's `capacity-estimation`, whose 0.6–0.7 target-utilization figure this skill explains rather than re-derives. Not for deciding which signals or SLOs to instrument in the first place — that's `observability-strategy`, whose SLIs/SLOs this skill's math consumes once they exist. Not for picking a protection mechanism (rate limiting, shedding, a circuit breaker) once a pressure is identified and quantified — that's `resilience-strategy`, which this skill's utilization/queueing reading feeds.
---

# Reliability Math

Five small pieces of arithmetic separate a confident diagnosis from a fooled one: check
percentiles before trusting an average, use Little's Law to connect latency and load,
convert an SLO into real downtime minutes and a real burn rate, read a utilization number
against the queueing-collapse curve instead of by gut feel, and run a checklist against any
graph before believing what it shows. None of these are hard math. All of them are
routinely skipped, and skipping them is exactly how a dashboard reads "fine" while a
customer is stuck. This skill forces the arithmetic, every time, on the numbers actually in
front of it.

## Out of scope — hand these off

- **A system that doesn't exist yet, or has no live traffic to read** — a-priori sizing from
  stated assumptions (DAU, payload sizes, growth) → `capacity-estimation`. That skill's
  `target_utilization ~0.6–0.7` figure is exactly the headroom this skill explains the
  *mechanism* behind (queueing collapse) — don't re-derive the number, use its number.
- **Deciding what to instrument in the first place** — which signals, which SLIs, whether an
  SLO needs an error budget at all → `observability-strategy`. This skill assumes the SLI/SLO
  already exists and does the live arithmetic against it; it doesn't decide whether one
  should.
- **Picking the protection mechanism once a pressure is quantified** — rate limiting, load
  shedding, circuit breakers, bulkheads → `resilience-strategy`. This skill's utilization/
  queueing reading is that skill's input ("how close to collapse, on what signal"), not its
  output.
- **A debugging session where the user already has a hypothesis** → `problem-solving-gates`
  (Rubber Duck) runs from there directly; don't re-run this skill's math if the hypothesis is
  already formed and being tested.
- **An optimization where the user already has a profile/measurement** → `problem-solving-
  gates` (Optimization) runs from there; this skill is for *before* a profile exists, when
  the raw dashboard numbers are what's in front of you.
- **The dollar cost of the headroom or the observability stack itself** → `technical-cost-
  decision`.

---

## Rule 1 — Never accept a bare average

A single latency or response-time number with no percentile context is not evidence the
system is healthy. If only an average is offered, ask for p50/p95/p99 (or the raw
distribution) before agreeing anything is "fine." If percentiles genuinely aren't available,
say so explicitly and name the risk of concluding anything from the average alone — don't
silently proceed as if the average were sufficient.

**Why it matters:** at 1,000 req/s, a "1%" p99 gap is 10 unhappy requests *every second* —
36,000/hour. That volume is invisible in an average and is exactly who's filing the support
tickets.

## Rule 2 — Little's Law: compute, don't gesture at it

**L = λ × W** — concurrent requests in the system = arrival rate × average time per request.
Given any two, compute the third. Do the arithmetic on the user's actual numbers, not a
generic restatement of the formula.

- If λ (arrival rate) doubles and W (latency) stays flat, L (concurrency/requests-in-flight)
  doubles — that's more open connections, more memory, more threads, whether or not anyone
  asked to size for it.
- If the system is near its capacity ceiling, W does not degrade gradually as λ rises — it
  degrades sharply, because queueing time is added on top of service time (see Rule 4).
- Use it to sanity-check a claim: "we doubled traffic and latency barely moved" is either a
  real capacity win worth understanding, or a sign concurrency (L) is being silently
  absorbed somewhere with a cost not yet visible (a growing queue, a connection pool nearing
  its limit) — check which.

## Rule 3 — Error budgets are minutes, not percentages

Convert every SLO to actual allowed downtime for its stated window before reasoning about it.
`(1 − SLO) × window`. Common conversions per 30-day month:

| SLO | Allowed downtime / month |
|---|---|
| 99.9% | ~43 minutes |
| 99.95% | ~21.6 minutes |
| 99.99% | ~4.3 minutes |
| 99.999% | ~26 seconds |

**During an active incident**, compute the burn, not just the target: elapsed outage time ÷
monthly budget = % burned. If a 20-minute outage against a 99.9% SLO (43 min budget) has
burned ~47% of the month's budget, say that number — not "you're getting close." State
whether continuing the incident, or shipping a risky release on top of it, would exhaust the
budget, and what fraction is left for the rest of the window.

## Rule 4 — Read utilization against the collapse curve, not by gut feel

Queueing time does not grow proportionally with utilization — it grows non-linearly, with
the knee typically in the 80–90% range depending on variability in arrival/service times:

| Utilization | What's actually happening |
|---|---|
| ~50% | Requests flow smoothly; queues rarely form |
| ~70–80% | Small queues start forming under normal variance |
| ~85–90%+ | Even a minor burst causes wait times to spike sharply — one small spike from collapse |

"90% CPU" read as "efficient" is the exact misreading this rule exists to correct — at that
utilization the system has little to no room to absorb a burst, and the wait-time cost of the
next spike is disproportionate to its size. This is *why* `capacity-estimation` targets
0.6–0.7 utilization by default (headroom for GC pauses, bursts, and the tail) — cite that
number rather than re-deriving a different one.

## Rule 5 — Graphs lie in five specific ways; check for each

Before treating a chart as ground truth:

1. **Aggregation** — is this an average, a median, p95, p99? A flat "latency" line with no
   labeled aggregation is not informative on its own (Rule 1).
2. **Time window** — a 1-minute average smooths out spikes a 5-second window would show.
   Use the shortest window the tool offers when investigating an active incident.
3. **Axis scale** — a logarithmic Y-axis compresses large spikes into small-looking bumps.
   Confirm linear vs. log before reading magnitude off a chart by eye.
4. **Heatmap density** — a heatmap that looks calm in aggregate can still have most of its
   density concentrated at the high end. Check where the mass actually sits, not just the
   overall shade.
5. **Cross-reference** — does CPU actually track latency? Does throughput track queue depth?
   A metric that doesn't move the way the story requires is a sign the story is wrong, or the
   metric is being misread.

---

## The walk

When investigating a live symptom (a dashboard that looks fine but users are hurting, an
"is this dangerous" question about a utilization number, an active incident):

1. **Percentiles first** (Rule 1) — get p50/p95/p99, not an average. If the tail is bad while
   p50 is fine, that's a tail-latency problem, not a capacity problem yet — keep going before
   concluding which.
2. **Utilization and queueing** (Rule 4) — where does current utilization sit on the curve?
   If it's in the danger zone, that's consistent with a tail-latency symptom and points at
   Rule 2 next.
3. **Little's Law** (Rule 2) — with arrival rate and latency both available, compute
   concurrency and check it against known limits (connection pool size, worker count, thread
   pool). This is usually where the actual ceiling shows up.
4. **Error budget impact** (Rule 3) — if this is an active incident, compute the burn now, not
   after the fact. It changes what "acceptable" means for the next hour.
5. **Cross-reference and graph-check** (Rule 5) — before finalizing the read, confirm the
   supporting charts aren't themselves the source of the confusion.

Each step either produces a number or names exactly what's missing to produce one — never a
qualitative stand-in ("seems high," "probably fine") for a number that could be computed from
what's already on screen.

---

## Output block

```
Symptom / question:   <what's being investigated>
Percentiles:           p50=<x> p95=<x> p99=<x>  (or: "unavailable — only an average given,
                       treat any conclusion below as provisional")
Utilization reading:  <%>  →  <safe / forming queues / collapse-risk zone>, per Rule 4
Little's Law:          <two known values> → computed third; what it implies
Error budget:          SLO <x%> → <minutes/month allowed>; burned so far this window: <x%>;
                       remaining: <x min>  (n/a if no active incident)
Graph-check:           <any Rule-5 flags raised, or "clean">
Diagnosis:             <what the numbers actually show, stated plainly>
Handoff:               <problem-solving-gates (Rubber Duck, now that a hypothesis is
                       reachable) | problem-solving-gates (Optimization, now that a bottleneck
                       has a number) | resilience-strategy (a mechanism is needed for the
                       quantified pressure) | none — the numbers alone answered the question>
```

---

## Red flags — the analysis isn't done

- A conclusion drawn from an average with no percentile check.
- "Little's Law says..." with no actual λ/W/L numbers plugged in.
- An SLO discussed in percent only, never converted to minutes for the stated window.
- "You're close to your error budget" with no computed burn percentage.
- A utilization number called "efficient" or "fine" with no reference to the collapse curve.
- A chart's reading accepted without checking its aggregation, window, or axis scale.
- The analysis stops at naming the concept ("this looks like a tail-latency issue") without
  the arithmetic that shows it.

---

## Worked example (condensed)

> Dashboard shows average latency at 200ms. Users report checkout is stuck. System handles
> 180 req/s against a 200 req/s capacity ceiling. SLO is 99.9% availability; this incident
> has been running 20 minutes.

```
Percentiles:          p50=150ms p95=2s p99=5s → the tail is the problem, not the average
Utilization reading:  180/200 = 90% → collapse-risk zone (Rule 4) — a small burst here
                       explains a disproportionate latency spike
Little's Law:          W (p99=5s) rising while λ is flat is consistent with growing L
                       (requests piling up) — check queue depth directly to confirm
Error budget:          99.9% → 43 min/month; 20 min elapsed → ~47% of the month burned;
                       another 23 min exhausts it
Graph-check:           the "average" line was hiding the real story (Rule 1); no other
                       flags
Diagnosis:             utilization-driven queueing, not a code regression — tail latency and
                       burn rate corroborate each other
Handoff:               resilience-strategy (headroom/shedding at this ceiling) for the
                       immediate response; problem-solving-gates (Rubber Duck) if a specific
                       recent change is suspected as the trigger
```

---

## Portability

Repo-agnostic. Writes nothing; produces the output block in chat. Copy the
`reliability-math/` directory into another repo's `.claude/skills/` to use it there.
