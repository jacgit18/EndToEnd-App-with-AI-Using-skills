---
name: migration-cutover
description: A gated decision for how to move a live workload from one system to another — replacing a datastore, an application, or a hosting home — covering the cutover pattern (big-bang / phased-by-slice / parallel-run with dual-write and shadow reads / strangler-fig), the data-move mechanic (freeze-and-copy / backfill + change-data-capture / dual-write + backfill + reconcile), the verification evidence that says the target is correct enough to take traffic, the rollback trigger criteria and the window in which rollback stays possible, and the sequencing against consumer coupling. Use when someone says "we're migrating from X to Y", "we need to move off the old system", "cut over to the new database", "replatform this", "lift-and-shift to the cloud", "the legacy system is being retired", "how do we move the data without downtime", "replace the API gateway / ingress / reverse proxy", "swap the load balancer", or proposes a migration approach and wants it checked. It forces the user to state the driver, the data volume and change rate, the downtime and rollback tolerance, and who the consumers are before any cutover plan is drawn, then records the outcome as an ADR. Not for shipping a new version of a system that already exists — rolling / blue-green / canary release of one deployable unit is `deployment-strategy`. Not for choosing the target store or paradigm — that is `database-architecture`. Not for the topology of an existing store that is staying (replicas, sharding) — that is `data-tier-operations`, which hands the execution of a store move here. Not for retiring one endpoint, column, flag, or UI route inside a system that isn't itself moving — that is `change-surface-audit`, whose "point of no return" is one feature's own removal at a much smaller scale; this skill is for the datastore, application, or hosting *system* being retired wholesale.
---

# Migration & Cutover

Take a live workload that has to move — off a datastore that is reaching EOL, onto a new application, out of a datacentre, from one account or region to another — and decide how the switch happens: whether it is one flip or many, how the data gets across while it is still changing, what evidence proves the target is right before traffic lands on it, how long going back stays possible and what ends that, and which consumers move in what order. The skill makes the user name the driver and the real constraints (data volume, change rate, downtime budget, rollback window, consumer coupling) before any plan is drawn, recommends one approach with the cheapest safe option preferred, and writes an ADR.

## When to use

- The user is **replacing a system**: "we're moving from MySQL to Postgres", "off the mainframe", "retiring the legacy billing app", "consolidating two systems into one".
- The user is **relocating a workload**: "lift-and-shift to AWS", "move this service to the new Kubernetes cluster", "migrate the data to the new account / region".
- The user asks a **data-move question**: "how do we copy 2 TB without a maintenance window", "how do we keep the old and new DB in sync during the move", "how do we backfill history while writes keep coming".
- The user asks about **cutover safety**: "what's our rollback plan", "how do we know the new system is correct", "can we do this tenant by tenant".
- The user proposes a migration plan and wants it pressure-tested ("we'll take a 4-hour window Saturday and dump/restore").

## Out of scope — hand these off

- **Which target store / paradigm / source-of-truth** — SQL vs NoSQL vs a managed service, database-first vs contract-first → `database-architecture`. Migration assumes the target is already chosen; if it isn't, that decision comes first.
- **Scaling or distributing a store that is staying put** — read replicas, partitioning, sharding, the shard key, isolation → `data-tier-operations`. That skill decides the *target topology*; when reaching it requires a backfill-and-flip of a live store, it hands the **execution** of that move here.
- **Releasing a new version of an existing system** — recreate / rolling / blue-green / canary / feature-flag rollout of one deployable unit, expand-contract schema changes within a running system's normal release flow → `deployment-strategy`. Migration is an A→B system transition with a data copy and consumer re-pointing; a deploy is a repeatable version bump. (They share blue-green / canary vocabulary and both cross-reference on rollback.)
- **The dollar cost** of running both systems in parallel, egress on the data copy, the target's steady-state bill → `technical-cost-decision`. This skill names that a parallel run has a cost and hands off the line items.
- **The test plan for the target system** — which levels, what to automate → `test-strategy`. This skill defines the *cutover verification* (parity checks, reconciliation), not the target's test suite.
- **Implementation** — the backfill scripts, the CDC pipeline, the dual-write shim, the reconciliation job. The skill stops at the ADR.
- **Choosing the target repo layout** — one repo, repo-per-service, or a hybrid → `microservices-decision`. That skill decides the target; when getting there means splitting or merging repos with history, CI, and open PRs to carry over, it hands the **execution** of that move here — same pattern as a store move.

---

## The gate

Before recommending any cutover pattern, data-move mechanic, or sequencing, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **Source and target** — the technology on each side, and version if it matters (e.g. MySQL 5.7 → Postgres 15, on-prem VMs → ECS Fargate).
2. **What connects to the source today** — services, jobs, reports, ETL, third parties that read or write it, as far as the code and config show.
3. **Existing move tooling** — any replication, CDC (Debezium, DMS), ETL, or export/import path already in place.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not plan without them. If any is missing, name it and stop:

