# Deployment Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR.

## 1. Confirm the pressure is a real release problem

Restate gate item 4 as one sentence. Then judge it:

- **Measured downtime per deploy** (N seconds of errors, a drop in throughput while instances cycle) → proceed.
- **A blast-radius incident** (a bad release served errors to everyone before it was caught) → proceed; the fix is a gated rollout, not just faster rollback.
- **Slow rollback** (a number, and why — re-run a pipeline, rebuild an image, restore a DB) → proceed.
- **Batching** (releases are risky, so changes pile up into large infrequent pushes, making each one riskier — the doom loop) → proceed; the fix is making a single small release safe and boring.
- **"Best practice", "the platform supports it", "the VP asked for canary", "before launch"** → stop. State that every rollout mechanism has a cost (capacity, wall-clock, operational surface, flag debt) and the first move is to name what actually goes wrong on a release today.

If item 9 (progressive-delivery infrastructure) is unknown, the deliverable is "find out what can split traffic and what metrics a controller can read", not a mechanism.

## 2. Classify the deployable unit

The unit's nature bounds which mechanisms are even available:

- **Stateless synchronous service** — the easy case. All mechanisms available. Rollout quality depends on correct readiness probes and connection draining.
- **Stateful service** (in-memory sessions, local queues, leader election, sticky connections) — blue-green and canary need session handling (drain, or externalise state first). Rolling needs `maxUnavailable: 0` and graceful shutdown. Sometimes the real fix is to externalise the state before touching the deploy mechanism.
- **Background worker / queue consumer** — no user-facing downtime, but watch for: two versions processing the same queue with different logic, poison messages from a bad release, in-flight message loss on shutdown. Canary = run a few new-version workers on the same queue and compare outcomes.
- **Scheduled batch job** — "rollout" means: which run picks up the new version, is a half-migrated state safe, can a bad run be re-run. Usually recreate; the care is in idempotency and the schema step.
- **Frontend bundle / static assets** — served from a CDN. Concerns: cache invalidation, users mid-session on the old bundle calling a new API (or vice versa — this is a contract-coupling problem, item 8), atomic asset swaps. Canary = percentage-based asset serving or a flag.

Record the class and the constraint it imposes.

## 3. Inventory the progressive-delivery infrastructure

From gate item 9. Be concrete about what exists *today*:

- **Can two versions run at once?** Spare capacity for a second full stack (blue-green) or +N% (canary)? What does that cost (→ `technical-cost-decision`)?
- **Can traffic be split?** By percentage (mesh, weighted target groups, CDN), by rule (header, user attribute — needed for internal-users-first canary), or not at all (then: recreate / rolling only, or introduce a flag service).
- **Is there a queryable health signal?** A metrics store (Prometheus, Datadog, CloudWatch) a rollout controller can read to auto-gate. Without it, "canary" degrades to a human watching a dashboard — possible, but not unattended, and doesn't scale with cadence.
- **Is there a feature-flag service?** (LaunchDarkly, Unleash, Flagsmith, a homegrown table.) Enables release-decoupled-from-deploy.

Record what's present. The mechanism choice in step 4 cannot exceed this inventory without a prerequisite project.

## 4. Pick the rollout mechanism

From gate items 6 (downtime tolerance), 4/5 (blast-radius need), and step 3 (infra). `rollout-patterns.md` has the full comparison table.

- **Recreate** (stop all old, start all new) — only acceptable when a downtime window is genuinely fine (internal tool, batch job, maintenance-window culture). Simplest. Don't reach for anything fancier if this honestly fits.
- **Rolling** (replace instances in batches) — the default for stateless services with no downtime budget and no traffic-splitting infra. Old and new run together during the roll — safe only if the release is backward-compatible with itself (step 6). Tune `maxSurge` / `maxUnavailable` to capacity. Needs real readiness probes.
- **Blue-green** (full second stack, flip all traffic, keep old warm) — instant rollback of the *application*, near-zero downtime, at the cost of double capacity for the overlap. Does **nothing** for schema changes that aren't backward-compatible — those still need step 6. Best when rollback speed is the pressure and capacity is available.
- **Canary** (route a small % to the new version, watch, promote in steps, auto-abort on regression) — the strongest answer to a blast-radius pressure. Requires traffic-splitting *and* a queryable health signal for the automated gate. Needs enough traffic that the canary slice shows a regression quickly. Adds wall-clock per release (bake time).
- **Feature-flag / dark launch** (deploy dormant code, enable at runtime for a growing cohort, instant kill-switch) — decouples release from deploy. Best for individually risky changes that need gradual exposure or instant-off independent of a deploy. Cost: every flag is a tested-both-ways branch in prod with a cleanup obligation.

