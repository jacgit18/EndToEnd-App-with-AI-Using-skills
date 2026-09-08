---
name: deployment-strategy
description: A gated decision for how a new version of one deployable unit reaches production — the rollout mechanism (recreate / rolling / blue-green / canary / feature-flag-gated dark launch), the environment progression that actually gates a release (which pre-prod stages, who signs off), the schema- and contract-change discipline (expand/contract for backward-compatible DB and message changes so a release and its rollback both work), the health signal that aborts a rollout and the automated-rollback trigger, and the release cadence (continuous vs code-freeze windows). Use when someone says "we need zero-downtime deploys", "should we do blue-green or canary", "our deploys cause an outage", "rollbacks take too long", "releases are scary so we batch them", "how do we roll this out safely", "set up a staging pipeline", or proposes a rollout approach and wants it checked. It forces the user to state what's wrong with releases today, the deployable unit and its consumers, the downtime and rollback tolerance, and the traffic-control and environment infrastructure that exists before any mechanism is recommended, then records the outcome as an ADR. Not for moving a workload from one system to another — including swapping one API-gateway / reverse-proxy / load-balancer product for another, config-heavy and data-light though that is — that is `migration-cutover`. Not for diagnosing a single anomalous failed release — that is `problem-solving-gates` (Rubber Duck); this skill owns the problem that recurs on every release. Not for which test levels run in the pipeline — that is `test-strategy`, whose pipeline stages this skill consumes. Not for the health signal's own design — that is `observability-strategy`. Not for deciding whether a specific change is breaking or what its compatibility phase must contain — that is `change-surface-audit`, which hands this skill the confirmed expand-contract steps to stage; this skill decides how the rollout is staged and what aborts it, not whether the change needs staging in the first place.
---

# Deployment Strategy

Take one deployable unit — a service, a worker, a batch job, a frontend bundle — and decide how a new version of it gets to production without breaking what's running: whether pods are replaced in place or a second version stood up beside the first, whether all traffic moves at once or a slice at a time under a health check, how a database or message-format change is staged so both the new version and a rollback to the old one work, what signal aborts the rollout, and how often the team ships. The skill makes the user name what is actually wrong with releases today and the infrastructure they have to work with before any mechanism is on the table, recommends one, and writes an ADR.

## When to use

- The user reports a **release pain**: deploys cause a visible outage, a bad release reached all users at once, rollback took an hour, releases are so risky the team batches a month of changes into one scary push.
- The user asks for a **rollout mechanism**: "blue-green or canary", "how do we do zero-downtime", "rolling update settings", "should we put this behind a feature flag".
- The user asks about **release process**: "set up dev/staging/prod properly", "what should gate a release", "do we need a code freeze", "how do we release on Fridays safely".
- The user asks about **schema changes during deploys**: "how do we deploy a migration without downtime", "the new code needs a column the old code doesn't have".
- The user proposes a rollout plan and wants it pressure-tested ("we'll just `kubectl apply` and watch").

## Out of scope — hand these off

- **Moving a workload to a different system** — replacing the datastore, replatforming the app, relocating hosting, or swapping one API-gateway / reverse-proxy / load-balancer *product* for another (config-heavy and data-light, but still an A→B component replacement with its own cutover and rollback) → `migration-cutover`. That's a one-time transition; this skill is the repeatable version bump of a unit that already exists. (They share blue-green / canary vocabulary and both care about rollback.)
- **Diagnosing one anomalous failed release** — a single deploy that broke in a way the others didn't, with a hypothesis to chase → `problem-solving-gates` (Rubber Duck). This skill owns the *recurring* release problem (every deploy drops traffic, every other release needs a rollback); a one-off is a debugging rep, not a strategy decision.
- **Which test levels run, and at which pipeline stage** — unit / integration / contract / E2E / smoke split, non-functional scope → `test-strategy`. This skill *consumes* the list of pipeline stages that exist and decides how the rollout uses them (e.g. smoke test against the green stack before the flip); it doesn't decide the test mix.
- **The design of the health signal** the rollout watches — which SLIs, how they're measured, sampling, alerting → `observability-strategy`. This skill names that a gated rollout *needs* a health signal and what it must cover (error rate and latency on the changed paths, key business metric); it hands the signal's design there.
- **The dollar cost** of running two full production stacks for blue-green, or canary's extra capacity → `technical-cost-decision`. This skill names the cost and hands off the sizing.
- **CI build/pipeline mechanics** — runners, caching, artifact registries, the YAML. This skill decides the *strategy* (mechanism, progression, gating, cadence), not the pipeline implementation.
- **How many repos, and which repo a pipeline belongs to** — one repo vs repo-per-service vs a hybrid, and the affected-graph/path-scoped CI tooling that follows from it → `microservices-decision`. This skill assumes the repo layout is settled and decides the rollout mechanism *within* a pipeline; it doesn't decide pipeline-per-repo vs one shared pipeline.
- **Implementation** — the Argo Rollouts / Flagger / Spinnaker config, the Helm values, the migration scripts. The skill stops at the ADR.

---

## The gate

