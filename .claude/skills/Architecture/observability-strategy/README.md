# observability-strategy skill

A gated decision for **how a service or system is made observable** — which signals to
invest in, the SLIs that define "working" and whether to set SLOs, the instrumentation
approach, the sampling and cardinality budget, the alerting policy, retention per signal,
and self-hosted vs managed. Not the dollar cost of the backend, and not the instrumentation
code itself. Given a diagnosis blind spot (or an incoming SLA), the skill makes the user
name the concrete unanswerable question and the user-facing SLIs before any signal or tool
is on the table, then writes an ADR.

Built from the `Architecture/` notes — `Monitoring & Observability.md` (monitoring vs
observability; the logs/metrics/traces pillars), `Distributed Tracking & Monitoring.md`,
`OpenTelemetry.md`, `12 Key Metrics for Measuring Service Performance.md` (latency, error
rate, throughput, MTBF, MTTR), `Fault Tolerance.md`, `Chaos Engineering.md`.

## Where it sits

```
microservices-decision   →  how many services, where the boundaries are
observability-strategy    →  how the resulting system is instrumented and alerted   (this skill)  → ADR
technical-cost-decision   →  the dollar sizing of the telemetry backend
problem-solving-gates     →  Rubber Duck / Optimization — using the instrumentation to diagnose one problem
```

`observability-strategy` **consumes** the architecture shape from `microservices-decision`
(hop count decides whether tracing earns its cost) and **hands off** the bill to
`technical-cost-decision`. It decides *what to collect and alert on*; the other two decide
*how many services there are* and *what the invoice is*.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The 7-item gate (items 4–10 from the user), challenge-the-framing, output contract. |
| `observability-framework.md` | The 10-step process — pressure → SLIs/SLOs → signal investment → instrumentation → sampling/cardinality → alerting → retention → placement. |
| `signals-and-slos.md` | Each signal type (metrics, logs, traces, profiling, events) — what it answers, costs, failure mode. RED/USE/Golden-Signals. The service-metric menu (TTFB, latency, response time, throughput, request rate, error rate, concurrent connections, cache hit ratio, MTBF/MTTR, SLA compliance) as candidate SLIs. SLI/SLO/error-budget. Symptom-vs-cause alerting. Head-vs-tail sampling. Cardinality budgeting. Self-hosted stack vs managed. |

## What it produces

1. A recommendation block in chat (pressure, questions to answer, SLIs, SLOs, signals,
   instrumentation, sampling, cardinality budget, alerting policy, retention tiers,
   placement, accepted tradeoffs, cost follow-up).
2. An ADR at `docs/architecture/decisions/NNN-<slug>.md` (reuses `database-architecture`'s
   `adr-template.md`), with a concrete "Revisit when" trigger.

Stops before the spans, dashboards, alert rules, and collector config.

## Deliberately out of scope

- Dollar sizing of the observability backend (per-host / per-GB / per-span / per-series
  pricing, self-hosted infra) → `technical-cost-decision`.
- Diagnosing one specific problem now → `problem-solving-gates` (Rubber Duck for a bug,
  Optimization for a measured-slow path). This skill makes those investigations *possible*.
- Whether to split services / where boundaries go → `microservices-decision`.
- Incident-response process, on-call rotation, postmortem culture — organizational.
- Security monitoring / SIEM / audit logging as a compliance control → future
  `security-architecture`. PII-in-logs and audit retention are *inputs* here, not the design.
- Implementation of any kind.

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/`.

```
cp -r ".claude/skills/Architecture/observability-strategy" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `problem-solving-gates` (Rubber Duck / Optimization)** — that skill diagnoses one
  problem with a hypothesis or a measurement; this skill decides what instrumentation
  should exist. "Why is this endpoint slow" → problem-solving-gates. "We can't tell why
  anything is slow" → here.
- **vs `technical-cost-decision`** — anything about the telemetry bill, ingest volume
  pricing, or managed-vs-self-hosted *on cost grounds* hands off; this skill picks the
  signal set and notes the cost follow-up.
- **vs `microservices-decision`** — this skill takes the service count / request-path shape
  as a given input; it does not decide it.
- **vs `caching-strategy` / `data-tier-operations`** — those may produce metrics worth
  watching (hit rate, replica lag); this skill decides how those get collected and alerted,
  it doesn't design the cache or the replica topology.
