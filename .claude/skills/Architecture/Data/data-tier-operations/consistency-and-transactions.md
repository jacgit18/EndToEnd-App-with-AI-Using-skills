# Consistency and Transactions

Reference for step 5 (and parts of 3 and 7) of `operations-framework.md`.

## Isolation levels

Set per workload, not globally. Higher levels prevent more anomalies at the cost of throughput and more serialization failures to retry.

| Level | Prevents | Still allows | Use for |
|---|---|---|---|
| **Read Uncommitted** | (almost nothing) | dirty reads | effectively unused in MVCC engines |
| **Read Committed** (typical default) | dirty reads | non-repeatable reads, phantoms, write skew | the default for most OLTP; each statement sees the latest committed data |
| **Repeatable Read** / Snapshot | dirty + non-repeatable reads; phantoms in Postgres's implementation | write skew | a transaction that reads a value, computes, and writes back and must see a stable snapshot |
| **Serializable** | all of the above, including write skew | — (transactions behave as if run one at a time) | bookings, double-entry ledgers, "check a condition across rows then insert" — where write skew is a real bug. Expect to catch-and-retry serialization failures |

Rules of thumb:

- Start at the engine default. Raise the level only for the specific transactions with a named anomaly.
- A targeted `SELECT ... FOR UPDATE` (pessimistic row lock) on the contended rows is often cheaper than raising the whole transaction to Serializable.
- `SELECT ... FOR UPDATE` / `FOR NO KEY UPDATE` locks matched rows for the transaction's duration — precise, but holds locks; keep the transaction short.

## Optimistic vs pessimistic locking

- **Optimistic** — no lock held; on write, check a version column / timestamp and reject if it moved (the caller retries). Best when conflicts are rare and transactions or user think-time are long (a form the user edits for minutes). Wasted work is a whole retry.
- **Pessimistic** — lock the rows up front (`FOR UPDATE`), hold to commit. Best when conflicts are likely and the critical section is short (decrement a counter, move stock). Cost is contention and deadlock risk — always lock rows in a consistent order.

## MVCC note

Engines like Postgres use multi-version concurrency control: readers don't block writers and writers don't block readers, because each transaction sees a snapshot. This means "add a read replica" and "raise isolation" are somewhat independent levers — but long-running transactions still cause table bloat and block vacuum, which is its own scaling problem.

## Distributed transactions — cross-shard or cross-service writes

Pick the weakest one that meets the requirement.

### None

The write touches one shard / one service. Verify this is actually true before reaching for anything below — a good shard key (`scaling-topologies.md`) is what keeps it true.

### Transactional outbox + events (default for "update, then notify")

In one local transaction, write the business row **and** an `outbox` row describing the event. A relay process reads the outbox and publishes to a broker; consumers update their own data. Delivery is at-least-once, so consumers must be idempotent.

- **Guarantees** — the event is published if and only if the local transaction committed. No distributed lock, no coupled availability.
- **Accepts** — eventual consistency; consumers converge after a short delay.
- **Fits** — the large majority of cross-service data flow.

### Saga

A business transaction as a sequence of local transactions, each with a compensating action that semantically undoes it. Orchestrated (a coordinator drives the steps) or choreographed (each step emits an event the next listens for).

- **Guarantees** — every step either completes or is compensated; the system reaches a consistent end state.
- **Accepts** — intermediate states are visible (an order exists briefly with an unconfirmed payment); compensations are app logic you must write and test; no isolation between concurrent sagas unless you add semantic locks.
- **Fits** — multi-step workflows spanning services: order → reserve inventory → charge → ship, where a partial failure needs explicit rollback.

### Two-phase commit (2PC)

A coordinator runs a prepare phase (every participant votes and durably promises it can commit) then a commit phase. All commit or all roll back.

- **Guarantees** — atomic across participants; no partial outcome is ever visible.
- **Accepts** — participants' availability is coupled: a slow or crashed participant blocks the commit and holds locks on the others; the coordinator is a failure point (in-doubt transactions need recovery). Throughput drops.
- **Fits** — few, reliable, co-located participants where a partial outcome is genuinely unacceptable and eventual consistency won't do. Rare in service architectures; more common across two databases in one trust boundary.

### Eventual consistency (accept it explicitly)

No transaction — each side writes independently and a reconciliation / repair process converges them. Only when the data genuinely tolerates being divergent for a while and there's a converging mechanism (idempotent replay, periodic reconciliation job).

## Replication lag and read-your-writes

A single-leader topology's main correctness hazard. After a user writes, a read routed to a lagging replica can miss their own change.

- **Route to primary** the reads in a flow immediately after that user's write (simplest).
- **Lag-bounded read** — record the write's LSN/position; only serve from a replica caught up past it, else fall back to primary.
- **Sticky window** — pin a user to the primary for N seconds after any write.
- Decide this per flow — item 7 of the gate is exactly this list.

## Connection pooling

- **Why** — establishing a Postgres/MySQL connection is expensive (process/thread, TLS, auth); the server has a hard `max_connections`. Many app instances or serverless functions exhaust it fast.
- **Pooler** — PgBouncer, pgcat, RDS Proxy, Cloud SQL connectors. Sits between app and DB, multiplexes many client connections onto few server connections.
- **Modes** —
  - *Session* — a server connection is held for the client's whole session; least reuse, fully compatible.
  - *Transaction* — server connection returned to the pool at each `COMMIT`; best reuse; **breaks** session-scoped state — `SET`, session advisory locks, some prepared-statement patterns, `LISTEN/NOTIFY`. Audit the app for these.
  - *Statement* — returned per statement; no multi-statement transactions; rare.
- **Placement** — central pooler is a shared failure point unless run redundantly; a sidecar per app pod avoids that but multiplies pooler count. Choose against the deployment shape.
- **Sizing** — pool size is not "as big as possible"; past the DB's useful concurrency, more connections add contention. Start near `(core_count * 2)` server-side and measure.
