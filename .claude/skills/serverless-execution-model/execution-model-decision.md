# Execution Model Decision

The compute-primitive and invocation-model comparisons behind gate items 3–5 in `SKILL.md`.
Written in AWS terms (Lambda / Fargate / ECS / API Gateway); the shapes transfer to Azure
Functions/Container Apps or GCP Cloud Functions/Cloud Run.

## Compute primitive: FaaS vs container task vs long-running service

| | FaaS (Lambda) | Container task (Fargate/ECS) | Long-running service |
|---|---|---|---|
| **Max duration** | Hard platform ceiling (15 min on Lambda) | No inherent ceiling | No ceiling |
| **State between invocations** | None — assume a fresh environment every time (though the runtime *may* be reused, never design around it) | Can hold in-memory state for the task's lifetime | Can hold state indefinitely |
| **Cold start** | Real, on the order of tens of ms to a few seconds depending on runtime/package size and whether it's the first invocation in a while | Slower to start a new task, but typically kept running so it's not a per-request cost | None — already running |
| **Scaling model** | Automatic, per-invocation, scales to zero when idle | Scales by task count, typically via a target-tracking policy — minutes, not milliseconds | Manual or autoscaled by the same mechanism as any service |
| **Local disk / custom runtime / GPU** | Limited ephemeral storage, restricted runtimes, no GPU | Full container control — any runtime, attached storage, GPU-enabled instance types available | Full control |
| **Cost model** | Pay per invocation + duration; free at zero traffic | Pay for the task's running time regardless of whether it's handling a request | Pay for the instance regardless of load, unless autoscaled to zero (rare) |
| **Ops burden** | Lowest — no servers, no runtime patching | Moderate — you own the container image and its base-image patching, not the underlying host | Highest — you own the host, the runtime, and the process supervision |

**Decision rule:** rule out by the hard limits first, then choose on preference within what's
left.

- Duration above the FaaS ceiling, or a need for a custom runtime, GPU, large local disk, or
  a persistent network connection (a long-lived WebSocket, a database connection pool kept
  warm across many logical requests) → **not FaaS**. Choose a container task if the workload
  is still bursty/on-demand, or a long-running service if it's genuinely always-on.
- Short (well under the ceiling), stateless, event-driven, and either bursty or low-volume
  enough that cold starts and per-invocation billing are net wins → **FaaS**.
- Steady, predictable, high-volume traffic where a warm process avoids repeated cold starts
  and the per-request cost of an always-on container beats per-invocation FaaS pricing at that
  volume → **container task or long-running service**, sized by `capacity-estimation` and
  priced by `technical-cost-decision`.
- If cold starts are the only objection to FaaS and duration/resource profile otherwise fit,
  consider provisioned concurrency (keeps a set number of instances warm) before abandoning
  FaaS for a container — it's a narrower fix than moving the whole workload.

## Invocation models and their built-in failure handling

Three distinct models, each with different consequences for who retries what:

### 1. Synchronous

The caller blocks until the function returns a response.

- **Examples**: API Gateway → Lambda for an HTTP response; any direct SDK invoke-and-wait
  call; a Step Functions Task invoked in synchronous mode.
- **Error handling**: errors return directly to the caller. There is no automatic retry —
  the *caller* decides whether and how to retry, which is exactly the retry-budget policy
  `resilience-strategy` owns for a live request path.
- **Cost of chaining synchronously**: if this function's job is itself to call another
  function and wait for it, the caller's timeout must exceed the callee's, cold starts stack
  across hops, and a change to the callee's duration or contract silently affects the caller.
  Prefer an async or event-based handoff between steps that don't need an immediate answer
  passed back up the chain.

### 2. Asynchronous (fire-and-forget)

The caller does not wait; the platform queues the invocation and runs it later.

- **Examples**: S3 upload event → Lambda; EventBridge scheduled/rule-matched event → Lambda;
  SNS message → Lambda subscriber.
- **Error handling**: the platform retries automatically a small, fixed number of times (on
  Lambda, twice — three attempts total) with no caller involvement. What's left after retries
  are exhausted goes to a configured **failure destination** (a DLQ, another queue, or an
  EventBridge bus) if one exists — if none is configured, the failure is silently dropped.
  This makes configuring the failure destination a design decision (gate item 7), not an
  afterthought.

### 3. Poll-based (event source mapping)

The platform continuously polls a queue or stream and invokes the function with batches of
records.

- **Examples**: Lambda triggered by SQS, Kinesis, DynamoDB Streams, or a Kafka-compatible
  source.
- **Error handling differs by source type**:
  - **SQS**: a failed message becomes visible again after its visibility timeout and is
    redelivered; a **redrive policy** with a `maxReceiveCount` sends it to a DLQ once that
    count is exceeded. Partial-batch-failure reporting lets the function tell SQS exactly
    which messages in a batch succeeded, so only the failed ones are redelivered — implement
    this rather than failing (and thus retrying) the whole batch for one bad message.
  - **Kinesis / DynamoDB Streams**: records are retried for up to 24 hours (configurable) or
    until a configured retry-attempt limit, then either skipped or sent to a failure
    destination — but note these sources preserve *order per shard/partition key*, so a
    stuck record can block everything behind it on the same shard until it's resolved or
    skipped. This is a materially different failure mode than SQS's per-message redelivery.

