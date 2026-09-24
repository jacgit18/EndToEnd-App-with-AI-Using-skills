# Cutover Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR.

## 1. Confirm the driver is real and dated

Restate gate item 4 as one sentence with a date attached. Then judge it:

- **EOL / unsupported / contract-ending** (a version out of support on a known date, a lease expiring, a licence not being renewed) → proceed; the date sets the outer deadline.
- **Cost** (the current spend is the problem, with a number) → proceed; chain the target's steady-state cost to `technical-cost-decision` so the migration is not trading one bill for a bigger one.
- **Capability gap** (the source genuinely cannot do a thing the business now needs — a data type, a scale ceiling, a region, a compliance control) → proceed; name the specific capability so the verification bar can check the target actually provides it.
- **"Modernise", "the new one is better", "tech debt", "everyone's on X now"** → stop. There is no forcing function, which means there is no deadline, which means the migration can and should wait until there is a real driver — or the driver is cost/risk and needs to be stated as such. Do not plan a migration whose only justification is preference.

If item 6 (volume and change rate) is absent, the deliverable is "go measure data size, largest table, and source write rate", not a plan.

## 2. Freeze the scope — and write down what is NOT in it

From gate item 5. State the seam precisely: which datasets, tables, capabilities, or tenants move in *this* cutover. Then write the **out-of-scope list** explicitly — the datasets that stay, the capabilities that follow later, the tenants in a second wave. A migration without a written boundary grows every week as "while we're in there" items attach to it, and a growing migration is one that slips its deadline and loses its rollback discipline.

If the honest answer is "everything, all at once", check that against item 6 and item 8 — a single flip of the entire estate needs either small data or a large downtime budget. If it has neither, the scope has to be sliced (step 4, phased pattern).

## 3. Classify the data move

From gate items 6 (volume, change rate) and 7 (schema delta). Pick one mechanic — `cutover-patterns.md` has the detail:

| Change rate during move | Schema delta | Mechanic |
|---|---|---|
| Static / can be paused | Any | **Freeze-and-copy** — quiesce writes, export, transform offline, import, verify, flip. Simplest; needs a downtime window sized to the copy. |
| Changing, cannot pause | Like-for-like or lightly typed | **Bulk load + change-data-capture** — snapshot the source, then stream changes (DMS, Debezium, native logical replication) until lag is near zero, flip during a short freeze. |
| Changing, cannot pause | Transformed / re-keyed / split / different consistency model | **Dual-write + backfill + reconcile** — new writes go to both sides (in the app or via a CDC transform), a background job backfills history, a reconciliation job proves convergence, flip reads when the diff rate is under threshold. |

The trap in the CDC and dual-write mechanics is the **gap between the initial load and the change stream**. Close it explicitly: either take the snapshot at a known log position (LSN / GTID / binlog coordinate) and start CDC from exactly that position, or start CDC first into a buffer and then load the snapshot and let the stream catch up. "We'll snapshot then turn on replication" without a shared position loses every write in between.

Record: the mechanic, the tool, where the transform runs (offline batch, CDC transformation, application dual-write), and how the load/stream gap is closed.

## 4. Pick the cutover pattern

From gate items 8 (downtime budget) and 10 (consumer coupling). `cutover-patterns.md` has the full comparison.

- **Big-bang** — one flip for the whole scope. Fits: small data, a real downtime window, like-for-like schema, few consumers that can all be repointed together. Fails when: the verify step overruns the window, or a post-flip defect has no fast rollback.
- **Phased by slice** (tenant / region / entity type / bounded context) — move a slice, verify, move the next. Fits: slices that are genuinely independent in the data, a desire to limit blast radius, a long deadline. Cost: the system runs in a mixed state for weeks — every shared consumer must handle both source and target at once.
- **Parallel run (dual-write + shadow reads)** — both systems live, writes go to both, reads served from the source while shadow reads hit the target and are compared; flip reads when parity holds; keep writing to both until the rollback window closes. Fits: zero / near-zero downtime, high-value data, an unclear-correctness target. Cost: the most moving parts — dual-write correctness, reconciliation, two systems' worth of load and spend for the overlap.
- **Strangler fig** — a facade in front routes per-capability; the new system takes over one capability at a time; the old system shrinks to nothing. Fits: replacing a whole application over months. Note: it is an *application* replacement strategy — each capability it moves still needs a data-move mechanic from step 3.

Record the pattern, and for phased/strangler the slice order and the mixed-state contract.

## 5. Design the verification

From gate item 11. This is the step that turns "it seems fine" into "it is authorised to take traffic". Define, with thresholds:

- **Structural parity** — row counts per table, and checksums / hashes over the rows (full for small tables, sampled or partitioned for large ones). Target: exact match, or a documented and explained delta.
- **Shadow-read comparison** (parallel run) — for a representative slice of real read traffic, run the query against both systems and diff the results. Track the diff rate over time; it should fall toward zero as backfill completes and dual-write bugs are fixed. Set the flip threshold (e.g. "< 0.01% mismatches, none in the money paths, for 72 hours").
- **Business-metric parity** — pick 2–4 numbers the business already watches (daily revenue, order count, active users, ledger balance) and confirm they match between systems for a settling period. A schema transform bug often shows here before it shows in row counts.
- **Reconciliation report** — a scheduled job listing every unexplained delta. The flip criterion is zero unexplained entries, not zero entries.

Record the checks, the thresholds, and who signs off that the bar is met.

## 6. Design the rollback

From gate item 9. A migration without a rehearsed rollback is a one-way door taken on faith.

- **What stays warm** — the source keeps running and, for CDC/dual-write patterns, keeps receiving writes (reverse the stream direction, or keep the app's dual-write on) so it stays a valid fallback, not a stale one.
- **How writes reverse** — the concrete mechanism to send traffic back: the config flip, the DNS / connection-string change, the feature flag. Rehearse it.
- **The rollback window** — how long the above is maintained. Every day of window is a day of paying for and operating both systems (→ `technical-cost-decision`).
- **The point of no return** — name the first event that makes rollback impossible: a target-only schema migration, a data-model change that can't be replayed to the source, the source's decommission. Schedule every one of these *after* the rollback window, never during it. The decommission step goes in the plan as an explicit dated task so it neither happens early nor is forgotten (paying for a dead system for a year).

Record: the warm-standby mechanism, the reverse-traffic mechanism, the window length, and the dated point-of-no-return / decommission tasks.

## 7. Sequence the consumers

From gate item 10. For each thing that connects to the source, place it:

- **Before the flip** — consumers that can safely read/write the target early (idempotent readers, a reporting job that can run against either).
- **At the flip** — the primary application(s) and anything that must switch atomically with them.
- **After the flip** — consumers with slow release cycles (mobile clients), external parties (give them a dated notice and a compatibility window), batch jobs that can run one more cycle against the source.
- **Pins the source alive** — a consumer that cannot move within the migration timeline (a quarterly regulatory extract, a partner who needs 6 months' notice). If one exists, the source cannot be decommissioned on the driver's date — surface that conflict now, not at the end.

Record the ordered list and any pin that threatens the deadline.

## 8. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR using `database-architecture`'s `adr-template.md` in `docs/architecture/decisions/`. The **Revisit when** line is a concrete trigger that says the plan needs re-examination: "the parallel run passes N weeks without hitting the parity threshold", "the shadow-read diff rate plateaus above the flip threshold", "the source EOL date changes", "a second dataset needs the same move" (turn this ADR into a template).

Then stop. Writing the backfill job, standing up the CDC pipeline, building the dual-write shim, and coding the reconciliation report are a separate, explicitly-started step.