Mechanisms combine: rolling deploy + feature flags for risky changes is a common, sane default before investing in canary infra.

Record the mechanism, its parameters (surge/unavailable, canary steps and %, bake time), and why the rejected ones lost.

## 5. Define the health signal and the auto-rollback trigger

A gated rollout (blue-green with a bake, canary, flag ramp) is only as good as the signal it watches.

- **What it must cover:** error rate and latency (p95/p99) on the paths this release *changes*, not just global averages — a regression in one endpoint hides in an aggregate. Plus at least one business metric (checkout rate, signups, key event volume) — some regressions are "works, but wrong".
- **Where it's measured:** server-side at the unit's edge, and ideally client-side / synthetic for user-facing units.
- **The window and threshold:** how long to observe per step, and what delta counts as a failure (absolute, or relative to the baseline / the non-canary population).
- **Hand the signal's design to `observability-strategy`** — SLI definition, measurement, sampling, cardinality. This step names *what the rollout needs from it*.
- **The trigger:** the exact condition that aborts (analysis fails at step N) and what executes the revert (the controller drops canary weight to 0 / flips blue-green back / disables the flag) and how fast.

Record the signal contents, the per-step window/threshold, and the abort mechanism.

## 6. Apply expand/contract to schema and contract changes

From gate item 8. If this release class changes a DB schema, a message/event format, or an API contract consumed by an independently-deployed unit, a naive "ship the migration with the code" breaks rollback: once rows are migrated, the old code can't read them. Stage it as **parallel change** (expand/contract) — `rollout-patterns.md` has the worked steps:

1. **Expand** — add the new column / table / optional field / new event version. Backward-compatible; old code ignores it. Independently deployable and rollback-safe.
2. **Migrate reads/writes** — deploy code that writes both old and new (or reads new, falling back to old). Still rollback-safe: the old shape is still populated.
3. **Backfill** — populate the new shape for historical rows. A data job, not a deploy; idempotent and re-runnable.
4. **Switch** — deploy code that reads only the new shape. Rollback here returns to step 2's dual code, which still works.
5. **Contract** — after a soak, drop the old column / stop writing the old event version. Only now is the old shape gone — and by now no running or rollback-target code needs it.

Each step is a separate release. The rollout mechanism from step 4 applies to each. This is what makes "zero-downtime migration" real rather than aspirational.

Record: whether expand/contract applies to this release class, and the ordered steps if so.

## 7. Set the environment progression and promotion criteria

From gate item 10. List only the stages that *actually gate* — a stage that everyone bypasses under pressure, or whose data is nothing like production, gates nothing and should be fixed or dropped.

For each real stage, write the **promotion criterion**: the concrete condition to move to the next stage (all pipeline tests green — from `test-strategy`; a manual exploratory pass by QA; a product sign-off; a soak with no error-budget burn; a change-board approval for regulated changes). Name who or what applies it.

Common shapes:

- **CI → staging → prod**, staging with production-like data, auto-promote on green + smoke, human gate on prod for high-risk changes.
- **CI → prod (canary)** — no staging; the canary in production *is* the gate. Viable with strong tests and fast auto-rollback; state that explicitly as the trade.
- **CI → staging → prod-canary → prod-full** — belt and braces for high-blast-radius units.

Record the stage list, each promotion criterion, and the sign-off owner per gate.

## 8. Set cadence and recommend

From gate item 11. State the target release frequency and confirm the chosen mechanism + progression supports it unattended or with the available watch capacity. If a manual step (a person clicking promote, a weekly change board) is the bottleneck against the desired cadence, name it as the thing to automate or streamline next.

Produce the recommendation block from `SKILL.md`. On approval, write the ADR using `database-architecture`'s `adr-template.md` in `docs/architecture/decisions/`. The **Revisit when** line is a concrete trigger: a deploy-frequency threshold where manual promotion breaks, a traffic level where the canary gate can tighten, a rollback incident that exposes a gap in the health signal, or a cost threshold on a second stack.

Then stop. The rollout-controller config, the probes, the migration scripts, and the flag wiring are a separate, explicitly-started step.
