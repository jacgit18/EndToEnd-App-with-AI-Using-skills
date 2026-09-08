# Scoring & Register Format

Reference for `SKILL.md` steps 2, 6, and 7. The source note names FMEA but gives no scoring
scheme and no register layout — both are defined here.

---

## Scheme A — RPN (Risk Priority Number)

`RPN = Severity × Occurrence × Detection`, each scored 1–10, so RPN ranges 1–1000.

Use RPN when: the system is long-lived or regulated, several teams depend on it, money or
safety is on the line, or the register will be tracked and re-scored over time.

### Severity (S) — how bad is the impact if this mode occurs

| S | Meaning |
|---|---|
| 1–2 | Cosmetic. No user-visible effect, or a trivial one with an obvious workaround. |
| 3–4 | Minor. Some users inconvenienced; no data affected; self-recovers or a quick manual fix. |
| 5–6 | Moderate. A feature is down or degraded for a subset of users; recoverable; no permanent data effect. |
| 7–8 | Major. Whole-service outage, or wrong results reaching users, or a tenant-wide effect; recovery needs intervention. |
| 9–10 | Critical. Permanent data loss, a safety issue, a regulatory/compliance breach, money moved incorrectly, or a whole-system outage with a slow recovery. |

Calibrate with SKILL.md input 5 — write the concrete worst case next to "S10 here means:".

### Occurrence (O) — how often will this mode actually fire

| O | Meaning |
|---|---|
| 1–2 | Implausible to rare — less than once a year, needs an unlikely combination. |
| 3–4 | Occasional — a few times a year; a known-flaky dependency, a rare load pattern. |
| 5–6 | Moderate — monthly-ish; a dependency with real downtime, a load peak that recurs. |
| 7–8 | Frequent — weekly; a routine occurrence given current load and dependency reliability. |
| 9–10 | Constant — daily or on most deploys; effectively expected. |

Score against *current* conditions and near-term load, not a hypothetical future.

### Scoring standing gaps (no runbook, no DLQ, no success alert, bus factor)

Occurrence and Detection are written for *events with a frequency*. A standing gap — "there
is no runbook", "the reconciliation job has no success alert", "one person knows this
component" — is a permanent condition, not an event. Score it like this:

- **Occurrence** = how often the latent gap is *exercised* — i.e. how often an incident
  occurs that needs the missing runbook / alert / second owner. Not "the gap is always
  true" (that would make every process row O10 and swamp the register).
- **Detection** = would anything surface the gap *before* it bites (a game-day, an audit, a
  dependency check on boot)? Usually no, so D is high — which is the point: standing gaps
  are dangerous precisely because nothing reveals them until an incident does.

### Detection (D) — how likely are you to catch it *before* it causes its impact

