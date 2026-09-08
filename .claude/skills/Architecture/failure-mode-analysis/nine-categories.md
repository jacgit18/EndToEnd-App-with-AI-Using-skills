# The Nine Failure-Mode Categories

Reference for `SKILL.md` step 3 and step 4. For each component and each interaction, walk
all nine. Each category below gives: what it means, the probe questions to ask, the
distributed-systems / async specifics, and an example `cause → manifestation → impact` row.

The source note (`Architecture/01. System Design/Failure Modes.md`) defines the categories;
this file adds the *probe questions* and the async-interaction specifics it lacks, so the
walk is repeatable rather than freeform.

Record `n/a — <reason>` when a category genuinely does not apply to a component, so a
skipped category is a decision on the record, not an omission.

---

## 1. Functional

**The system runs and responds, but the behaviour is wrong.**

Probe:
- Wrong calculation, wrong rounding, wrong currency/unit.
- Invalid state transition (an order goes `shipped → pending`; a payment marked paid on a
  partial amount).
- A business rule applied incorrectly, or not at all, at an edge (zero, negative, empty,
  max-length, timezone boundary, leap second).
- Data corruption on write — a field truncated, encoded wrong, or overwritten.
- A feature flag or config value read wrong so the wrong branch runs.

Distributed specifics: a partial failure leaves the aggregate in a state no single service
thinks is invalid but the whole is (order created, inventory not decremented).

Example: *a rounding bug in the tax calculation (cause) → invoices are off by one cent
(manifestation) → reconciliation fails monthly, finance does manual correction, small but
compounding trust cost (impact, blast radius: every invoice)*.

## 2. Availability

**The component is unreachable or cannot do its job at all.**

Probe:
- Process crash (OOM, unhandled exception, panic), and does it restart cleanly.
- Deadlock / livelock — two operations each holding what the other needs.
- Resource exhaustion: file descriptors, threads, connection-pool slots, disk full, inode
  exhaustion, ephemeral port exhaustion.
- Startup dependency — the component can't boot because something it needs at init is down.
- A single point of failure with no redundancy (one instance, one AZ, one leader with no
  failover).

Distributed specifics: quorum loss (a 3-node cluster drops to 1); a control-plane outage
that leaves the data plane running but unmanageable; DNS failure making a healthy service
unreachable.

Example: *a slow query holds a DB connection, connections pile up, the pool is exhausted
(cause) → every request 503s (manifestation) → full outage of the service until the pool is
recycled (impact, blast radius: whole service)*.

## 3. Performance

**It works, but too slowly or with too little throughput to be useful.**

Probe:
- p99 / p999 latency far above p50 — a long tail that times out upstream callers.
- Throughput collapse under load (a queue that drains slower than it fills → permanent
  backlog).
- Thread-pool / event-loop starvation — one slow path blocking all others.
- N+1 queries, missing index, full-table scan that only shows at production data size.
- Cold-start / warm-up latency after a deploy or scale event.
- Head-of-line blocking on a shared channel.

Distributed specifics: a slow dependency's latency adding to every caller's latency
(latency amplification across hops); retry amplification turning a slowdown into a storm.

Example: *traffic hits 3× average at the evening peak (cause) → the recommendations call's
p99 goes from 200ms to 4s and ties up worker threads (manifestation) → the whole page slows
and some requests time out; checkout still works but conversion drops (impact, blast radius:
all users at peak)*.

## 4. Consistency & reliability

**Behaviour is inconsistent over time or across replicas; data diverges.**

