# Rollout Patterns

Reference for `SKILL.md` step 4–7. Mechanisms for getting a new version live, the parallel-change discipline for schema/contract evolution, and what makes an environment stage actually gate.

---

## Rollout mechanisms

| Mechanism | Downtime | Blast radius of a bad release | Rollback speed | Extra capacity | Infra needed | Main failure mode |
|---|---|---|---|---|---|---|
| **Recreate** | Full window | 100% (after window) | Redeploy old (slow) | None | None | Assuming the window is "fine" when it isn't; long restart = long outage |
| **Rolling** | ~None | Grows as the roll proceeds; caught early if watched | Roll back = another rolling update | Small (`maxSurge`) | Orchestrator | Fake readiness probes ("process up" ≠ "serving correctly"); old+new incompatible with each other |
| **Blue-green** | ~None (flip) | 100% at the flip, but instantly reversible | Flip back (seconds) | 1× full second stack | Two stacks + a traffic switch | Non-backward-compatible schema change makes the "instant rollback" a lie; connection draining at the flip |
| **Canary** | ~None | Bounded to the canary % until promoted | Drop canary weight to 0 (seconds) | Small (+5–10%) | Traffic split **+ queryable metrics** | No automated quantitative gate → it's just a slow manual rollout; too little canary traffic to detect a regression |
| **Feature flag / dark launch** | ~None (code already deployed) | Bounded to the enabled cohort; instant kill-switch | Toggle off (instant) | None | Flag service | Flag sprawl — every flag is a prod branch to test both ways and later delete; stale flags become incidents |

### Notes per mechanism

**Recreate** — legitimate for internal tools, batch jobs, and teams with an accepted maintenance-window culture. Don't over-engineer past it when it genuinely fits. The risk is a slow-starting app turning a "quick" recreate into minutes of downtime.

**Rolling** — the right default for stateless services without traffic-splitting infra. Two hard requirements: (1) readiness probes that check real dependencies and actual request-serving, not just liveness; (2) graceful shutdown — stop accepting new work, drain in-flight, then exit, within the orchestrator's termination grace period. `maxUnavailable`/`maxSurge` trade rollout speed against capacity dip. Because old and new serve simultaneously, the release must be compatible with the previous version (same reason expand/contract matters).

**Blue-green** — the answer when *rollback speed* is the pain and you can afford the second stack for the overlap. Green is validated (smoke tests from `test-strategy`, a soak) while blue still serves; then the switch. Keep blue warm for the rollback window, then reclaim it. It buys nothing for database changes — if green's migration isn't readable by blue, flipping back fails. Handle in-flight requests: drain blue's connections, don't hard-cut.

**Canary** — the answer when *blast radius* is the pain. Progressive traffic steps (e.g. 5 → 25 → 50 → 100) with a bake period at each, and an **automated analysis** step that compares the canary population's error rate / latency / business metric against the baseline population and aborts on a significant regression. Tools: Argo Rollouts, Flagger, Spinnaker, a service mesh + a controller. Two preconditions people skip: enough traffic for the canary slice to be statistically meaningful in the bake window, and a metrics source clean enough to gate on automatically. Without the automated gate, canary is a manual rollout with extra steps.

**Feature flags / dark launch** — decouples *deploy* (code is in prod, dormant) from *release* (turn it on). Enables: gradual cohort exposure, instant kill-switch independent of a deploy, A/B and ring rollouts, testing in production with internal users. The cost is real: each flag doubles the test matrix for the code it guards, and flags left in after rollout are latent bugs (the "off" path bit-rots, someone flips it in an incident, it breaks). Require a removal ticket per flag with an owner and a date. Use flags for individually risky changes; don't wrap every trivial change in one.

### Vendor mechanics — where each pattern lives on ECS vs. Kubernetes (EKS)

The mechanism decided above is a shape; on AWS these two container platforms implement it differently, and naming the wrong tool for the platform is a common "already decided" trap:

