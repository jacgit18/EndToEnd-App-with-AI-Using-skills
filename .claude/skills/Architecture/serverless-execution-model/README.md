# serverless-execution-model skill

A gated decision for **how one unit of work actually runs** — the compute primitive (FaaS /
container task / long-running service), the invocation model (sync / async / poll-based),
whether a multi-step process needs a central orchestrator or tolerates event-driven
choreography, the messaging technology that carries an event between choreographed steps
(queue / pub-sub / stream-log), and the failure contract (retry/backoff, catch routing,
DLQ/failure destination, idempotency). Not service boundaries or team ownership (that's
`microservices-decision`), not the execution role or network placement (that's
`cloud-iam-boundary`), not overload/cascade defense on a live path (that's
`resilience-strategy`), not dollar cost (that's `technical-cost-decision`).

Built from the `Architecture/02. Backing Service Options/Cloud/` notes — `Lambda vs
Fargate.md`, `Microservices vs FaaS.md`, `Lambda Invocation Models.md`, `AWS/AWS Async Vs
Sync.md`, `AWS/Step function.md`, `AWS/Step Function Extension.md`, `Step Function Catch
Blocks.md`, `Failure States.md`, `AWS Parallel State.md`, `AWS/DLQ.md`, `AWS/DLQ
Drainer.md`, `AWS/AWS SQS.md`, `AWS/Amazon Kinesis Data Streams vs Amazon Kinesis Data
Firehose.md`, `Scalable Messaging Architecture.md` (the SNS-fanning-out-to-per-consumer-SQS
pattern), and `Qsink.md` (the general sink/stream-consumer vocabulary, used to frame Firehose
as an ingest-to-destination sink with no custom processing step).

Also added `2026-09-04` (second pass, closing a gap noted in `SKILL-BACKLOG.md`): the
state-to-state data-contract note in `orchestration-and-failure-handling.md`, from `Req and
RES.md`'s point about JSONPath data flow between Step Functions states being a contract like
any API boundary.

Note: `Lambda Invocation.md` in the same folder is about generic programming-language lambda
expressions (Python/JavaScript closures), not AWS Lambda invocation — it was not used as a
source here despite the name; don't confuse the two when re-reading the vault notes.

## Where it sits

```
microservices-decision     →  how many services, team ownership (assumed given, upstream of this skill)
capacity-estimation        →  concurrency / volume numbers this skill consumes
serverless-execution-model →  compute primitive + invocation model + orchestration + messaging technology + failure contract   (this skill)  → ADR
cloud-iam-boundary          →  the execution role and network placement this workload needs
resilience-strategy        →  overload/cascade retry-budget on a live request path (composes with this skill's per-invocation retry contract)
technical-cost-decision    →  the dollar cost of the chosen primitive/concurrency
observability-strategy     →  alerting on execution failures and a filling DLQ
```

## The shape

A gate skill. It refuses to recommend a primitive or orchestration approach until the user
supplies:

- **the unit of work** — one request, one event-triggered side effect, a multi-step process,
  a stream to consume — not "a backend thing"
- **duration and resource profile** — checked against hard platform ceilings before anything
  is compared on preference
- **trigger and response need** — does the caller need to wait
- **concurrency and burst pattern**, including cold-start tolerance
- **whether steps need central coordination** or can tolerate independent event reaction, and
  if so what property (competing workers, fan-out, replay, per-key ordering) the handoff
  between them actually needs
- **failure semantics** — retry vs park vs drop, and whether the operation is idempotent

Then it rules primitives in/out by hard limits, picks the invocation model from the
trigger/response need, decides orchestration vs choreography by the coordination need (not by
default in either direction), picks the messaging technology from the property actually
needed rather than whichever is already deployed, assigns per-step Retry/Catch only where
something fallible is actually called (Task/Parallel/Map, never Choice/Pass/Wait), and
designs the DLQ/failure destination plus the idempotency requirement it imposes.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 2–8 from the user), challenge-the-proposal, output contract. |
| `execution-model-decision.md` | FaaS vs container-task vs long-running-service decision table; the three invocation models (sync, async, poll-based event-source mapping) and each one's built-in retry/error behavior; the cost of synchronous function-to-function chaining; the messaging-technology decision table (queue vs pub/sub vs stream/log vs ingest-to-destination) for what carries an event between choreographed steps. |
| `orchestration-and-failure-handling.md` | Orchestration vs choreography tradeoff; Step Functions state types and which can carry Retry/Catch and why; hard vs soft failure classification; Parallel/Map fan-out failure semantics and Distributed Map's tolerated-failure option; DLQ/failure-destination mechanics and the idempotency requirement retries impose. |

