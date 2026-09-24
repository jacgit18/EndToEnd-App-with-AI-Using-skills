# Cutover Patterns & Data-Move Mechanics

Reference for `SKILL.md` step 3–6. Two axes: **how the data crosses** (mechanic) and **how traffic switches** (pattern). They combine — a parallel-run pattern is usually built on a dual-write or CDC mechanic.

---

## Data-move mechanics

### Freeze-and-copy

Quiesce writes to the source, export the data, transform it offline if needed, import to the target, verify, repoint.

- **Fits:** data that is static or whose writes can be paused for the length of the copy-plus-verify; one-off moves; small-to-medium volume.
- **Downtime:** the whole copy-plus-verify duration. Measure it on real volume before committing — export, transfer, import, and *verify* each scale with size, and verify is the one people forget to time.
- **Failure mode:** the window is sized from an optimistic copy estimate with no verify time and no contingency, the copy overruns, and the team is forced to either extend an outage or flip without verifying.
- **De-risk:** do a full timed rehearsal against a production-sized copy. The rehearsal number, plus 50%, is the window you ask for.

### Bulk load + change-data-capture (CDC)

Take a consistent snapshot of the source at a known log position, load it into the target, then stream every subsequent change (insert/update/delete) from the source's transaction log into the target until replication lag is near zero. Flip during a brief freeze that lets lag drain to zero.

- **Tools:** AWS DMS (full-load + CDC mode), Debezium + Kafka, native logical replication (Postgres publications, MySQL binlog replication), Google DMS.
- **Fits:** live data that cannot be paused, with a like-for-like or lightly-typed schema. The standard near-zero-downtime mechanic.
- **The load/stream gap** is the whole game. Two safe orderings:
  1. **Snapshot-then-stream from a position:** record the log coordinate (LSN / GTID / binlog file+offset) at snapshot time, load the snapshot, start CDC from *exactly* that coordinate.
  2. **Stream-then-snapshot:** start CDC into a buffer/target first, then take the snapshot; the target applies buffered changes and converges. Handles the case where you can't pin the snapshot to a coordinate.
  Anything that "turns on replication some time after the export" without a shared position silently drops the writes in between.
- **Failure mode:** replication lag at flip time is larger than the RPO allows; or a schema/type edge case (timezones, `ENUM`, `JSON`, generated columns, collation) is mishandled by the CDC transform and corrupts a subset of rows that row-count checks don't catch — business-metric parity (framework step 5) is what catches it.

### Dual-write + backfill + reconcile

New writes are applied to both source and target — either in application code (every writer calls both) or via a CDC transform that projects source changes into the transformed target shape. A background job backfills historical data. A reconciliation job continuously compares the two and reports divergence. Reads stay on the source until the diff rate is under threshold, then flip; writes stay dual until the rollback window closes.

- **Fits:** live data *with* a schema transform, re-keying, splitting one store into several, or a consistency-model change — cases where CDC alone can't produce the target shape safely.
- **Authoritative side:** during the parallel run the **source stays authoritative**. If a write succeeds on the source and fails on the target, that's a reconciliation item to fix forward; the reverse (target-only write) must not happen while the source is the fallback.
- **Application dual-write cost:** every code path that writes the data must adopt the dual-write, and each is a chance to miss one. A single missed writer means silent drift. Prefer routing all writes through one module before adopting this, or use the CDC-transform variant so there's a single projection path.
- **Failure mode:** partial-failure writes with no reconciliation → two datasets that diverge slowly and are both "sort of right"; or the backfill and the live stream race on the same row and last-write-wins picks the stale one (fix: backfill with "insert if not exists" semantics, or version/timestamp guards).

---

## Cutover patterns

### Big-bang

One flip for the entire scope, in a single planned window.

- **Fits:** small data + a genuine downtime budget + like-for-like schema + a handful of consumers that repoint together.
- **Cost:** low complexity, low overlap cost — you pay for both systems only briefly.
- **Risk:** all the risk lands in one window. If verification overruns or a defect surfaces after traffic is on the target and writes have accumulated, rollback means replaying or discarding those writes. Mitigate with a hard "verify by time T or roll back" rule decided *before* the window.

### Phased by slice

Move one independent slice at a time — a tenant, a region, an entity type, a bounded context — verifying each before the next.

- **Fits:** slices that share no rows, no cross-slice queries, no global sequences; a comfortable deadline; a low risk appetite.
- **Cost:** the system runs in a **mixed state** for the whole rollout. Every shared consumer (reporting, search indexing, a downstream ETL, cross-entity features) must read from both source and target and merge. That mixed-state contract is design work, not a detail.
- **Risk:** low blast radius per phase; the danger is discovering mid-rollout that the slices weren't as independent as assumed (a shared sequence, a global uniqueness constraint, a cross-tenant admin report) and having half the estate on each side.

### Parallel run (dual-write + shadow reads)

Both systems live. Writes dual-written (see mechanic above). Reads served from the source; a copy of read traffic ("shadow reads") also hits the target and results are diffed. When the diff rate holds under threshold for a set period, flip reads to the target. Keep dual-writing until the rollback window expires.

- **Fits:** zero / near-zero downtime requirement; high-value data; a target whose correctness needs to be *proven* under real traffic, not assumed.
- **Cost:** highest complexity and highest overlap spend — two systems taking full production load and storage for the length of the parallel run plus the rollback window. Dual-write correctness and reconciliation are ongoing toil during that time.
- **Risk:** lowest cutover risk (you've watched it be correct under real load before flipping, and rollback is a config change), bought with weeks of operational overhead and cost. Time-box it — a parallel run that runs indefinitely because the diff rate never quite clears threshold is a sign of a real bug being tolerated, not a safety margin.

### Strangler fig

A facade (proxy, gateway, routing layer) sits in front of the old system. New capabilities are built in the new system; the facade routes each capability to whichever system now owns it. Over time every capability moves and the old system is deleted.

- **Fits:** replacing a whole application over months or quarters, incrementally, with continuous delivery of value and no big-bang application rewrite.
- **Relationship to data:** strangler routes *capabilities*, not data. Each capability it moves still needs one of the mechanics above for its data — either the old and new share a database during the transition (simplest, but couples them), or each capability's data is migrated with its endpoint.
- **Risk:** low per-step; the failure mode is a strangler that stalls half-done — the easy capabilities move, the gnarly core stays on the old system for years, and now there are two systems and a facade to maintain forever. Commit to a completion date for the last capability, not just a start.

---

## Rollback design

| Element | What it means | Common mistake |
|---|---|---|
| **Warm standby** | The source keeps running *and* keeps receiving writes (reversed CDC, or app dual-write left on) so it's a current fallback | Letting the source go stale the moment traffic flips — now "rollback" means restoring from a backup and losing hours |
| **Reverse mechanism** | The concrete, rehearsed action to send traffic back — a flag, a connection string, a DNS record | Never testing it; discovering at incident time that the reverse path was never wired |
| **Rollback window** | The fixed period the warm standby is maintained | Leaving it open-ended (unbounded double cost) or closing it before the target has been through a full business cycle (month-end, a quarterly job) |
| **Point of no return** | The first event that makes rollback impossible — a target-only schema change, an un-replayable data-model change, decommission | Doing one of these *inside* the rollback window and not noticing rollback is now a lie |
| **Decommission** | A dated task to shut down and stop paying for the source, placed just after the window | Forgetting it — paying for and patching a dead system for a year — or doing it early |
