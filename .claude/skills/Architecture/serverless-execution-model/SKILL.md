---
name: serverless-execution-model
description: A gated decision for how one unit of work actually runs — the compute primitive (function-as-a-service / a container task / a long-running service), the invocation model (synchronous request-response, asynchronous fire-and-forget, or poll-based event-source consumption of a queue or stream), whether a multi-step process needs a central orchestrator (a state machine) versus event-driven choreography versus a single function, the messaging technology that carries an event or message between steps when choreographed (a queue for competing workers, pub/sub for fan-out to independent consumers, a stream/log for replay or per-key ordering), and the failure contract inside that model (per-step retry count and backoff, which errors are caught vs left to fail terminally, the dead-letter queue or failure destination for what's exhausted, and the idempotency requirement retries impose). Use when someone says "should this be a Lambda or a container for this workload", "Lambda vs Fargate for this job", "do we need Step Functions for this", "should these steps be orchestrated or event-driven", "should we use SQS or SNS", "queue vs pub/sub vs stream for this", "Kinesis or Kafka for this", "the function times out after 15 minutes", "how do we handle a failed message", "add a dead-letter queue", "should this call be sync or async", "what happens when one branch of a parallel job fails", or hands over a workflow and asks how it should be wired. It forces the user to state the unit of work, its duration and resource profile, its trigger and concurrency pattern, whether it's a single step or needs coordination across several, and the failure semantics it can tolerate, before any primitive or orchestration mechanism is recommended, then records the outcome as an ADR. A bare conceptual comparison with no named workload ("what's the difference between Lambda and Fargate", "how does sync invocation differ from async") is answered directly, no gate — the gate exists for a pending decision on a named unit of work, not for explaining the vocabulary. Not for how many services or team boundaries exist — that is `microservices-decision`, which this skill assumes as given (it decides what runs one already-scoped unit of work, not how work is split across teams). Not for the execution role or account/network placement this workload needs — that is `cloud-iam-boundary`, which this skill hands the permission requirements to. Not for the retry-budget-and-backoff policy that protects a live request path under overload or cascading dependency failure — that is `resilience-strategy`; this skill's retry/DLQ contract is the per-invocation guarantee for one asynchronous unit of work eventually succeeding, being parked, or being dropped, not a defense against traffic spikes — if per-invocation retries are themselves hammering an already-struggling downstream, that's `resilience-strategy`'s concurrency-limit/circuit-breaker territory, run after this skill's contract is set. Not for the dollar cost of Lambda invocations, provisioned concurrency, or Step Functions state transitions, or for "X or Y, which is cheaper" — that is `technical-cost-decision`, which this skill's duration/concurrency numbers feed once the technical fit narrows the choice. Not for DynamoDB/Kinesis partition-key or shard topology when a poll-based consumer is stuck on a hot key — that is `data-tier-operations`; this skill owns the consumer-side retry/skip/redrive contract regardless of cause. Not for an unscoped, not-yet-designed system ("what should the backend for our new admin tool look like") — that is `design-scoping` first, which sequences a named unit of work back here.
---

# Serverless Execution Model

Take one unit of work that needs to run — a request that must answer immediately, a file
that landed in a bucket and needs processing, a multi-step business process with branches
and a wait for human approval, a continuous stream of events to consume — and decide what
actually executes it: a function that starts cold and dies after one invocation, a container
task that stays warm, or a long-running service; whether the caller waits for an answer or
the work happens later; whether several steps need a central, visible orchestrator or can
react to each other's events independently; and, when something in that chain fails, exactly
what happens to it — retried how many times, on what backoff, caught and routed where, or
given up on and parked for a human. The skill makes the user name the unit of work and its
real shape before any primitive is on the table, because "just use Lambda, it's serverless"
and "wrap it in Step Functions to be safe" are both defaults that get expensive or brittle
the moment the shape doesn't fit.

## When to use

- Someone is **picking a compute primitive** — "Lambda or Fargate for this", "should this run
  as a function or a container", "this job runs for 20 minutes, can it still be a Lambda".
- Someone is **deciding whether to orchestrate** — "do we need Step Functions here", "should
  these three services just react to each other's events instead", "how do we track where a
  customer's order is in this process".
- Someone hits a **concrete execution limit or failure** — "the function times out", "cold
  starts are killing our p99", "a batch of SQS messages keeps failing and blocking the
  queue", "one branch of our parallel step failed and took down the whole workflow".
- Someone is **designing the failure contract** for an async or event-driven path — "add a
  dead-letter queue", "how many times should this retry", "what happens to a message we can
  never process", "does this need to be idempotent".
- Someone asks about **invocation shape** — "should the client wait for this or not", "can we
  make this async so the API responds faster", "how do we process this stream continuously".
- Someone proposes a shape already-decided and wants it checked — "let's just chain Lambdas
  calling Lambdas", "we'll retry forever until it works", "wrap everything in one giant Step
  Functions workflow so we never lose visibility".

## Out of scope — hand these off

- **How many services exist and who owns them** — service boundaries, team ownership, repo
  layout → `microservices-decision`. This skill takes one already-scoped unit of work (inside
  one service, one team's remit) and decides what runs it; it does not decide whether that
  unit of work should live in its own service.
- **The execution role and network placement** — the IAM role this function/task assumes, its
  least-privilege permission set, and whether it sits in a public or private subnet →
  `cloud-iam-boundary`. This skill names what the workload needs to call; that skill designs
  the role and boundary that grants it.
- **Overload and cascade defense on a live request path** — rate limiting, circuit breakers,
  bulkheads, and the retry-budget policy that stops a struggling dependency from being
  hammered by retries under load → `resilience-strategy`. Overlap point: both skills talk
  about "retries with backoff." This skill's retry/Catch/DLQ design is the per-invocation
  contract for one asynchronous unit of work — does it eventually succeed, land in a DLQ, or
  get dropped — independent of whether the system is under load. The two compose: an
  async worker built here can *also* need a concurrency limit from `resilience-strategy` if
  its downstream is being overwhelmed by the retries this skill's contract generates.
- **Dollar cost** — per-invocation and provisioned-concurrency pricing for Lambda, vCPU/memory
  pricing for Fargate, per-state-transition cost for Step Functions → `technical-cost-decision`,
  which consumes the concurrency and duration numbers this skill produces.
- **Capacity numbers** — expected request volume, payload sizes, peak:average ratio →
  `capacity-estimation`, which this skill consumes (concurrency and duration inputs) rather
  than re-deriving.
- **Hot-partition or shard topology on a poll-based source** — if a DynamoDB Streams or
  Kinesis consumer is stuck on a poison-pill record, this skill owns the consumer-side fix
  (`ReportBatchItemFailures`, bisect-on-error, redrive to a DLQ) regardless of cause. Only if
  the failures trace to a genuinely hot partition key — the same key concentrating traffic,
  not a one-off bad record — does the fix move to `data-tier-operations`'s partition/shard
  design. Don't reach for a shard-key change before ruling out a plain poison-pill record.
- **An unscoped, not-yet-designed system** — "what should the backend for our new service
  look like" with no named operation, trigger, or duration yet → `design-scoping` first,
  which sequences a specific unit of work back here once purpose and functional scope exist.
- **Implementation** — the actual `.asl.json` state machine definition, the SAM/CDK/Terraform
  resources, the handler code. The skill stops at the ADR.

---

## The gate

Before recommending a primitive, an invocation model, or an orchestration approach, these
must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **What already exists** — any current Lambda/Fargate/ECS/Step Functions resources this
   unit of work is replacing, extending, or sitting beside; an existing event bus, queue, or
   orchestrator already in place that a new workflow could reuse instead of introducing a
   second mechanism.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do
not design without them. If any is missing, name it and stop:

2. **The unit of work** — is this a single request that needs one answer, a side effect
   triggered by an event (a file landing, a record changing), a multi-step business process
   with branching or parallel work, a scheduled/batch job, or a continuous stream to consume?
   "A backend thing" is not a unit of work.
3. **Duration and resource profile** — how long does one execution take (sub-second, a few
   seconds, minutes, hours), and does it need specialized hardware (GPU), a large local disk,
   a persistent network connection, or state carried between invocations? A hard ceiling
   (e.g. "must complete in under 15 minutes" is a FaaS platform limit, not a target to design
   toward) rules primitives in or out immediately.
4. **Trigger and response need** — what starts this (an HTTP request, a file event, a queue
   message, a stream record, a schedule, a manual start), and does whatever starts it need an
   answer back before moving on, or can it move on immediately?
5. **Concurrency and burst pattern** — is load bursty and unpredictable (favors auto-scaled
   FaaS) or steady and forecastable (favors provisioned/always-on compute)? What's the max
   concurrent executions this needs to support, and is a cold start (tens of ms to a few
   seconds, depending on runtime and package size) acceptable for this trigger, or does the
   caller need consistently low latency?
6. **Coordination across steps** — if this is more than one step, do the steps need a central,
   visible definition of the whole process (useful when you need to answer "where is order
   #4521 right now" or when there's branching, parallel fan-out, or a wait for an external
   callback/human approval), or is independent, event-triggered reaction between loosely
   coupled steps acceptable — trading a central view for looser coupling and one less piece
   of shared infrastructure? If steps hand off via an event or message rather than a direct
   call, what actually carries it matters too: does one step need to notify several
   independent consumers (fan-out), does work need to be spread across competing workers
   (a queue), does anything need to replay history or have multiple readers move through the
   same events at their own pace (a stream/log), and does ordering need to be preserved
   per-key? See `execution-model-decision.md`'s messaging-technology section — don't default
   to whatever queue or topic already exists in the account without checking it fits this
   shape.
7. **Failure semantics** — if a step fails, must it be retried automatically, parked for a
   human to inspect (a dead-letter queue), or is it safe to drop? Is the operation
   **idempotent** — can it safely run twice with the same input? If not, is idempotency
   something the user can add (an idempotency key, a conditional write), or is retrying
   unsafe outright, which changes the answer from "retry" to "fail fast and alert"?
8. **Team and existing infrastructure** — does the team already operate a container platform
   (ECS/Kubernetes) they're comfortable running workloads on, or do they want to avoid owning
   any infrastructure? Is there an existing event bus, queue, or orchestrator this should
   plug into rather than duplicate?

"Just make it a Lambda" or "wrap it in Step Functions" with items 2–7 unanswered is not valid
input — a 20-minute job named as "just make it a Lambda" fails on item 3 alone (past the
15-minute platform ceiling), and a single-step, non-branching operation wrapped in a state
machine "to be safe" pays orchestration overhead item 6 never justified.

**Urgency does not open the gate.** "We need this shipped today, just chain three Lambdas
together" is exactly the shape that produces synchronous Lambda-invoking-Lambda chains: each
hop pays cold-start latency, timeouts stack (the caller's timeout must exceed the sum of
everything downstream), costs multiply per hop, and a change to one function silently breaks
its caller. Naming items 2–7 in one paragraph is faster than debugging that chain's first
production timeout.

---

## Challenge a proposed approach

If the user opens with the mechanism already chosen, put their reasoning under the gate,
then test the specific claim against `execution-model-decision.md` and
`orchestration-and-failure-handling.md`:

- **"just use Lambda, it's serverless and simple"** — what's the actual duration ceiling
  (item 3)? Above ~15 minutes, or needing GPU/local disk/a persistent connection, Lambda is
  ruled out regardless of preference — that's a platform limit, not a style choice. Below it,
  is the trigger bursty (favors it) or does it need to avoid cold starts on every single call
  (may favor a provisioned-concurrency Lambda or a small always-on service instead)?
- **"wrap it in Step Functions so we don't lose track of it"** — is there real branching,
  parallel fan-out, or a wait-for-callback (item 6), or is this a straight linear chain of
  two or three steps? A linear chain gains little from a state machine over a single function
  calling the next step directly, or an event triggering the next step, and pays the extra
  infrastructure and per-transition cost for the visibility. Justify the orchestrator by the
  coordination need, not by "so we can see it in a console."
- **"let event-driven choreography handle it, everything reacts to everything"** — can anyone
  currently answer "where is instance #4521 in this process, and why is it stuck" without
  reconstructing the trail from logs across every service? If coordination or debuggability
  (item 6) matters and there's branching or a required order, choreography trades a real cost
  (no single place to see or resume workflow state) for looser coupling — name that cost
  explicitly rather than defaulting to it because it feels more "cloud native."
- **"chain Lambdas calling each other synchronously"** — every hop adds latency, the calling
  function's timeout must exceed everything downstream, and a change to the callee's
  contract or duration silently affects the caller. If step B doesn't need to hand a result
  back to step A immediately, invoke it asynchronously or via an event/queue instead of a
  direct synchronous call.
- **"retry forever until it works"** — unbounded retries with no backoff turn a transient
  blip into sustained load on a struggling dependency (this is where `resilience-strategy`'s
  retry-budget concern and this skill's per-invocation contract meet). Cap the attempts, use
  exponential backoff with jitter, and name what happens when attempts are exhausted (item 7)
  — "keep trying forever" is not a failure semantics answer, it's the absence of one.
- **"the whole Parallel state failing when one branch fails is fine, we'll just rerun it"** —
  by default a Parallel or Map state's failure aborts every branch, including ones that
  already succeeded and now have to redo work. If branches are independent and partial
  success is meaningful (some items processed, some not), catch failures per-branch or use a
  tolerated-failure-percentage on a Distributed Map instead of accepting all-or-nothing.
- **"just use SQS for everything" / "let's use Kinesis, it's real-time"** — a queue (SQS)
  hands each message to exactly one of a pool of competing workers and deletes it once
  processed; it's the wrong tool the moment a second, independent consumer also needs to see
  the same event (that's fan-out — SNS, or a stream), or a consumer needs to replay history
  it missed (a queue's gone once consumed; a stream/log can be re-read). "Real-time" isn't
  the deciding factor for Kinesis over SQS — ordering-per-key and multiple independent
  readers are. Ask which of those properties (competing workers vs fan-out vs replay vs
  per-key ordering) this actually needs before defaulting to whichever one is already
  familiar or already deployed elsewhere in the account.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `execution-model-decision.md` and `orchestration-and-failure-handling.md` in order once
the gate is satisfied. In short: name the unit of work and its duration/resource ceiling
(items 2–3) → rule primitives in or out by the hard limits (duration, custom runtime, local
state) before comparing on preference → decide the invocation model from the trigger and
response need (item 4: sync / async / poll-based event-source mapping) → decide whether
coordination needs a central orchestrator or tolerates choreography, and if steps hand off
via an event or message, which messaging technology actually fits — competing workers,
fan-out, replay, or per-key ordering (item 6) → if
orchestrated, assign each step's compute primitive and design its Retry (interval, backoff
rate, max attempts, which error types) and Catch (which failures route where) individually —
never on Choice/Pass/Wait/Succeed states, which don't call anything fallible → design the
DLQ/failure-destination for what's exhausted, and confirm idempotency for anything that can
be retried or delivered more than once (item 7) → name the concurrency ceiling and cold-start
tolerance → recommend and record.

Reference files:

- `execution-model-decision.md` — the FaaS vs container-task vs long-running-service decision
  table (duration, statefulness, cold start, concurrency/scaling model, ops burden); the three
  invocation models (synchronous, asynchronous, poll-based event-source mapping) and each
  one's built-in retry and error-handling behavior; the real cost of synchronous
  function-to-function chaining; the messaging-technology decision (queue vs pub/sub vs
  stream/log) for what carries an event or message between steps.
- `orchestration-and-failure-handling.md` — orchestration (state machine) vs choreography
  (event-driven) tradeoffs and when each earns its cost; Step Functions state types and which
  ones can carry `Retry`/`Catch` and why (Task, Parallel, Map — they call something fallible;
  not Choice, Pass, Wait, Succeed, Fail — they don't); hard failures (terminal — timeout,
  unhandled exception) vs soft failures (retryable — throttling, transient service errors);
  Parallel/Map fan-out failure semantics and the Distributed Map option for large-scale
  tolerated-failure fan-out; dead-letter-queue and failure-destination mechanics across
  Lambda async invocations, SQS-triggered functions, and Step Functions; the idempotency
  requirement that any retry or at-least-once delivery model imposes.

---

## Output

**1. In chat, a recommendation block:**

```
Unit of work:        <the operation from gate item 2, its trigger, and whether it's one step or several>
Compute primitive:   <FaaS (Lambda) | container task (Fargate/ECS) | long-running service> — ruled in/out by duration & resource profile (item 3)
Invocation model:    <synchronous | asynchronous | poll-based event-source mapping> — from the trigger & response need (item 4)
Orchestration:       <state machine, naming the coordination need it serves | event-driven choreography, naming the coupling tradeoff accepted | none — single step>
Messaging technology: <queue (competing workers) | pub/sub (fan-out) | stream/log (replay, per-key ordering) | ingest-to-destination | n/a — direct call or single step, with which property (fan-out/replay/ordering) drove the pick>
Retry & catch:       <per step/state: max attempts, backoff, which error types retried vs caught vs left terminal>
DLQ / failure dest.: <where exhausted attempts go, who's notified, and the idempotency requirement this imposes>
Concurrency & scaling: <max concurrent executions, cold-start tolerance, provisioned concurrency if needed>
Tradeoffs accepted:  <2–4 concrete costs: orchestration overhead, choreography's lost central visibility, cold starts, cost-per-invocation vs always-on>
Not chosen because:  <one line per rejected primitive/mechanism>
Follow-ups:          <execution role → cloud-iam-boundary; overload/retry-budget on a live path → resilience-strategy; dollar cost → technical-cost-decision; concurrency numbers → capacity-estimation; execution-failure alerting → observability-strategy>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using
`database-architecture`'s `adr-template.md` (same directory and numbering). Reference any
related `cloud-iam-boundary`, `microservices-decision`, or `resilience-strategy` ADR. Fill
"Revisit when" with a concrete trigger — "duration grows past the FaaS ceiling", "a second,
meaningfully branching path is added to what was a linear chain (reconsider orchestration)",
"the DLQ starts filling faster than someone is triaging it", "concurrency needs exceed the
account's default limits".

Then stop. Implementation — the state machine definition, the IaC, the handler code — is a
separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the unit of work named, duration and resource limits
checked against the platform ceilings, the invocation model and orchestration need decided
against a real coordination requirement, and the failure/idempotency contract thought through
— and wants a review or a tie-break rather than a Socratic pass, they say so and you give a
direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "When a video is uploaded to S3 we need to: transcode it (takes 3–8 minutes depending on
> length, uses ffmpeg, needs real CPU), generate a thumbnail (a few seconds), and update the
> record in DynamoDB, then notify the user by email. If transcoding fails we want it retried
> twice with backoff, and if it still fails a human should look at it — that queue is checked
> a few times a day, not paged. Thumbnail and DynamoDB update can happen in parallel with
> transcoding. Nobody's waiting synchronously for this — the user gets a 'processing' status
> immediately and finds out later. We don't have an event bus or orchestrator yet."

Gate satisfied. Unit of work: multi-step, S3-triggered, no synchronous caller. Duration:
transcoding (3–8 min, CPU-heavy) rules out a plain short-lived Lambda for that one step —
either a longer-running Lambda near its ceiling with a memory bump for more CPU, or a Fargate
task if it can run past 15 minutes; thumbnail and DynamoDB update are both well within Lambda's
profile. Invocation: asynchronous end-to-end (S3 event trigger, no caller waiting). Given
three steps with real coordination (parallel thumbnail+transcode, then a join before
notification, plus a distinct failure path with different urgency for transcoding) — an
orchestrator earns its cost here (item 6): Step Functions, `Parallel` state for
thumbnail-generation + transcoding, `Retry` on the transcode Task (2 attempts, exponential
backoff) `Catch`-ing to a `NotifyOpsForReview` state feeding a low-urgency (ticket, not page)
DLQ, then a join into the DynamoDB-update-and-notify step. Idempotency: the DynamoDB update
should be a conditional/idempotent write since a retried transcode could otherwise trigger a
duplicate notification. Concurrency: bound by expected upload rate → `capacity-estimation` if
not yet sized. Follow-ups: execution roles for the transcode task and the two Lambdas →
`cloud-iam-boundary`; DLQ-checked-a-few-times-a-day alert → `observability-strategy`. ADR;
revisit when a second failure path needs different urgency, or transcoding needs GPU (moves
it further from Lambda toward a dedicated Fargate/EC2 profile).

> "Should we use Lambda or Fargate for our API?"

Gate not satisfied — item 2 (which operation — the whole API, or one endpoint?), item 3
(duration/resource profile unstated), item 5 (concurrency/burst pattern and cold-start
tolerance unstated). Response: ask what a typical request does and how long it takes, whether
traffic is bursty or steady, and whether occasional cold-start latency on this path is
acceptable to end users — those three answers, not a general preference, decide it. Do not
recommend a primitive.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other
architecture skills, reusing `database-architecture`'s `adr-template.md`. Written from AWS
vocabulary (Lambda, Fargate, Step Functions, SQS/Kinesis event-source mapping) but the gate
items and decision structure transfer to Azure Functions/Container Apps/Durable Functions or
GCP Cloud Functions/Cloud Run/Workflows — swap the platform-specific limits and mechanics in
the reference files if this repo targets a different cloud. Copy the
`serverless-execution-model/` directory into another repo's `.claude/skills/` to use it there.