4. **The driver** — what is *actually* forcing this move, concretely. One of: an end-of-life / unsupported / out-of-contract deadline (with the date), a cost problem (the current number), a capability the source cannot provide (name it), a compliance or residency requirement, or a consolidation mandate. "The new system is better", "we want to modernise" is **not** a driver — it is a reason to stop and find the real one, or to defer the migration.
5. **Scope of this cutover** — exactly what moves in *this* migration and what stays: which tables / datasets / capabilities / tenants. The seam. A migration with an unstated boundary expands until it fails.
6. **Data volume and change rate** — how much data crosses (rows / GB, and the largest single table or dataset), and how fast it changes *during* the move: writes/sec to the source, and whether that can be paused. A static 10 GB dataset and a 10 GB dataset taking 500 writes/sec are different migrations.
7. **Schema / semantic delta** — how different is the target shape: a like-for-like copy, a re-typed / re-keyed schema, a denormalised or split model, a different consistency model. This decides whether a straight copy works or a transform-and-reconcile step is required.
8. **Downtime tolerance and RPO** — how long the workload may be unavailable at the flip (a number: zero, minutes, a weekend window), and how much in-flight data may be lost if the flip goes wrong. "Zero downtime, zero data loss" is a valid answer but it forces the pattern (parallel run) and its cost.
9. **Rollback window** — after traffic moves to the target, how long must reverting to the source remain possible, and what *ends* that possibility — the first target-only write that cannot be replayed back, a schema change on the source, decommissioning. Name the point of no return.
10. **Consumer coupling** — for each item in fact 2: can it be pointed at the target, and when — before, at, or after the flip; does it need both to work at once; is there a consumer (a third party, a quarterly report, a mobile client with a slow release cycle) that pins the source alive regardless.
11. **Verification bar** — what evidence will say the target is correct enough to take traffic: row-count and checksum parity, shadow-read diff rate below a threshold, a business metric (revenue, order count) matching for a period, a reconciliation report with zero unexplained deltas. "It looked fine in staging" is not a bar.
12. **Operational capacity** — who runs the backfill and watches it, who owns the dual-write shim, who is on the flip call, who investigates a reconciliation mismatch at 2am.

"We're moving to the new database, plan the migration" with items 4–12 absent is not valid input.

**A deadline does not open the gate.** "The old contract ends in three weeks", "the datacentre lease is up", "just give me the runbook" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–12 in one sentence each, because a cutover with no verification bar and no rollback window is how a migration becomes a data-loss incident with no way back.

---

## Challenge a proposed approach

If the user opens with the plan already chosen, put their reasoning under the gate, then test the specific claim against `cutover-patterns.md`:

- **"we'll take a maintenance window and dump/restore"** (big-bang) — what is the restore-plus-verify time for the volume in item 6, measured not guessed, and does it fit the window in item 8 with margin? What is the rollback if the target is wrong *after* the window closes and writes have landed? Big-bang is correct for small, low-change data with a real downtime budget — confirm all three.
- **"dual-write to both systems"** — what reconciles the two when a write succeeds on one side and fails on the other? Is the dual-write in the application (every writer must adopt it) or in the data layer (CDC)? Which side is authoritative during the parallel run? Dual-write without reconciliation is two diverging datasets.
- **"we'll do it tenant by tenant"** (phased) — are the tenants actually independent in the data (no shared rows, no cross-tenant queries, no global sequences)? What runs the system in a mixed state where tenant A is on the target and tenant B is on the source — do shared consumers handle both? Phased limits blast radius only if the slices are genuinely separable.
- **"strangler fig — the new service takes over endpoints one at a time"** — what sits in front routing per-capability (a proxy, a facade), and does the old and new share a database during the transition or is each capability's data moved with its endpoint? Strangler is for replacing an application over months; it is not a data-store move mechanic on its own.
- **"CDC will keep them in sync"** — CDC replicates *changes*; what does the initial bulk load, and how do you guarantee no change is lost in the gap between the bulk snapshot and the CDC stream starting? How is the transform in item 7 applied to the stream? What is the replication lag at the flip and does item 8's RPO tolerate it?
- **"we tested it in staging, we're good"** — staging data volume and staging traffic vs item 6. Verification (item 11) is a production-parity measurement, not a staging smoke test.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `cutover-framework.md` in order once the gate is satisfied. In short: confirm the driver is real and dated → freeze the scope and write down what is explicitly *not* in this cutover → classify the data move from volume × change rate × schema delta (static → freeze-and-copy; changing + like-for-like → bulk load + CDC; changing + transformed → dual-write or CDC-with-transform + reconcile) → pick the cutover pattern from the downtime budget and consumer coupling (big-bang / phased / parallel-run / strangler) → design the verification: the parity checks, the shadow-read comparison, the business-metric watch, the sign-off threshold → design the rollback: what stays warm, how writes reverse, the point of no return, and the decommission step that is deliberately *after* it → sequence the consumers → recommend and record.

