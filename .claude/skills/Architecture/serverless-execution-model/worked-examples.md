# Serverless Execution Model — example invocations

Read to calibrate a response.

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
