# deployment-strategy skill

A gated decision for **how a new version of one deployable unit reaches production** — the
rollout mechanism (recreate / rolling / blue-green / canary / feature-flag), the environment
progression that actually gates, the expand/contract discipline for schema and contract
changes, the health signal that aborts a rollout, and the release cadence. Not moving a
workload to a different system (that's `migration-cutover`), not which tests run in the
pipeline (that's `test-strategy`), not the health signal's own design (that's
`observability-strategy`).

Built from the `Architecture/Devops/` notes — `Deployment Strategies.md` (CI/CD, deployment
patterns), `Release.md` (versioning, code freeze, release process), `Staged Deployment.md`
(environment progression), `Steps to Release Stage.md`, `Deployment Artifacts.md` — plus the
12-factor `V Build, release, run.md` and `Database Migrations.md`. The ECS-vs-Kubernetes
vendor-mechanics note in `rollout-patterns.md` was added `2026-09-04` from `Architecture/02.
Backing Service Options/Cloud/AWS/AWS CI-CD Pipeline.md` (CodeDeploy for ECS,
kubectl/Helm/Argo Rollouts/Flagger for EKS).

## Where it sits

```
test-strategy            →  which test LEVELS run, and at which pipeline stage
observability-strategy    →  the SLIs / health signal the rollout gates on
deployment-strategy       →  the rollout MECHANISM + progression + schema discipline + cadence   (this skill)  → ADR
migration-cutover         →  one-time move to a DIFFERENT system (data copy, consumer re-point)
technical-cost-decision   →  the dollar cost of a second stack / canary overhead
```

`deployment-strategy` **consumes** the pipeline stages from `test-strategy` and the health
signal from `observability-strategy`, and **hands off** second-stack capacity cost to
`technical-cost-decision`. It is distinct from `migration-cutover`: this is the repeatable
version bump of a unit that already exists; that is a one-time A→B system transition.

## The shape

A gate skill. It refuses to recommend a mechanism until the user supplies:

- **a real release pressure** — measured downtime, a blast-radius incident, slow rollback, or the batching doom-loop — never "best practice"
- **the unit and its class** — stateless service / stateful / worker / batch / frontend, which bounds the options
- **downtime tolerance + traffic shape**
- **rollback speed needed**, and which changes are legitimately forward-only
- **state and contract coupling** — does the release change shared schema / message formats / consumed API contracts
- **the progressive-delivery infrastructure that exists** — can two versions run, can traffic be split, is there a queryable health signal, a flag service
- **the environments that actually gate** and who signs off
- **cadence + operational capacity**

Then it prefers the simplest mechanism that fits (recreate/rolling before blue-green/canary)
and insists a gated rollout has a real health signal behind it.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 4–11 from the user), challenge-the-proposal, output contract. |
| `deployment-framework.md` | The 8-step process — pressure → classify unit → inventory infra → pick mechanism → define health signal + auto-rollback → expand/contract for schema → environment progression → cadence. |
| `rollout-patterns.md` | The five mechanisms compared (downtime, blast radius, rollback speed, capacity, infra, failure mode); expand/contract worked step by step; what makes an environment stage actually gate. |

## Output

1. A recommendation block in chat (pressure, unit class, mechanism + params, health signal,
   auto-rollback trigger, expand/contract steps, environment progression, sign-off, cadence,
   tradeoffs, cost follow-up).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (deploy-frequency threshold,
   traffic level to tighten the canary gate, a rollback incident exposing a health-signal
   gap, a second-stack cost threshold).

Stops before implementation (rollout-controller config, probes, migration scripts, flag wiring).

## Interaction with sibling skills

- **Consumes `test-strategy`** — the list of pipeline stages that exist; this skill decides
  how the rollout uses them (smoke against green before the flip), not the test mix.
- **Consumes `observability-strategy`** — names that a gated rollout needs a health signal
  (error rate + latency on changed paths, a business metric) and hands that signal's design
  there.
- **Distinct from `migration-cutover`** — recreate / rolling / blue-green / canary of an
  existing unit, and expand/contract schema changes in the normal release flow = here;
  replatform / datastore move / consumer re-pointing = `migration-cutover`. Shared vocabulary
  (blue-green, canary), reciprocal boundary notes in both.
- **Chains to `technical-cost-decision`** — blue-green's double stack, canary's extra
  capacity, a flag-service tier.
- **`learning-gate`** hands off here on rollout / release-process questions rather than
  running its own rep gate (see `learning-gate` Step 3).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `migration-cutover` (blue-green / canary phrasing, "cut over"), `test-strategy`
(pipeline stages), and `observability-strategy` (the health signal).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`
and reuses its `adr-template.md`.

```
cp -r ".claude/skills/Architecture/deployment-strategy" /path/to/other-repo/.claude/skills/
```