Reference files:

- `cutover-patterns.md` — the four cutover patterns (big-bang, phased-by-slice, parallel-run with dual-write + shadow reads, strangler-fig): what each costs, when each fits, and its failure mode. The data-move mechanics (freeze-and-copy, bulk snapshot + change-data-capture, dual-write + backfill + reconcile) and how the initial-load / streaming-changes gap is closed without loss. Reconciliation approaches. Rollback design and the point of no return.
- `cutover-framework.md` — the 8-step process, worked once the gate is satisfied.

---

## Output

**1. In chat, a recommendation block:**

```
Driver:              <the dated EOL / cost / capability / compliance / consolidation reason from gate item 4>
Scope (in):          <exactly what moves in this cutover>
Scope (out):         <what explicitly stays / is a later migration>
Data move:           <freeze-and-copy | bulk load + CDC | dual-write + backfill + reconcile> — <why, from volume × change rate × schema delta>
Schema delta:        <like-for-like | re-keyed | transformed> — <where the transform runs>
Cutover pattern:     <big-bang | phased by <slice> | parallel run (dual-write + shadow reads) | strangler fig> — <why, from downtime budget + coupling>
Downtime at flip:    <the window, or "none"> — meeting RPO <x>
Verification bar:    <the concrete checks and the threshold that authorises the flip>
Rollback:            <what stays warm, how writes reverse, for how long> ; point of no return: <the first irreversible event>
Consumer sequence:   <who moves before / at / after the flip; who pins the source alive>
Tradeoffs accepted:  <2–4 concrete costs: parallel-run complexity, dual-write coupling, a stale window, a frozen period, reconciliation toil>
Not chosen because:  <one line per rejected pattern>
Cost follow-up:      <hand to technical-cost-decision: parallel-run duration, egress on the copy, target steady-state>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). Reference any related `database-architecture` (target choice) or `data-tier-operations` (target topology) ADR. Fill "Revisit when" with the concrete trigger that reopens this — "the parallel run exceeds N weeks without reaching the parity threshold" (the pattern isn't working), "shadow-read diff rate stops falling", "a second dataset needs the same move" (template it), "the source's EOL date moves".

Then stop. Implementation — the backfill job, the CDC pipeline, the dual-write shim, the reconciliation report — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the driver dated, the scope frozen, the data move classified against real volume and change-rate numbers, a verification bar with a threshold, a rollback window with a named point of no return — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "MySQL 5.7 → Aurora Postgres 15. Support for 5.7 ends in 8 months. ~1.4 TB, biggest table is 600 GB of append-mostly event rows, ~800 writes/sec sustained on the OLTP tables, can't pause them. Schema is mostly like-for-like but three `ENUM` columns and the JSON handling change. Consumers: the monolith, two Lambdas, a nightly Redshift ETL, and a partner SFTP export that runs weekly off a read replica. We can take a 15-minute write freeze but not more. Zero data loss. We need to be able to roll back for a week after cutover. Two backend engineers plus a DBA on contract."

Gate satisfied. Framework: changing data + near-like-for-like schema → **bulk load + CDC** (AWS DMS full-load + CDC, or a snapshot + Debezium), with the three column transforms applied in the CDC transformation layer. Cutover pattern: **parallel run** — DMS keeps Aurora in sync, run shadow reads from the monolith comparing result sets, watch the diff rate. Flip: 15-minute write freeze to let CDC lag drain to zero, verify row counts + checksums on the top 20 tables + the weekly export's query, then repoint. Rollback: keep MySQL live and reverse the CDC direction (Aurora → MySQL) for one week; point of no return is the first schema change on Aurora or decommissioning MySQL — schedule both *after* the week. Consumer sequence: monolith and Lambdas at the flip; Redshift ETL repointed same day; partner SFTP export moved last, after one clean weekly cycle. Tradeoffs: a week of running both (→ `technical-cost-decision`), CDC transform complexity for the three columns, reconciliation toil during the parallel run. Not big-bang: 1.4 TB won't restore-and-verify in 15 minutes. ADR; Revisit when the diff rate stops falling or the parallel run passes 4 weeks.

> "We're moving to the new database next quarter, can you write the migration plan."

Gate not satisfied — item 4 (no driver — "moving to the new database" is a restatement, not a reason), item 6 (no volume or change rate), item 8 (no downtime or RPO), item 10 (consumers not named). Response: name what's missing, note that a cutover with no verification bar and no rollback window is a data-loss incident waiting to happen, and ask for the driver with its date, the data volume and write rate, the downtime budget, and the list of things that connect to the current store. Do not recommend a pattern.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Copy the `migration-cutover/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.
