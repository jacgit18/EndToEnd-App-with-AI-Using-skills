# Orchestration and Failure Handling

The coordination and failure-contract mechanics behind gate items 6–7 in `SKILL.md`. Written
around AWS Step Functions' Amazon States Language (ASL), since that's the concrete example
most teams reach for; the orchestration-vs-choreography tradeoff itself is platform-agnostic.

## Orchestration vs choreography

| | Orchestration (a central state machine) | Choreography (event-driven reaction) |
|---|---|---|
| **Where the process definition lives** | One place — the state machine definition | Nowhere — it's implicit in which service listens for which event |
| **"Where is this instance right now?"** | Answerable directly — the orchestrator has execution state | Requires reconstructing the trail from logs/traces across every service involved |
| **Branching, parallel fan-out, wait-for-callback** | Native support (`Choice`, `Parallel`, `Map`, `.waitForTaskToken`) | Possible but requires each service to carry its own state about what it's waiting for |
| **Coupling** | Every step is coupled to the orchestrator's definition (not directly to each other) | Steps are decoupled from each other, coupled only to an event's shape |
| **Adding a new step** | Edit one definition | Add a new listener; existing services don't need to change |
| **Extra infrastructure** | The orchestrator itself (a real, billed, operated piece of infrastructure) | None beyond the event bus/queue already needed for the events |
| **Failure visibility** | The orchestrator's own execution history typically shows exactly which step failed and why | Failure is only visible to whichever service noticed it; requires distributed tracing to reconstruct |

**Decision rule** (gate item 6): reach for orchestration when there is real coordination
need — branching logic, parallel steps that must join, a wait for an external callback or
human approval, or a genuine operational requirement to answer "where is process X right
now" without archaeology. Reach for choreography when steps are a straight, non-branching
sequence, or when the explicit goal is loose coupling and independent deployability between
services that don't need a shared view of overall progress — and say out loud that debugging
a stuck process now means tracing across services, which is the cost being accepted.

Don't reach for either by default. A single linear chain of two steps gains nothing from a
state machine over one function calling the next directly or firing an event the next step
picks up; a process with three branching outcomes and a human-approval wait gains real
correctness and visibility from an orchestrator that ad hoc event-passing would have to
reinvent badly.

## Step Functions state types and where Retry/Catch apply

| Type | Purpose | Can carry `Retry`/`Catch`? | Why |
|---|---|---|---|
| **Task** | Executes a unit of work (a Lambda, an ECS task, a direct AWS SDK integration) | Yes | It calls something external that can genuinely fail (throttled, timed out, errored) |
| **Parallel** | Runs its branches concurrently | Yes | The branches it runs can fail |
| **Map** | Applies a set of steps to each item in a collection | Yes | Same reason as Parallel, at scale |
| **Choice** | Branches based on a condition | **No** | It only evaluates data already in hand — there's no external call to fail. If validation needs to fail safely, put the fallible check in a preceding `Task` with its own `Catch`, then branch on the result in the `Choice` that follows |
| **Pass** | Passes or transforms data without calling anything | No | Nothing to fail |
| **Wait** | Pauses for a duration or until a timestamp | No | Nothing to fail |
| **Succeed** / **Fail** | Terminal states | No | Already the end of the line |

The source material this reference replaces treated the Choice-can't-Catch restriction as an
isolated API quirk; the actual reason is structural and applies to every non-Task/Parallel/Map
state — none of them invoke anything that can throw. Keep the fallible operation in a Task
upstream of any Choice, Pass, or Wait that depends on its result.

**The data passed between states is itself a contract, not just the control flow.** Step
Functions moves data between states via JSONPath (`InputPath`, `ResultPath`, `OutputPath` —
`$.foo.bar` addressing into the JSON blob), and a state's output shape has to match what the
next state's `Task` parameters or `Choice` conditions expect. A field renamed, nested one
level differently, or a type changed (string where a number was expected) doesn't fail loudly
at the point of the mistake — it produces a runtime `States.Runtime` or a `Choice` silently
taking the wrong branch, often several states downstream of the actual defect. Treat each
state's input/output shape as a versioned contract the same way a REST/GraphQL API boundary
is one: define it, and validate a Task's output against it in that Task's own code before
returning, rather than discovering the mismatch two states later.