- **ECS**: **AWS CodeDeploy** is the deployment provider plugged into CodePipeline's deploy stage — it natively supports rolling, blue-green (two target groups behind an ALB, CodeDeploy flips traffic and can auto-rollback on a CloudWatch alarm), and canary (a defined traffic-shifting schedule, e.g. 10% then wait then 100%). Blue-green and canary are configuration on CodeDeploy, not custom-built.
- **EKS / Kubernetes**: rolling update is native to a `Deployment` object (`maxSurge`/`maxUnavailable` map directly to the rolling row above) via `kubectl apply` or a Helm upgrade — no extra tooling needed. Blue-green and canary are **not** built into vanilla Kubernetes; they need an add-on — Argo Rollouts or Flagger (both drive a service mesh or ingress controller's traffic split and can wire in the same automated-analysis gate the canary row above requires) — or a hand-rolled second Deployment + Service swap for blue-green.
- **The tell**: "we're on EKS and want canary" is not fully specified until the add-on is named — plain `kubectl`/Helm alone only gives rolling. Surface this gap explicitly rather than letting "Kubernetes handles it" stand as a rollout decision.

---

## Parallel change (expand / contract) for schema and contract evolution

The pattern that makes a schema, message-format, or API-contract change deployable and rollback-safe one step at a time. Each step is a separate release; the rollout mechanism above applies to each.

**Worked example — renaming `users.name` to `users.full_name`:**

| Step | Action | Why it's safe to stop or roll back here |
|---|---|---|
| 1. **Expand** | `ALTER TABLE users ADD COLUMN full_name text` (nullable, no backfill yet) | Old code doesn't know the column exists; nothing reads it. Rolling back the migration is just a `DROP COLUMN` of unused space. |
| 2. **Dual-write** | Deploy code that writes `full_name` on every write that sets `name`, and still writes `name` | Both columns are current. Rollback to step 1's code leaves `full_name` slightly stale but `name` is authoritative and correct. |
| 3. **Backfill** | Batch job: `UPDATE users SET full_name = name WHERE full_name IS NULL` — idempotent, chunked, re-runnable | Not a deploy. If it fails partway, re-run it. Reads still use `name`. |
| 4. **Switch reads** | Deploy code that reads `full_name` (still writing both) | Rollback returns to step 2's code, which reads `name` — still populated and current. |
| 5. **Stop writing old** | Deploy code that only writes `full_name` | `name` goes stale but is untouched. A rollback window here still has step 4's dual-write code as the target. |
| 6. **Contract** | After a soak: `ALTER TABLE users DROP COLUMN name` | No running version and no rollback target reads or writes `name` any more. |

The same shape applies to:

- **Event / message formats** — publish v2 alongside v1; migrate consumers; retire v1. Never change a field's meaning in place.
- **API contracts** — add the new field/endpoint; move clients; deprecate then remove the old — with a deprecation window sized to the slowest client's release cycle (mobile: months).
- **Splitting or merging tables** — expand into the new shape, dual-write, backfill, switch, contract.

The cost is more deploys and a period of carrying both shapes. The payoff is that no single step is a one-way door, so every release in the sequence can use a fast auto-rollback.

---

## What makes an environment stage actually gate

A stage gates a release only if all three hold:

1. **It can catch something the earlier stages can't** — production-like data volume and shape, production-like traffic or a realistic load test, real integrations (or faithful contract mocks). A "staging" with 200 hand-made rows catches nothing an integration test didn't.
2. **It has a promotion criterion that is actually enforced** — a green condition that blocks promotion when red, not a dashboard someone glances at. Automated where possible; a named human or board where judgement is genuinely required.
3. **It isn't routinely bypassed** — if every urgent release skips staging, staging is not part of the release path; either make it fast enough to keep in the path or accept it's optional and don't count on it.

Progression shapes and when each fits:

- **CI → staging → prod** — the common default. Staging auto-promotes on green pipeline + smoke; prod has a human gate for high-risk changes, auto for the rest.
- **CI → prod (canary as the gate)** — no staging environment; the production canary with automated analysis is the safety mechanism. Requires strong pre-merge tests and fast auto-rollback. A deliberate trade: less pre-prod assurance, more production-truth and fast reversal.
- **CI → staging → prod-canary → prod-full** — for units where a bad release is very expensive; pays double bake time for defence in depth.
- **Ring deployment** — internal users → beta cohort → everyone, via flags or environment targeting. A canary variant where rings are defined by *who* rather than *what percentage*.