Probe:
- Race condition — two writers, last-write-wins silently loses one.
- Lost update, dirty read, phantom read (name the isolation level and whether it's enough).
- Event duplication (at-least-once delivery) processed non-idempotently → double effect.
- Event loss (at-most-once, or a crash between receive and commit).
- Partial write / partial commit — some of a multi-step change lands, some doesn't, no
  rollback.
- Replica lag serving a read-your-writes violation (user updates, then sees the old value).
- Clock skew breaking an ordering or expiry assumption.

Distributed specifics: split-brain (two nodes both think they're leader, both accept
writes); a Saga that fails mid-way with a compensating transaction that itself fails;
read-repair that never converges.

Example: *the payment webhook is delivered twice by the provider (cause) → the non-idempotent
handler credits the account twice (manifestation) → customer balance wrong, manual clawback,
support load (impact, blast radius: affected customers, ~1/week)*.

## 5. Integration

**Failures at the boundary between two systems that each work alone.**

Probe:
- Schema mismatch — a field renamed, removed, retyped, or made nullable without coordination.
- Version incompatibility — client and server on different contract versions.
- Contract violation — a response that's valid JSON but breaks an unstated assumption
  (a list that's now sometimes null, a string that's now sometimes empty, an enum with a
  new value).
- Encoding / serialization drift — a date format, a number precision, a charset.
- Unexpected null / missing field / extra field the parser rejects.

Async specifics: a message schema evolved on the producer before all consumers can read it;
a new event type that old consumers don't know to ignore.

Example: *the pricing service changes `amount` (cents, int) to `amount` (dollars, decimal
string) in a minor release (cause) → checkout parses it as cents and charges 100× (or
crashes) (manifestation) → wrong charges / checkout outage until rolled back (impact, blast
radius: all checkouts during the window)*.

## 6. Dependency

**An external system this component relies on misbehaves.**

Probe:
- Third-party API down, slow, or returning errors.
- Rate limiting / quota exhaustion (429s) — and does the client back off or hammer.
- Auth expiry — a token or cert that lapses and isn't rotated.
- Network partition between this component and the dependency.
- The dependency returns success but with garbage, or with a 200 wrapping an error body.
- A transitive dependency (the thing your dependency depends on) failing.

Distributed specifics: a shared dependency failing takes down every service that uses it at
once (correlated failure); a dependency's retry of *its* dependency stacking with yours.

Example: *the payment gateway starts returning 429s under its own load (cause) → checkout's
uncapped retries triple the load on it, extending the outage; checkout requests queue and
time out (manifestation) → no payments accepted for 20 minutes (impact, blast radius: all
checkouts)*.

## 7. Security

**The system fails by allowing unauthorized or unsafe behaviour.** Coarse pass here — a
real threat model is separate.

Probe:
- An endpoint or admin function reachable without the auth it should require.
- Over-broad permissions (a service role that can do far more than it needs).
- A secret in the wrong place — logs, error messages, a client bundle, a repo.
- Injection surface — unparameterized query, template, or shell built from user input.
- Missing input validation / size limits (a path to resource exhaustion or a stored XSS).
- PII in a log or an analytics event that shouldn't carry it.
- A token with no expiry, or no revocation path.

Example: *an internal metrics endpoint is exposed through the public ingress by a
too-broad path rule (cause) → anyone can read internal request metadata (manifestation) →
information disclosure, possible compliance breach (impact, blast radius: whole service's
traffic metadata)*.

## 8. Operational

**Failures from deployment, configuration, and the running environment.**

Probe:
- Misconfigured env var / secret / connection string in one environment.
- A bad feature-flag rollout or a flag left in the wrong state.
- Wrong IAM / RBAC policy — the app can't reach a resource it needs, or can reach one it
  shouldn't. For an application-authorization system specifically, walk this against
  `access-control-modeling`'s granularity/tenancy vocabulary: a role granting resource-*type*
  access where only per-*instance* was intended, a shared-schema tenant filter forgotten on one
  query path, a role hierarchy that lets a lower role inherit an unintended action.
- A failed or half-applied database migration; a migration that locks a table.
- A deploy that succeeds (process healthy) but the app is broken (can't read a bucket,
  wrong region).
- Certificate / DNS / load-balancer config change with a blast radius nobody checked.
- No rollback path, or a rollback that doesn't work because the schema moved forward.
- Log/metric volume blowing a quota or a disk.

Example: *a deploy ships with the staging database URL in one region's config (cause) →
that region's writes go to staging, reads return "missing" (manifestation) → data loss for
users in that region until caught and replayed (impact, blast radius: one region, ~30 min
of writes)*.

## 9. Human & process

**Failures from people and workflow gaps around the system.**

Probe:
- Manual step that's easy to do wrong or skip (a runbook with an un-automatable step).
- Runbook missing, stale, or never tested.
- Alert with no clear owner — it fires and nobody knows whose it is.
- On-call without the access or context to act.
- A change process that lets a risky change through without review at the hours it's
  riskiest (Friday 5pm deploy).
- Knowledge concentrated in one person (bus factor 1) for a critical component.
- No practised failover — the DR plan exists on paper and has never been run.

Example: *the certificate for the payment callback endpoint is renewed manually once a year
(cause) → it lapses because the person who did it left and it wasn't documented
(manifestation) → payment callbacks fail for hours until someone figures out why (impact,
blast radius: all payment confirmations that day)*.

---

## Which categories to weight per component type

Not every component earns a deep walk in every category. A quick guide to where the modes
usually concentrate:

| Component type | Heaviest categories |
|---|---|
| Stateless service / API | availability, performance, dependency, integration |
| Datastore | consistency, availability, operational, performance |
| Queue / message bus | consistency (dup/loss/order), performance (backlog), dependency |
| Cache | consistency (staleness), dependency (cache-down fallback), performance (stampede), operational (eviction) |
| External API / third party | dependency, integration, security |
| Scheduled job / batch | functional (partial run), operational (missed run, overlap), performance |
| Human / manual step | human/process, operational, security |

Still record the others as `n/a — <reason>` so the walk is complete on paper.
