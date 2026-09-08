# migration-cutover skill

A gated decision for **how a live workload moves from one system to another** — a datastore
replacement, an application replatform, a hosting relocation. Decides the cutover pattern
(big-bang / phased / parallel-run / strangler), the data-move mechanic (freeze-and-copy /
bulk load + CDC / dual-write + backfill + reconcile), the verification bar that authorises
the flip, the rollback window and its point of no return, and the consumer sequence. Not the
choice of target store, not scaling a store that's staying, not a routine version release.

Built from the `Architecture/01. System Design/Migration Plan.md` note (objective, inventory,
risk, data-migration strategy, rollback plan, deployment strategy — phased / parallel /
cutover — and post-migration support), sharpened into a gate.

## Where it sits

```
database-architecture   →  WHICH target store + source-of-truth        (ADR)
data-tier-operations     →  target TOPOLOGY for a store that's staying   (ADR)  ─┐ hands execution of a live move ↓
migration-cutover         →  HOW the live workload crosses to the target  (ADR)  ← this skill
deployment-strategy       →  routine version release of a unit that exists (ADR)   (shares blue-green / canary vocab; cross-links on rollback)
```

`migration-cutover` assumes the target is already chosen (`database-architecture`) and, if
the target is a new topology of an existing store, that `data-tier-operations` picked it and
handed the *move* here. It is distinct from `deployment-strategy`: a migration is a one-time
A→B transition with a data copy and consumer re-pointing; a deployment is a repeatable
version bump of a system that already exists.

## The shape

A gate skill. It refuses to draw a cutover plan until the user supplies:

- **a real, dated driver** — EOL / cost / capability gap / compliance / consolidation, never "modernise"
- **scope** — exactly what moves in this cutover, and a written out-of-scope list
- **data volume × change rate × schema delta** — which classifies the data-move mechanic
- **downtime tolerance + RPO** — which, with consumer coupling, picks the cutover pattern
- **rollback window + point of no return**
- **consumer coupling** — who moves when, who pins the source alive
- **the verification bar** — the parity / diff / business-metric threshold that authorises the flip
- **operational capacity**

Then it prefers the cheapest safe option (freeze-and-copy + big-bang) and only reaches for a
parallel run when zero downtime and unproven-correctness genuinely require it.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 4–12 from the user), challenge-the-proposal, output contract. |
| `cutover-framework.md` | The 8-step process — driver → freeze scope → classify data move → pick pattern → design verification → design rollback → sequence consumers → record. |
| `cutover-patterns.md` | The data-move mechanics (freeze-and-copy, bulk load + CDC, dual-write + backfill + reconcile) and the load/stream-gap trap; the four cutover patterns and their failure modes; rollback design and the point of no return. |

## Output

1. A recommendation block in chat (driver, scope in/out, data move, schema delta, cutover
   pattern, downtime at flip, verification bar, rollback + point of no return, consumer
   sequence, tradeoffs, cost follow-up).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (parallel run overruns,
   diff rate plateaus, EOL date moves).

Stops before implementation (backfill job, CDC pipeline, dual-write shim, reconciliation report).

## Interaction with sibling skills

- **Chains from `database-architecture`** — the target store / source-of-truth ADR is the
  precondition; migration doesn't choose the target.
- **Chains from `data-tier-operations`** — when that skill picks a new topology (a shard key,
  a new replication layout) for a *live* store, reaching it is a backfill-and-flip; that skill
  hands the execution here. Reciprocal note added to `data-tier-operations`.
- **Distinct from `deployment-strategy`** — replatform / store move / consumer re-pointing =
  here; recreate / rolling / blue-green / canary release of an existing unit, and
  expand-contract schema changes in the normal release flow = `deployment-strategy`. Both
  cross-reference on rollback and share blue-green / canary vocabulary.
- **Chains to `technical-cost-decision`** — a parallel run and the rollback window mean paying
  for two systems; egress on the data copy; the target's steady-state bill. The recommendation
  block hands off the line items.
- **Defers to `test-strategy`** for the target system's test plan; this skill owns only the
  *cutover verification* (parity, reconciliation, shadow-read diff).
- **`learning-gate`** hands off here on migration questions rather than running its own rep
  gate (see `learning-gate` Step 3).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `deployment-strategy` (blue-green / canary phrasing), `data-tier-operations` (store
moves), and `database-architecture` (target choice).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`
and reuses its `adr-template.md`.

```
cp -r ".claude/skills/Architecture/migration-cutover" /path/to/other-repo/.claude/skills/
```
