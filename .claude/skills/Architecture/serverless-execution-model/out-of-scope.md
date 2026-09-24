# Serverless Execution Model — out-of-scope hand-offs (full)

Full reasoning behind the one-line summary in `SKILL.md`.

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
