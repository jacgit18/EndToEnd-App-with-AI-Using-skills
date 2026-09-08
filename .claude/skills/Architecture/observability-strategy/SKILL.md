---
name: observability-strategy
description: A gated decision for how a service or system is made observable — which signals to invest in (metrics, structured logs, distributed traces, continuous profiling, events), the SLIs that define "working" and whether to set SLOs with an error budget, the instrumentation approach (OpenTelemetry SDK / auto-instrumentation / vendor agent and the collector topology), the sampling strategy (head vs tail, rate) and the cardinality budget for metric labels and log fields, the alerting policy (symptom / SLO-burn paging vs cause-based tickets), retention tiers per signal, and self-hosted vs managed placement. Use when someone says "we need monitoring / observability", "add Datadog / Grafana / Honeycomb", "we should have dashboards", "set up distributed tracing", "what should we alert on", "our logs are useless in an incident", "we can't tell why prod is slow", "incidents take hours to diagnose", "we're committing to an SLA", or proposes an observability approach and wants it checked. It forces the user to state the triggering pressure, the user-facing SLIs, the architecture shape and request volume, and the operational capacity before any signal, tool, or alert is recommended, then records the outcome as an ADR. Not for the dollar sizing of an observability vendor or self-hosted stack (per-host / per-GB / per-span / per-active-series pricing) — that is `technical-cost-decision`. Not for diagnosing one specific slow endpoint right now — that is `problem-solving-gates` (Rubber Duck for a bug, Optimization for a measured-slow path). Not for whether to split services — that is `microservices-decision` (this skill consumes that shape). Not for what to shed or how to degrade under overload, or the rate-limit / circuit-breaker / bulkhead design — that is `resilience-strategy`, which consumes the SLIs this skill defines. Not for the health signal a progressive rollout gates on beyond defining the SLIs — the rollout mechanism is `deployment-strategy`. Not for security/audit logging as a compliance control — name it and defer.
---

# Observability Strategy

Take a service or system that is hard to see into — an incident took hours to diagnose, nobody can say what "healthy" looks like, a slowdown has no explanation, or an SLA is about to be signed — and decide how it gets instrumented: which signals earn their cost, what defines "working" from the user's side, how traces and logs are sampled and bounded, what pages a human versus what files a ticket, how long each signal is kept, and whether the backend is self-hosted or managed. The skill makes the user name the concrete blind spot and the user-facing SLIs before any signal or tool is on the table — because observability is a permanent cost stream (instrumentation overhead, storage, a bill, and alert-attention) traded for faster diagnosis — recommends one design, and writes an ADR.

## When to use

- The user reports a **diagnosis blind spot** — "we couldn't tell what caused the outage", "no idea which service is slow", "the logs don't answer the question", "we found out from a customer".
- The user asks to **add observability tooling**: "set up Datadog / New Relic / Grafana / Honeycomb", "add Prometheus", "we need distributed tracing", "stand up dashboards".
- The user is **introducing an SLA/SLO commitment** and needs to measure against it.
- The user asks an **alerting question**: "what should we alert on", "we get paged too much", "how do we know if it's actually down".
- The user reports an **observability defect**: log bill blew up, metric cardinality explosion, traces sampled so hard the interesting ones are gone, dashboards nobody opens during an incident.
- The user proposes an approach and wants it pressure-tested ("we'll log everything and grep it", "100% trace sampling", "alert on every error").

## Out of scope — hand these off