## Hard failures vs soft failures

- **Hard (terminal) failures** — `States.Timeout`, an unhandled exception, a malformed
  input the code can't recover from. These stop execution immediately unless caught. Always
  give a Task doing anything non-trivial a `Catch` routing to a defined failure/cleanup state
  — an uncaught hard failure just stops, with no notification unless something else is
  watching the execution-failed metric.
- **Soft (retryable) failures** — throttling (`Lambda.TooManyRequestsException`,
  `DynamoDB.ThrottlingException`), transient service exceptions, network blips. These are
  what `Retry` is for: an `IntervalSeconds`, `MaxAttempts`, and `BackoffRate` (exponential
  backoff — reuse `resilience-strategy`'s backoff-with-jitter framing rather than a fixed
  interval, since a fixed retry interval across many concurrent failed invocations recreates
  the retry-storm problem that skill names) per error type. Retry only errors that are
  actually transient — retrying a validation error or a 4xx-equivalent just delays reaching
  the same failure.

Classify each Task's realistic failure modes into these two buckets explicitly (gate item 7)
rather than either catching everything the same way or retrying everything indefinitely.

## Parallel and Map fan-out failure semantics

By default, a `Parallel` or `Map` state **fails entirely if any single branch/iteration
fails**, and every other branch — including ones that already finished successfully — is
stopped or its result discarded. This is rarely what's wanted when branches are independent:

- **Catch inside each branch** so one branch's failure produces a recorded result (an error
  object) rather than aborting the whole state, and downstream logic decides what to do with
  a partial result set.
- **Distributed Map** (for large-scale fan-out, up to tens of thousands of items) supports a
  **tolerated failure percentage/count** — a defined fraction of items can fail without
  failing the whole Map, which is the mechanism for "process what you can, flag the rest"
  at scale rather than all-or-nothing.

Ask explicitly whether partial success is meaningful for this fan-out (gate item 7) before
accepting the default all-or-nothing behavior.

## Dead-letter queues, failure destinations, and idempotency

| Mechanism | Where it applies | What triggers it |
|---|---|---|
| **Lambda asynchronous failure destination** | Async-invoked Lambda | Exhausted the platform's automatic retries (2 retries, 3 attempts total) |
| **SQS dead-letter queue** | A queue (including one an SQS-triggered Lambda consumes) | A message's receive count exceeds the queue's configured `maxReceiveCount` (a redrive policy) |
| **Step Functions `Fail` state / execution-failed** | A state machine execution | An unhandled error after all `Retry`/`Catch` options are exhausted |

Whichever mechanism applies, a DLQ or failure destination is not the end of the design — it
needs an owner and a cadence (gate item 10 territory, handed to `observability-strategy`:
paged immediately, or checked on a schedule, depending on how urgent an exhausted failure
actually is) and, critically, it needs **idempotency** on whatever eventually reprocesses
those messages. Any mechanism that can redeliver or retry — async retries, SQS redelivery,
Kinesis/DynamoDB Streams retry, a human manually replaying a DLQ message — implies
**at-least-once** delivery, not exactly-once. If the operation isn't naturally idempotent
(an unconditional "charge the card," "send the email," "increment the counter"), add an
idempotency key or a conditional write before relying on any retry mechanism — otherwise the
failure-handling design that was supposed to make the system more reliable produces
duplicate side effects instead.

A caution on function-to-function chaining: nothing here recommends against Lambda calling
another Lambda in general — an asynchronous or event-mediated handoff between two functions
is a normal, sound pattern. The specific thing worth designing around is a **synchronous**
chain of functions invoking each other and waiting, which stacks cold starts, compounds
timeouts, multiplies invocation cost per hop, and creates a coupling where a duration or
contract change three hops downstream silently breaks the entry point's timeout budget. Use
`execution-model-decision.md`'s synchronous-invocation section for that specific case.