Before recommending any rollout mechanism, environment progression, or cadence, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **The deployable unit(s)** — what ships as one release: language/runtime, packaged as (container / function / static bundle / VM image), where it runs (Kubernetes / ECS / serverless / VMs / a CDN).
2. **Current deploy method** — how a release goes out today (CI job, `kubectl apply`, a script, a platform's built-in deploy), and whether it currently causes downtime.
3. **Existing environments and traffic control** — the pre-prod environments that exist, and what can shift production traffic (an ingress / load balancer, a service mesh, a CDN, a feature-flag service, none).

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

4. **The pressure** — the concrete release problem, not a wish. One of: measured downtime per deploy, a specific incident where a bad release hit all users before anyone noticed, a rollback that took too long (how long, why), or a batching problem (releases so risky they're bundled, making each one bigger and riskier). "We should do canary", "best practice", "the new platform supports blue-green" is **not** a pressure — it is a reason to stop.
5. **The unit and its consumers** — what the release affects: is it a user-facing synchronous service, a background worker, a scheduled batch job, a shared library, a frontend. Who or what depends on it being available, and do they retry on failure or surface it to a user immediately.
6. **Downtime tolerance per release and traffic shape** — can this unit take a brief drop on deploy (seconds, none), is production traffic steady or spiky (deploying into a spike is different), are there session-affinity or long-lived-connection concerns (WebSockets, streaming, in-flight jobs).
7. **Rollback needs** — how fast a bad release must be reversible (a number), and whether some changes are legitimately forward-only (a data migration that's already transformed rows) — those need the expand/contract treatment, not a rollback plan.
8. **State and contract coupling** — does the unit hold local state (in-memory sessions, a local queue, leader election); does this class of release change a database schema, a message/event format, or an API contract that other units consume — and are those consumers deployed independently.
9. **Infrastructure for progressive delivery** — can two versions of the unit run at once (spare capacity, and the cost of it); can traffic be split by percentage or by rule (mesh, weighted LB, flag service); is there a metrics source a rollout controller can query to auto-gate. If none of this exists, the realistic options narrow to recreate / rolling.
10. **Environments that actually gate, and who signs off** — which pre-prod stages have production-like data and traffic (a "staging" nobody trusts doesn't gate anything), what must be true to promote from each, and who or what approves (automated checks, a person, a change-approval board).
11. **Release cadence and operational capacity** — how often the team wants to ship (per-commit, daily, weekly, per-sprint), who watches a rollout while it progresses, who is on call, and whether releases are currently blocked on a manual step that won't scale.

"Our deploys cause downtime, set up blue-green" with items 4–11 absent is not valid input.

**Pressure does not open the gate.** "We go live in two weeks", "the VP wants canary", "just tell me the rolling-update settings" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–11 in one sentence each, because a progressive-delivery setup with no health signal to gate on (item 9) is just a slower way to ship the same bad release.

---

## Challenge a proposed approach

If the user opens with the mechanism already chosen, put their reasoning under the gate, then test the specific claim against `rollout-patterns.md`:

- **"blue-green"** — can you afford a second full production stack (item 9), for how long? What happens to in-flight requests and non-drained connections at the flip (item 6)? Crucially: how do database and message-format changes work when both stacks might be live and you might flip *back* — do they already follow expand/contract (item 8)? Blue-green makes the app instant to roll back and does nothing for a schema change that isn't backward-compatible.
- **"canary"** — what metric decides the canary is healthy, measured where, over what window (item 9)? At your traffic volume, does a 5% canary get enough requests to show a regression before promotion? Who or what promotes/aborts — automated analysis or a human watching a dashboard? Canary without an automated, quantitative gate is just a slow manual rollout.
- **"feature flags for everything"** — flags decouple *release* from *deploy*, which is powerful, but every flag is a branch in production that must be tested both ways and later removed. Which changes genuinely need runtime toggling (risky, needs gradual exposure, needs instant off) vs which are fine with a normal rollout? What's the flag-cleanup discipline?
- **"rolling update, it's the default"** — often right. But rolling runs old and new versions simultaneously for the duration — is that safe for this unit (item 8: shared schema, message formats)? What are the readiness/liveness probes, and does "ready" actually mean "serving correctly" or just "process up"? What's `maxUnavailable` / `maxSurge` against your capacity headroom?
- **"we'll deploy the migration with the code"** — if the new schema isn't readable by the old code, a rollback of the code now fails against the migrated database. Split it: expand (add the column/table, backward-compatible) → deploy code that writes both → backfill → deploy code that reads new → contract (drop the old) — each step independently rollback-safe. See `rollout-patterns.md`.
- **"just push to prod on green CI, no staging"** — sometimes correct (strong tests, fast rollback, low blast radius). Does your rollback meet item 7 without a staging catch? What's the smoke check immediately post-deploy, and does it run before real users hit the new version?

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `deployment-framework.md` in order once the gate is satisfied. In short: confirm the pressure is a real release problem → classify the unit (stateless service / stateful / worker / batch / frontend) because it bounds the mechanisms → check what progressive-delivery infrastructure actually exists → pick the rollout mechanism from downtime tolerance, blast-radius need, and that infrastructure → define the health signal the rollout gates on (hand its design to `observability-strategy`) and the auto-rollback trigger → apply expand/contract to any schema or contract change so every step is rollback-safe → set the environment progression and the promotion criteria that actually gate → set the cadence → recommend and record.

Reference files:

- `rollout-patterns.md` — the mechanisms (recreate, rolling, blue-green, canary, feature-flag / dark launch): what each does to downtime, blast radius, rollback speed, cost, and infra requirement, plus the failure mode of each. Expand/contract (parallel-change) for backward-compatible schema and message evolution, step by step. Environment-progression patterns and what makes a stage actually gate. Automated rollback and the signals worth gating on.
- `deployment-framework.md` — the 8-step process, worked once the gate is satisfied.

---

## Output

**1. In chat, a recommendation block:**

```
Pressure:            <the measured downtime / blast-radius incident / slow rollback / batching problem from gate item 4>
Unit:                <what ships, and its class: stateless service | stateful | worker | batch | frontend>
Rollout mechanism:   <recreate | rolling (maxSurge/maxUnavailable) | blue-green | canary (steps + %) | flag-gated> — <why, from downtime tolerance + blast-radius need + infra>
Health signal:       <what the rollout watches — error rate + latency on changed paths, key business metric — measured where; design → observability-strategy>
Auto-rollback:       <the trigger condition and who/what executes it>
Schema/contract changes: <expand/contract required? the ordered steps> — or "n/a, no shared schema/contract in this release class"
Environment progression: <the stages that actually gate, and the promotion criterion for each>
Sign-off:            <automated checks | named role | change board> at <which gate>
Cadence:             <per-commit | daily | weekly | per-sprint> ; who watches a rollout
Tradeoffs accepted:  <2–4 concrete costs: double capacity for blue-green, canary bake time, flag debt, rolling's mixed-version window>
Not chosen because:  <one line per rejected mechanism>
Cost follow-up:      <hand to technical-cost-decision: second-stack capacity, canary overhead, flag-service tier>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). Reference any related `test-strategy` (pipeline stages), `observability-strategy` (health signal), or `migration-cutover` ADR. Fill "Revisit when" with the concrete trigger that reopens this — "deploy frequency crosses N/day and manual promotion becomes the bottleneck", "traffic grows to where a 5% canary is statistically meaningful and we can tighten the gate", "a rollback incident shows the health signal missed a regression class", "the second blue stack's cost crosses $X/mo".

Then stop. Implementation — the rollout-controller config, the probes, the migration scripts, the flag wiring — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the release problem measured, the unit classified, the infrastructure known, a mechanism chosen against a real health signal, and schema changes already following expand/contract — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Node API on EKS, ~40 pods behind an ALB, Istio is in the mesh. Right now CI runs `kubectl set image` and we get ~20s of 503s per deploy while pods cycle, and twice this quarter a bad release errored for all users for 10+ minutes before someone rolled it forward. Rollback today is 're-run the old pipeline', ~8 minutes. Deploys ~5×/day. Traffic is steady on weekdays. Some releases touch the Postgres schema; the schema is shared only by this API. We have Prometheus + Grafana and an SLO on API error rate. Two engineers rotate the deploy watch."

Gate satisfied. Framework: stateless service, mesh present, metrics present → **canary via Istio weighted routing**, steps 5% → 25% → 50% → 100% with a 5-minute bake at each, automated analysis on API error rate and p95 latency against the SLO (Flagger or Argo Rollouts driving it). Auto-rollback: analysis failure at any step reverts weight to 0 — seconds, not 8 minutes. Readiness probe changed to a real dependency check so the 503 gap closes (rolling under the hood still needs correct probes). Schema: adopt expand/contract for the shared-schema releases — add-only migration, deploy, backfill, switch reads, drop later — each step rollback-safe even mid-canary. Environments: keep the existing staging smoke gate; the canary *is* the production gate. Cadence unchanged at 5×/day, now unattended-safe. Tradeoffs: ~5% extra capacity during a canary, ~20 min added wall-clock per release, expand/contract discipline on schema PRs. Not blue-green: 40 pods × 2 is real cost for a change canary handles with 5% overhead; not recreate/rolling-only: doesn't fix the blast-radius incident. → `observability-strategy` to confirm the analysis metrics; → `technical-cost-decision` if canary capacity matters. ADR; Revisit when a rollback shows the gate missed a regression class, or traffic/volume lets us tighten steps.

> "We want zero-downtime deployments. Let's do blue-green."

Gate not satisfied — item 4 (no measured pressure — is there downtime today, and how much?), item 8 (does a release change shared schema/contracts? blue-green doesn't fix that), item 9 (can you run two stacks — capacity and cost?). Response: name what's missing, note that blue-green makes the *app* instantly reversible but does nothing for a non-backward-compatible schema change and needs double capacity, and ask for the current downtime measurement, whether releases touch shared schema, and the spare-capacity picture. Do not recommend a mechanism.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Copy the `deployment-strategy/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.