## Output

1. A recommendation block in chat (unit of work, compute primitive, invocation model,
   orchestration decision, retry & catch per step, DLQ/failure destination, concurrency &
   scaling, tradeoffs, follow-ups).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (duration grows past the FaaS
   ceiling, a linear chain gains real branching and needs reconsidering as orchestrated, the
   DLQ fills faster than it's triaged, concurrency needs exceed account limits).

Stops before implementation (the state machine definition, IaC, handler code).

## Interaction with sibling skills

- **Assumes `microservices-decision`'s output** — takes one already-scoped unit of work as
  given; does not decide whether it should be its own service. Reciprocal pointer added
  there ("what compute primitive runs one already-scoped service").
- **Hands off to `cloud-iam-boundary`** — this skill names what a Task/function needs to call;
  that skill designs the role and network placement. The two are typically worked together
  when standing up a new workload; `skill-interaction-testing` confirmed this composes as a
  clean hand-off with no duplicate questions.
- **Composes with `resilience-strategy`** — that skill's retry-budget-under-load concern and
  this skill's per-invocation retry/DLQ contract are different questions that share
  vocabulary ("retry with backoff"); an async worker built here can still need a concurrency
  limit from that skill if its retries are hammering an overwhelmed downstream. Confirmed
  clean chaining under test; a disambiguating clause was added to this skill's description so
  entry point isn't a coin-flip between the two trigger phrasings.
- **Feeds `technical-cost-decision`** — the chosen primitive and concurrency ceiling are the
  usage-driver inputs; this skill doesn't price them. `skill-interaction-testing` found the
  hand-off worked only because of an exact phrase match ("Lambda vs Fargate"); fixed by
  widening `technical-cost-decision`'s description to route any bare primitive-cost question
  through this skill's fit gate first, regardless of phrasing.
- **Consumes `capacity-estimation`** — concurrency and volume numbers, rather than re-deriving
  them.
- **Feeds `observability-strategy`** — the DLQ-triage cadence and execution-failure alert
  requirement are named here, designed there.
- **Hands off to `data-tier-operations`** — a poll-based consumer's poison-pill/redrive
  handling stays here; only a genuinely hot partition/shard key moves to that skill.
  Reciprocal pointer added both ways.
- **Defers to `design-scoping`** for an unscoped, not-yet-designed system.
- **Absorbed by `deployment-strategy`** for rollout-mechanism questions (canary/blue-green) —
  confirmed no overlap; this skill has no rollout vocabulary and correctly doesn't fire.

Fixed after `skill-interaction-testing` (2026-09-04, see
`skill-interaction-cloud-iam-and-serverless-execution.md`): the frontmatter's bare "Lambda vs
Fargate" trigger phrase risked firing the full gate on a pure conceptual comparison with no
named workload — qualified the phrase and added an explicit "answered directly, no gate" carve-out
for bare comparisons.

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside
`database-architecture` and reuses its `adr-template.md`. Written in AWS vocabulary (Lambda,
Fargate, Step Functions, SQS/Kinesis); swap the platform-specific limits and mechanics in the
reference files for Azure Functions/Container Apps/Durable Functions or GCP Cloud
Functions/Cloud Run/Workflows if this repo targets a different cloud — the gate items and
decision structure carry over unchanged.

```
cp -r ".claude/skills/Architecture/serverless-execution-model" /path/to/other-repo/.claude/skills/
```