### Comparison

| Model | Caller waits? | Who retries | Typical use |
|---|---|---|---|
| Synchronous | Yes | The caller, per its own retry-budget policy | API responses, interactive requests |
| Asynchronous | No | The platform, a small fixed number of attempts, then a failure destination | Event-driven side effects with no immediate answer needed |
| Poll-based (event source mapping) | No (auto-triggered) | Depends on source — redelivery (SQS) or ordered per-shard retry (Kinesis/DynamoDB Streams) | Continuous queue/stream consumption |

**Choosing between them** follows directly from gate item 4: if whatever triggers this needs
an answer before it can proceed, it's synchronous, full stop — there's no version of "make it
faster by going async" that also hands back an immediate real answer. If nothing is waiting,
default to asynchronous for a single event, or poll-based when the source is inherently a
queue or stream to be continuously drained rather than a one-off event.

## Choosing what carries an event between steps

Once a step hands off to the next via a message or event rather than a direct call (gate
item 6), a second, separate decision follows: what actually sits in the middle. This is not
the same question as the invocation model above — it's what the invocation model (poll-based,
usually) is polling. Reach for the property actually needed, not whichever of these is
already deployed elsewhere in the account or feels more "real-time":

| | Queue (SQS) | Pub/sub (SNS) | Stream/log (Kinesis Data Streams, Kafka/MSK) | Ingest-to-destination (Kinesis Data Firehose) |
|---|---|---|---|---|
| **Delivery model** | One message goes to exactly one of a pool of competing consumers, then is deleted | One message fans out to every current subscriber (SQS queues, Lambda, HTTP endpoints, email/SMS) | Every consumer reads the same append-only log independently, at its own position | Ingests and buffers, then delivers to a fixed destination (S3, Redshift, OpenSearch) — no custom consumer |
| **Replay** | No — a message is gone once consumed and deleted | No — a subscriber that wasn't listening when the message was published misses it (unless it also has a durable queue behind it) | Yes, within the retention window (hours to indefinitely, configurable) — a new or restarted consumer can re-read history | N/A — not a consumer-facing store |
| **Ordering** | Standard: no ordering guarantee. FIFO: strict order *per message group ID*, with a throughput tradeoff | None — fan-out doesn't order across subscribers | Per-shard/per-partition, by a partition key you choose — same key always lands on the same shard, preserving order for that key | N/A |
| **Multiple independent readers** | No — the pool of consumers competes for each message, they don't each see everything | Yes, by design — that's the point of pub/sub | Yes — each consumer group/application tracks its own read position independently | No |
| **Delivery guarantee** | At-least-once (never exactly-once) | At-least-once per subscriber | At-least-once (per-shard ordering, not global) | At-least-once, with configurable buffering/batching |
| **Typical fit** | Work distribution across competing workers — a task queue | Notifying several independent, decoupled systems that something happened | High-throughput ordered event log with multiple analytics/processing consumers, or where replay-on-failure matters | Streaming straight into a data lake/warehouse with no custom processing step |

**Decision rule:**

- **Does one event need to reach several independent consumers**, each of which should see
  every event (an order placed → analytics, fulfillment, and notifications all react
  separately)? → pub/sub (SNS), typically fanning out to one SQS queue per consumer so each
  gets its own competing-worker pool and its own retry/DLQ without one slow consumer blocking
  another. This SNS-to-multiple-SQS pattern is the default "fan-out with durability" shape —
  SNS alone has no replay or durable buffering if a subscriber is briefly down.
- **Does work just need to be spread across a pool of workers, one worker per unit of work,
  no replay needed**? → a plain queue (SQS). Reach for FIFO only if a specific ordering
  guarantee is actually required (and accept the throughput ceiling that comes with it) —
  most task-queue workloads don't need it and standard SQS is simpler and higher-throughput.
- **Does a consumer need to replay history, or do multiple independent applications need to
  process the same events at their own pace** (a real-time pipeline plus a batch analytics
  job both reading the same click-stream)? → a stream/log (Kinesis Data Streams, or Kafka/MSK
  if the team already operates Kafka or needs its broader ecosystem/tooling). Size shard or
  partition count, and choose the partition key, from the ordering requirement — a key that's
  too coarse creates a hot shard; the shard/partition-key choice itself is
  `data-tier-operations` territory once real numbers exist.
- **Is the goal just to land streaming data in a data lake or warehouse with no custom
  processing step in between**? → Kinesis Data Firehose (or an equivalent managed
  ingest-to-destination service) — simpler than standing up a Data Streams consumer when
  there's no actual processing logic to run, only buffering and delivery.
- **Default posture**: don't introduce a new messaging technology because a scenario notes
  in some manual say it's "for real-time" or "for scale" — a queue moves messages just as
  fast as a stream for a single competing-consumer workload, and a stream adds real
  operational cost (shard/partition management, consumer-position tracking) that only pays
  for itself when replay or multiple independent readers are actually needed.