**Inverted scale: high D = bad (you won't catch it).**

| D | Meaning |
|---|---|
| 1–2 | An automated guard catches it before user impact — a pre-deploy check, a synthetic probe, a hard constraint that rejects the bad state. |
| 3–4 | Alerting fires within minutes on the manifestation, on-call can act before most users notice. |
| 5–6 | It shows up in dashboards/logs but only if someone looks; no alert. Caught in hours. |
| 7–8 | No signal for this specifically; found when a related alert fires or during unrelated work. Caught in days. |
| 9–10 | Only discovered when a customer complains, an audit finds it, or it causes a bigger failure. |

For a system with **no telemetry yet**, score D against what exists *today* — usually 7–10.
A high D is not a reason to skip the row; it's a row for `observability-strategy`.

**When detection depends on another component.** If the only thing that catches a mode is a
reconciliation job, a nightly check, or a single alarm, its D is only valid *while that
component works*. Note the dependency on the row, and make sure the mode "that detector is
silently broken" is itself in the register — a mode that disables your detection outranks
its raw RPN.

### Contested severity

When a mode straddles two severity bands (is a systematic under-charge "money moved
incorrectly, S9" or "shipped and never paid, S10"?), record the **higher** severity, mark
the row **contested — confirm at triage**, and put it on the high-severity watchlist
pending resolution. Don't average the two or quietly pick the lower one; surface the
disagreement to the person triaging.

### Acting on RPN

| RPN | Action |
|---|---|
| **> 200**, or **S ≥ 9 at any RPN** | Must mitigate (or consciously accept with a named owner) before the design ships / the review passes. |
| **80–200** | Mitigate, or explicitly accept with a reason and an owner. Don't leave silent. |
| **< 80** | Log in the register, monitor; revisit if conditions change. |

RPN is a sorting aid, not a verdict. Two modes at RPN 180 can deserve very different
responses — the number ranks, the human decides.

---

## Scheme B — 2-axis grid (fast pass)

`Severity × Likelihood`, each 1–5, plotted on a 5×5 grid.

Use the grid when: it's a design-review pass under ~90 minutes, an early-stage design where
Occurrence and Detection can't honestly be scored to ten levels, or one or two people are
doing a first sweep. It's coarser on purpose — no false precision.

- **Severity 1–5**: 1 cosmetic · 2 minor · 3 a feature degraded for some users · 4
  whole-service outage or wrong results to users · 5 data loss / safety / compliance / money.
- **Likelihood 1–5**: 1 rare (<1/yr) · 2 occasional · 3 monthly · 4 weekly · 5 daily/most deploys.

| Band | Condition | Action |
|---|---|---|
| **Red** | `S×L ≥ 15`, or `S = 5 and L ≥ 3` | Mitigate or accept-with-owner before ship. |
| **Amber** | `S×L` 6–14 | Decide: mitigate, accept, or defer with a trigger. |
| **Green** | `S×L ≤ 5` | Register and monitor. |

Detection isn't scored in the grid, but still note per row whether you'd currently catch it
— it's the `observability-strategy` handoff signal.

You can start on the grid and promote the Red/Amber rows to a full RPN score later without
redoing the walk.

---

## The severity override (both schemes)

After ranking, pull **every mode with top-of-scale severity** (S10 in RPN, S5 in the grid)
into a separate **high-severity watchlist**, regardless of its RPN or band. A
catastrophic-but-rare, currently-well-detected mode scores low and gets buried; "rare"
is not "won't happen", and detection can regress. The watchlist is reviewed on its own.

---

## How many rows is a register

A rough anchor so the walk doesn't get cut short or padded: expect on the order of **2–3
modes per component and 1–2 per interaction** for a real system — so a pipeline of ~10
components and ~10 interactions lands around **20–35 rows**. Far fewer means the
nine-category walk was shallow (a whole category or a whole component went unprobed); far
more usually means near-duplicates that should be merged (tax-API-down and
shipping-API-down are one row "an enrichment dependency is down" unless their impact
genuinely differs). Merge on *shared cause and shared mitigation*; split when the impact or
the handoff differs.

## Register format

A table, sorted by RPN (or band) descending:

| ID | Component / Interaction | Category | Cause | Manifestation | Impact + blast radius | S | O | D | RPN | Priority | Owner | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

- **ID** — `FM-001`, stable across revisions of the register.
- **Category** — one of the nine (§ `nine-categories.md`).
- **Cause / Manifestation / Impact** — from SKILL.md step 5; concrete enough to write a test from.
- **S / O / D / RPN** — or `S / L / band` for the grid.
- **Priority** — `mitigate-before-ship` / `mitigate-or-accept` / `monitor`, from the tables above.
- **Owner** — who decides this row (required for block-sign-off mode; blank is a finding).
- **Handoff** — `resilience-strategy` / `observability-strategy` / `test-strategy` /
  `eng-backlog` / `threat-model` / `—`.

### High-severity watchlist

Same columns, filtered to S = max. Kept even when RPN is low.

### Acceptance log (block-sign-off mode only)

| ID | Decision | Rationale | Accepted by | Date | Revisit trigger |
|---|---|---|---|---|---|

One row per mode that is being *accepted* rather than mitigated now — so "we knew and chose
not to" is on the record with a name and a condition that reopens it.

---

## Worked scoring examples

From the checkout-service pre-mortem in `SKILL.md`:

| Mode | S | O | D | RPN | Why |
|---|---|---|---|---|---|
| Payment succeeds, Postgres write fails → double-charge risk | 10 | 4 | 7 | 280 | S10: money moved, no order. O4: needs a write failure in a narrow window, a few times/yr. D7: the path returns 200, only 5xx alarms exist, so no signal — caught by a customer dispute. → watchlist + resilience-strategy (outbox/idempotency) + observability-strategy (reconciliation alarm). |
| `order.placed` published, fulfilment consumer down → silent lag | 7 | 5 | 8 | 280 | S7: orders delayed, not lost (Kafka retains). O5: consumer deploys/restarts monthly-plus. D8: no consumer-lag metric today. → observability-strategy (lag alert) + test-strategy (inject consumer outage). |
| Pricing service returns stale price on cache fallback → wrong amount | 8 | 3 | 9 | 216 | S8: wrong charge reaches the user. O3: only on a pricing-cache fallback event. D9: nothing compares charged-vs-catalogue price. → observability-strategy + eng-backlog (price-check assertion). |
| gRPC pricing timeout under peak → checkout latency spike | 6 | 6 | 4 | 144 | S6: slow checkout, some abandonment. O6: recurs at evening peak. D4: latency dashboards + a p99 alert exist. → resilience-strategy (timeout + fallback) + capacity-estimation (the peak ceiling). |

Note the first two tie at RPN 280 but route differently — the number ranks, the categories
and the handoffs come from the row, not the score.
