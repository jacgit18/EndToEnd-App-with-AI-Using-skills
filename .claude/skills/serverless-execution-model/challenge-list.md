# Serverless Execution Model — challenging a proposed approach

Read when the user opens with a mechanism already chosen.

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