- **The dollar cost** of the observability backend — vendor per-host / per-GB-ingested / per-million-spans / per-active-time-series pricing, self-hosted storage and compute, egress → `technical-cost-decision`. This skill names that the design has a recurring price and hands off the line items; it decides *what* to collect, not what the invoice is.
- **Diagnosing one specific problem right now** — a bug with a hypothesis → `problem-solving-gates` (Rubber Duck); a path that is measured-slow and needs to be faster → `problem-solving-gates` (Optimization). This skill decides what instrumentation should exist so those investigations are possible; it does not run them.
- **Enumerating the failure surface you don't yet have** — "we keep getting blindsided by failures nobody anticipated", a design or pipeline with no failure-mode list → `failure-mode-analysis` first. This skill consumes that register's impact ranking and detection-gap rows to design the alerting; it does not run the nine-category walk itself.
- **Whether to split into services / where boundaries go** → `microservices-decision`. This skill consumes the architecture shape (how many hops a request makes) to decide whether tracing earns its keep; it does not decide the shape.
- **What the system does under overload or dependency failure** — load shedding and its priority tiers, rate limiting, circuit breakers, retry budgets, bulkheads, graceful degradation → `resilience-strategy`. This skill defines the SLIs that say "critical traffic is healthy" and alerts on them (including on shedding that fires when it shouldn't); that skill decides the mechanisms that keep those SLIs green.
- **The rollout mechanism a canary/blue-green release gates on** → `deployment-strategy`. This skill defines the SLIs and the health signal; that skill decides recreate/rolling/blue-green/canary and wires the auto-rollback to the signal.
- **Incident-response process, on-call rotation design, postmortem culture** — organizational, not instrumentation. Name that they matter and stop.
- **Security monitoring, SIEM, audit logging as a compliance control** — a future `security-architecture` concern. PII-in-logs and audit-retention constraints are *inputs* to this skill (gate item 8); designing the audit trail is not.
- **Implementation** — writing the spans, the dashboards, the alert rules, the collector config. The skill stops at the ADR.

---

## The gate

Before recommending any signal, tool, sampling rate, or alert, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **The service(s) in question** and their runtime — language, framework, where they run (VMs / containers / serverless / a mix).
2. **Existing instrumentation** — what already emits logs, metrics, or traces; log format (structured or text); any APM agent, Prometheus scrape, or OTel setup already present.
3. **The current backend** — where logs/metrics go today (a vendor, an ELK/Loki stack, CloudWatch, nothing), and what dashboards or alerts exist.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

4. **The pressure** — the concrete triggering event, not a wish. One of: a specific incident whose diagnosis was too slow (what happened, how long to root-cause, what was missing), a named blind spot (a question about production you currently cannot answer), an SLA/SLO being introduced (with the target), or an existing observability cost or alert-fatigue problem. "We should have monitoring", "best practice", "the board wants dashboards" is **not** a pressure — it is a reason to stop.
5. **User-facing SLIs** — for each thing a user (or calling system) depends on: what does "working" mean in measurable terms — the latency of *which* operations, the error rate on *which* paths, availability, freshness/lag? If this is an internal batch job with no interactive user, say so — the SLI is then completion time and success, not p99 latency.
6. **SLO or no SLO** — is there a real commitment (an SLA with a customer, an internal target with consequences) that needs an objective and an error budget, or is this "we just want to see what's happening"? Don't set SLOs where nothing depends on them.
7. **Architecture shape and request path** — monolith / a few services / many services / serverless / event-driven; synchronous request/response or async via queues; how many network hops and async handoffs a *typical* user request crosses. This decides whether distributed tracing earns its instrumentation and storage cost or a request-ID in structured logs is enough.
8. **Volume and cardinality** — request rate (peak RPS), and the rough size of the high-cardinality dimensions: distinct users / tenants / endpoints / device IDs that might end up as labels or fields. This bounds sampling and the metric-label budget before a cardinality explosion happens in production.
9. **Retention and compliance constraints** — how far back do incident investigations and any audit or regulatory requirement actually need to look, per signal; is there PII that must not land in logs/traces, or data-residency limits on where telemetry may be stored.
10. **Operational capacity and on-call** — who instruments the code, who owns the dashboards and alert rules, who is paged, and what the incident cadence is now. A managed backend and a self-hosted one need very different amounts of this.

"We need observability, set up Grafana" with items 4–10 absent is not valid input.

**Pressure does not open the gate.** "We go live in two weeks", "the SRE role starts next month", "just tell me which tool" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–10 in one sentence each, because instrumentation retrofitted after an incident, with no SLI defined and no cardinality budget, becomes the next incident's bill.

---

## Challenge a proposed approach

If the user opens with the approach already chosen, put their reasoning under the gate, then test the specific claim against `signals-and-slos.md`:

- **"add Datadog / add observability"** — which blind spot (item 4), measured how? What is the SLI (item 5)? Is the problem "no data" or "lots of data and no answers"? A tool purchase does not define what "working" means.
- **"we need distributed tracing"** — how many service hops and async handoffs does a real request cross (item 7)? A monolith with two DB calls does not need tracing infrastructure; a request-ID propagated into structured logs answers the same questions. Tracing earns its keep at roughly 3+ services, or heavy queue-based async, or a fan-out.
- **"log everything and grep it"** — log volume is both a bill and a haystack. What questions must the logs answer (item 4)? Structured events with a few deliberate fields beat verbose free text; "everything" means the one line you need is buried and expensive.
- **"100% trace sampling"** — at what RPS (item 8), and what is the storage cost? Tail-based sampling keeps the *interesting* traces (errors, slow outliers, specific routes) at a fraction of the volume; head sampling at a low rate keeps a representative baseline. 100% is rarely the right default above trivial volume.
- **"alert on every error" / "alert on high CPU"** — that is cause-based alerting and it produces fatigue. Page on *symptoms* the user feels — SLO burn rate, elevated error rate on a critical path, availability — and route cause signals (CPU, memory, queue depth) to dashboards and tickets. What is the actual paging criterion (item 5, 6)?
- **"a dashboard for every service"** — which decision does each dashboard support during an incident? A dashboard nobody opens at 3am is maintenance cost, not observability. Start from the SLIs and the top failure modes (from a `failure-mode-analysis` register if one exists).
- **"OpenTelemetry everywhere, now"** — a good vendor-neutral default, but auto-instrumentation has coverage gaps, and someone has to own the collector, the semantic conventions, and the pipeline. Is the team (item 10) ready for that, or is a managed agent the right first step with OTel as the migration target?
- **"metrics are enough"** — metrics tell you *that* something is wrong and *which* SLI moved; they rarely tell you *why*. Without exemplars or correlated traces/logs, every alert becomes a from-scratch investigation. What connects a bad metric to the request that caused it?

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `observability-framework.md` in order once the gate is satisfied. In short: confirm the pressure is real and name the exact questions production currently can't answer → define SLIs from the user's perspective (RED for request-driven work, USE for resources, completion+success for batch) and set SLOs + error budget only where a real commitment exists → choose signal investment against the architecture shape (metrics and structured logs always; distributed tracing when the request path crosses enough hops; continuous profiling only for CPU/memory-bound hot paths; events for audit-like needs) → pick the instrumentation approach (OTel SDK + auto-instrumentation as the default, manual spans where they add value, collector topology) → set the sampling strategy and a cardinality budget (metric-label allow-list, log-field discipline, head vs tail trace sampling from the volume) → set the alerting policy (symptom/SLO-burn → page; cause → dashboard/ticket; every alert links a runbook) → set retention tiers per signal from how far back investigations and audits actually look → choose self-hosted vs managed from operational capacity and residency, and hand the dollar comparison to `technical-cost-decision` → name the metrics of the observability system itself and the revisit trigger → recommend and record.

Reference files:

- `signals-and-slos.md` — the signal types (metrics, structured logs, distributed traces, continuous profiling, events): what each answers, what each costs to produce and store, and its failure mode when over- or under-used. The method cheat-sheets (RED, USE, the Four Golden Signals). SLI / SLO / error-budget in brief, and symptom-vs-cause alerting. Sampling: head vs tail and the trade. Cardinality as the hidden cost driver and how to budget it. Self-hosted component stack (OTel Collector, Prometheus, Grafana, Loki, Tempo, Jaeger) vs managed platforms — what each choice asks of the team.

---

## Output

**1. In chat, a recommendation block:**

```
Pressure:            <the incident / blind spot / SLA / cost problem from gate item 4, concretely>
Questions to answer: <the specific production questions this design must make answerable>
SLIs:                <per user-facing operation: the metric and where it's measured>
SLOs:                <objective + error budget where a real commitment exists — or "none, observation only">
Signals invested in: metrics <always> | structured logs <always> | traces <yes/no — why, from hop count> | profiling <yes/no> | events <yes/no>
Instrumentation:     <OTel SDK + auto-instrumentation | vendor agent | manual> ; collector: <topology or "n/a">
Sampling:            traces <head @ rate | tail on error+slow+routes | none> ; logs <level policy> — <why, from volume>
Cardinality budget:  metric labels <allow-list>; log fields <disciplined set>; the dimensions deliberately kept OUT
Alerting:            page on <symptom / SLO burn conditions> ; ticket/dashboard for <cause signals> ; every alert → runbook
Retention:           metrics <e.g. 15mo downsampled> | logs <e.g. 30d hot, 1y cold> | traces <e.g. 7d> — from investigation + audit lookback
Placement:           <self-hosted stack (components) | managed (which class)> — <why, from operational capacity + residency>
Tradeoffs accepted:  <2–4 concrete costs: instrumentation overhead, storage/bill class, alert-attention budget, a stack to run>
Not chosen because:  <one line per rejected signal / tool / sampling choice>
Cost follow-up:      <hand to technical-cost-decision: ingest GB/day, active series, spans/day, host count, retention tiers>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). Reference any related `microservices-decision` or `technical-cost-decision` ADR. Fill "Revisit when" with the concrete trigger that reopens this — "a third service enters the critical request path" (tracing crosses its threshold), "the log bill crosses $X/mo" (revisit sampling and retention), "an SLO is introduced for this service", "alert-to-incident ratio exceeds N:1" (paging policy is too noisy), "request volume 10×'s" (re-budget cardinality and sampling).

Then stop. Implementation — the spans, dashboards, alert rules, collector config — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the blind spot named and measured, SLIs defined from the user's side, signal investment chosen against the real architecture, a sampling and cardinality plan, a symptom-based paging policy — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Payments service, Go, on ECS. Last month a downstream timeout cascaded and it took us ~3 hours to work out which dependency was the cause — our logs are unstructured text and we had no view across service boundaries. The service calls 4 internal services and Stripe; a typical charge crosses all of them. ~60 rps peak, ~200k distinct merchants. We're on CloudWatch Logs only, no metrics or traces. Two engineers own it, we're on PagerDuty, ~1 real incident a month. We have a 99.9% availability SLA with our biggest customer starting next quarter. PII (card metadata) must never hit logs; telemetry has to stay in-region."

Gate satisfied. Framework: SLIs = charge-success rate and charge p95/p99 latency measured at the service edge; SLO = 99.9% availability with a monthly error budget (real commitment). Signals: metrics (RED on the charge path, per-dependency call success/latency) + structured JSON logs with a trace/request ID and a strict field allow-list (no card data) + **distributed tracing** — 5 hops on every charge is exactly where tracing earns its cost. Instrumentation: OTel Go SDK, auto-instrumentation for the HTTP/gRPC clients plus manual spans around the Stripe call; a collector sidecar per task. Sampling: tail-based — keep every errored or >1s trace, 5% of the rest (60 rps makes 100% affordable but not useful). Cardinality: `merchant_id` stays OUT of metric labels (200k series per metric) — it lives on spans and logs where it's queryable; labels limited to route, dependency, status class. Alerting: page on SLO burn rate and on charge-error-rate spike; dependency CPU/latency → dashboard. Retention: metrics 15mo downsampled, logs 30d hot / 1y cold (chargeback window), traces 7d. Placement: managed, in-region (small team, can't run Tempo/Loki HA for a payments SLA) — hand instance/ingest sizing to `technical-cost-decision`. ADR; Revisit when a 6th hop enters the path, the SLA target tightens, or ingest crosses the budgeted GB/day.

> "We should set up observability before the launch. Thinking Grafana."

Gate not satisfied — item 4 (no incident, blind spot, or SLA named; "before launch" is a schedule, not a pressure), item 5 (no SLI), item 7 (architecture shape not given). Response: name what's missing, note that observability is a permanent cost stream and the first move is to name the specific production questions it must answer and what "working" means to a user, and ask for a measured blind spot or an SLA plus the request-path shape. Do not recommend a signal set or a tool.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Copy the `observability-strategy/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.
