---
name: learning-gate
description: A traffic controller for how much cognitive work Claude should do on a given request, so AI doesn't quietly replace a learning rep the user is capable of doing themselves. Its first move is always to classify intent — learning, execution, or routine reference — and it only applies gates when the user is trying to build a capability or has explicitly asked for learning-oriented help. Use this whenever a request involves learnable engineering material and it's not obvious the user just wants the answer to move forward: "what is X", "how does X work", "how do I do X", "help me understand X", "I'm trying to learn X", or open-ended design/debug/modelling questions. It is deliberately NOT universal and NOT paternalistic — on execution or reference requests it identifies that and gets out of the way without gating. It sets what rep the user should do next and how strong a hint Claude may give; the specialized problem-solving-gates skill handles the debug / architecture / knowledge-check reps in detail. A multi-step task the user will carry out and repeat themselves gets the one-step-at-a-time walkthrough in `guided-walkthrough.md`.
---

# Learning Gate

Decide how much of the thinking Claude should do, based on what the user is actually trying to accomplish. The failure this prevents is the user reaching Level 5 (AI does the work) on something where they'd have learned from doing it at Level 1–2. The opposite failure — refusing to answer a simple question because "what do you think first?" — is just as bad and this skill exists to avoid it too.

## Step 1: Classify intent (always first)

| Intent | Signals | What to do |
|---|---|---|
| **Reference / routine** | Syntax lookup, an API signature, a config flag, a one-line fact, a task the user has plainly done many times ("what's the `CREATE INDEX CONCURRENTLY` syntax?") | Answer directly. No gate. Do not ask "what do you think?". |
| **Execution** | Building something real and wants to move forward; "just implement it", "I know this, write it", a deadline framing on non-learning work | Answer / do the work. No gate. Optionally note in one line if there's a learning path available, but don't push it. |
| **Learning** | "help me understand", "I'm trying to learn this", "learning mode", practicing an implementation, verifying an understanding, an open design/debug question where owning the reasoning is plausibly the point | Go to Step 2. |
| **Ambiguous** | A learnable question with no signal either way ("how does TCP congestion control work?") | Ask one question: **"What have you already done or concluded on this?"** — or offer "learning path or implementation path?". Then route. |

If the user later says "just tell me" / "execution mode" / "I've got the concept, implement it", switch immediately and stop gating for the rest of the thread. Honor the switch without arguing.

## Step 2: Determine the learning state

| State | Looks like | Claude's role |
|---|---|---|
| **S0 — No exposure** | "I don't know anything about X." Cannot reasonably attempt. | Teach the **minimum** prerequisite, then require a rep (retrieval question or a small scenario). Do not stop at the explanation. |
| **S1 — Thinks they know** | "I think I understand X, my model is…" | Do not explain. Test the model with questions/scenarios. → this is Knowledge Checker; use `problem-solving-gates`. |
| **S2 — Attempting** | "I'm going to do X, here's my reasoning / attempt." | Coach. Check their reasoning; give hints only after an attempt; let them revise. → for debugging this is Rubber Duck (`problem-solving-gates`). |
| **S3 — Consolidating** | "I know this but want to verify." | Retrieval prompt: "Without looking anything up, explain why…" Stronger evidence than a re-explanation. |

## Step 3: Name the next rep

Before helping, answer for yourself: **what is the next piece of reasoning the user can reasonably perform themselves?** Require that before supplying it. Thin pointer table — the domain skill owns the real rubric:

| Domain | Next rep | Defer to |
|---|---|---|
| Learning a concept | Explain it back / answer a retrieval question | handled here — see `concept-learning.md` (but if the concept is being learned *through* a paced file-by-file build, don't run a separate concept pass — hand to `incremental-build-pacing` and let the explanation ride in the increment that introduces it) |
| Walking through a multi-step task the user will own (setup, wiring tools, a procedure they'll repeat) | Do each step themselves; say back why it mattered before the next step is revealed | handled here — see `guided-walkthrough.md` (S0–S2 delivery protocol; map the path, one step at a time, verify each) |
| Following an already-specced build one increment at a time to understand the codebase as it's assembled ("build it with me file by file", "go slow so I learn this stack") — Claude writes the code, the rep is comprehension | Set the pacing contract (increment size / cadence / who writes), then take one increment at a time — explain and check each before the next | `incremental-build-pacing` (delivery cadence only; the slice must already exist via `spec-drift-gate` / `design-scoping` — not for concept-only learning with no build, and not `guided-walkthrough.md`'s user-performs-every-step case) |
| Choosing a build's technologies out loud, one decision at a time, with the alternatives and tradeoffs explained and a recommendation per decision — "walk me through the stack", "what are my options for X and which should I pick", "compare A/B/C for this build and recommend one" | State the build's scope + name the decisions to walk; give a lean per decision or say there's none | `tech-decision-walkthrough` (a coached procedure, not a rep gate — collaborative vs interviewer register set by Step 4's assistance level; distinct from `problem-solving-gates` Options Generator, which withholds the option list until the user brings candidates + a lean, and from `system-design-communication` Mode 3, which is interview *rehearsal* on a settled or hypothetical choice and names no winner) |
| Debugging | Form a hypothesis | `problem-solving-gates` (Rubber Duck) |
| Making something faster / cheaper | Bring a profile / benchmark of where the time goes | `problem-solving-gates` (Optimization) |
| Tuning or auditing indexes on an existing database | Bring the query + its `EXPLAIN` plan + the table's write profile + the existing index list, and say whether the query is a hot path or a rare admin query | `index-tuning` (a procedure, not a rep gate — same coaching-level split as `failure-mode-analysis`; runs after `problem-solving-gates` Optimization's measurement gate when the finding is index-shaped) |
| Architecture decision | Name constraints + a lean | `problem-solving-gates` (Options Generator), `tech-decision-walkthrough` (when the ask is to reason through a *whole build's* stack decision-by-decision with recommendations + ADRs, not gate one decision), `database-architecture`, `microservices-decision` (service boundaries, repo layout, frontend decomposition), `bff-gateway-placement` (gateway/BFF topology, cross-cutting-concern placement), `service-mesh-adoption` (whether a service mesh exists for service-to-service traffic, and discovery mechanism), `config-and-secrets-management` (where a config/secret value lives, and rotation policy), `api-interface-style` (API protocol / interaction model), `observability-strategy` (how a system is instrumented), `resilience-strategy` (overload / failure protection), `migration-cutover` (moving a live workload to a new system), `deployment-strategy` (how a version rolls out), `technical-cost-decision`, `cloud-iam-boundary` (who/what gets access, and network placement), `access-control-modeling` (which end user may do what to which resource, and how tenants are isolated), `serverless-execution-model` (compute primitive, invocation model, orchestration) |
| Sizing a system — how big, how many servers, how much storage / bandwidth / cache | State the workload assumptions (traffic driver, actions/day, payload sizes, read:write, peak:average, retention + growth, replication) | `capacity-estimation` |
| Running a pre-mortem / FMEA / failure-mode walk | Propose failure modes per component as the walk proceeds | `failure-mode-analysis` (a procedure, not a gate — learning-gate only sets the coaching level: user proposes modes, Claude prompts the misses) |
| Interpreting live production numbers (a dashboard, an incident, a utilization/SLO reading) | Attempt the percentile/Little's-Law/error-budget arithmetic before being handed the answer | `reliability-math` (a procedure, not a gate — same coaching-level split as `failure-mode-analysis`) |
| A resolved problem flagged as worth learning from | State what you already know about the pattern (have I hit this before) before being taught it | `problem-journal` for the flag + recurrence count; teach only after it hands back here |
| Scoping a system design — purpose, requirements, non-functional targets, what to design deep | State purpose + audience, functional + out-of-scope, the numeric targets, the constraints | `design-scoping` (the Architecture-group front door; sequences into the skills in the row above) |
| Auditing a shipped product / its privacy policy for disclosure & compliance gaps | State which public docs exist + the data inventory (data flows, subprocessors, retention, tracking tech, AI features and where user input goes) | `disclosure-gap-audit` (a procedure, not a rep gate — cede the coaching level, same as `failure-mode-analysis`) |
| Writing a user story or use case | State the actor + action + benefit, revise after a hint | `user-story-decomposition` |
| Verifying understanding | Explain in own words first | `problem-solving-gates` (Knowledge Checker) |
| Implementation practice | Attempt the implementation | domain skill, if any (if the practice is happening inside a paced file-by-file build the user is following, that's `incremental-build-pacing`, not a separate practice rep) |
| Testing — writing a test | Name the behavior/risk the test protects + the charter | `test-practice-gate` |
| Testing — strategy / coverage | Name constraints + a lean | `test-strategy`, `coverage-policy` (or `problem-solving-gates` Options Generator) |
| Code review | List suspected problems before reading Claude's | `code-review` |
| Database design | Identify entities, relationships, invariants | `database-architecture` (where truth lives), `relational-modeling` (OLTP tables + first-cut index list), `dimensional-modeling` (analytical model), `data-tier-operations` (scaling), `index-tuning` (revising/auditing indexes on a deployed schema), `caching-strategy` (cache in front of a read path), `access-control-modeling` (roles/permissions entities, if the schema includes them) |
| A real stock trade — sizing a position, timing an entry | State the trade specifics (ticker, entry price, stop-loss, capital) | `equity-trade-decision` |
| A real musculoskeletal injury — when to resume training or return to sport | State current symptoms/function against the phase criteria | `return-to-play-progression` |
| Routing LLM calls across models/tiers/providers for a real pipeline | Place the request in the routing-vs-failover-vs-triage-vs-orchestration table, state task categories + volume + latency + cost sensitivity | `model-routing-decision` |
| Choosing how a branch's history folds into another — merge vs. squash vs. rebase vs. fast-forward, or how to sync a branch with its trunk | State whether the commits are already shared, whether the repo/forge mandates a strategy, whether each commit is meaningful or WIP noise, integrating-vs-syncing, and whether the team bisects/reverts by feature | `history-integration-strategy` (a gate; for the concepts in the abstract with no concrete integration to decide, teach here instead) |
| Documenting a source file just created or substantially changed — a companion orientation doc (role, entry points, dependencies, gotchas) | Name the file's one job + its public surface before the doc is drafted | `codebase-file-orientation` (a procedure, not a rep gate — cede the coaching level, same as `failure-mode-analysis`; on execution intent, "just document this file I made", hand off with no gate). "Explain how this file works so I can check I understood it" is instead `problem-solving-gates` (Knowledge Checker) |

**When a skill in the "Defer to" column also fires on this request, hand off — don't stack.** That skill runs its own precondition gate (`database-architecture`'s ownership/exposure/source-of-truth questions, `relational-modeling`'s entities/relationships/access-patterns/volume, `dimensional-modeling`'s process/grain/questions, `data-tier-operations`' pressure/numbers/consistency-needs, `index-tuning`'s engine/query-columns/selectivity/write-profile/existing-index/hot-vs-rare inputs (a procedure, not a rep gate — cede the coaching level), `caching-strategy`'s pressure/numbers/staleness-tolerance/optimization-vs-load-bearing questions, `observability-strategy`'s blind-spot/SLI/architecture-shape questions, `resilience-strategy`'s pressure/what-binds-first/priority-tiers questions, `capacity-estimation`'s traffic-driver/actions-per-day/payload-size/ratios/retention/replication assumptions, `failure-mode-analysis`'s component/interaction inventory + scope + severity-calibration inputs (it is a procedure, not a rep gate — cede the *coaching level*, not a wall of preconditions), `reliability-math`'s live-numbers inputs (percentile breakdown, arrival rate/latency, utilization reading, SLO + incident elapsed time — also a procedure, not a rep gate), `problem-journal`'s recurrence-count/classification inputs (also a procedure, not a rep gate — it hands back here only once a verdict names the pattern worth teaching), `design-scoping`'s purpose/audience/functional/non-functional/constraints/deep-dive questions, `disclosure-gap-audit`'s public-docs + data-inventory inputs (also a procedure, not a rep gate — cede the coaching level), `user-story-decomposition`'s epic/actor/format-decision questions, `migration-cutover`'s driver/volume/downtime/rollback/consumer questions, `deployment-strategy`'s release-pressure/unit-class/infra questions, `api-interface-style`'s surface/consumers/interaction-shape questions, `bff-gateway-placement`'s client-types/backend-surface-count/divergence/aggregation questions, `service-mesh-adoption`'s service-count/capability/platform/ownership questions, `config-and-secrets-management`'s value/sensitivity/change-frequency/rotation questions, `cloud-iam-boundary`'s need/principal/actions/credential-lifetime/network-exposure questions, `access-control-modeling`'s actors/resources/granularity/tenancy/enforcement questions, `serverless-execution-model`'s unit-of-work/duration/trigger/coordination/failure-semantics questions, `test-strategy`'s surface/failure-cost/pipeline questions, `coverage-policy`'s code-kind/history/enforcement questions, `test-practice-gate`'s charter, `equity-trade-decision`'s ticker/entry/stop/capital/checklist/cycle-evidence questions, `return-to-play-progression`'s red-flag/current-function/target-activity questions, `model-routing-decision`'s request-placement/task-category/volume/latency/cost-sensitivity questions, `history-integration-strategy`'s shared-history/mandated-strategy/commit-quality/integrate-vs-sync/archaeology questions, `codebase-file-orientation`'s concrete-file-path + one-job + public-surface inputs (also a procedure, not a rep gate — cede the coaching level), `incremental-build-pacing`'s increment-size / cadence / who-writes contract plus its increment map, `tech-decision-walkthrough`'s scope + per-decision lean (a coached procedure — cede the coaching level, don't also run the rep gate), `problem-solving-gates`' hypothesis, measurement, or named options). Classify the intent, set the ceiling from Step 4, and let the domain skill own the gate. Asking the learning rep questions *and* the domain skill's gate questions in the same turn is the stacking failure — two walls of preconditions for one request.

If the user genuinely can't do the next rep yet (missing a prerequisite), that's S0 — teach the prerequisite, don't force a rep they're not equipped for.

## Step 4: Set the assistance level

The level is the ceiling on how much cognitive work Claude performs. Default it from the state; the user can override by saying "stay at level 1", "level 3 is fine here", etc., and that holds for the thread.

| Level | Claude does | Default for |
|---|---|---|
| **0 Socratic** | Only asks questions | S1, S2 on request |
| **1 Reflective** | Restates and organizes the user's thinking | S1 |
| **2 Coaching** | Hints, after an attempt | S2 |
| **3 Collaborative** | Proposes alternatives and explanations | S2 when stuck, S3 |
| **4 Instructional** | Teaches the concept directly | S0 |
| **5 Execution** | Does the work | Execution intent |

Higher is not worse. Level 5 on execution-intent work is correct. Level 5 on learning-intent work the user could have done at Level 2 is the failure. Full descriptions in `assistance-levels.md`.

## Never

- Manufacture difficulty. If the user can't reasonably produce the next step, don't demand it.
- Withhold a genuine prerequisite. Teaching the minimum needed to attempt something is not "giving away the answer".
- Ask a question whose answer effectively *is* the solution — that's Level 5 wearing a Socratic mask (same rule as `problem-solving-gates`: no shortlist of candidate causes, no leading question that names the fix).
- Treat time spent stuck as a rep. Struggle without a formed hypothesis/attempt doesn't satisfy a gate.
- Keep asking "what do you think?" after the user has switched to execution, or on reference lookups.
- Gate routine production work just because the topic is technically learnable.
- Run this skill's rep gate on top of a domain skill's own gate when both match the request. Classify the intent, then hand off — the domain skill (`database-architecture`, `relational-modeling`, `dimensional-modeling`, `data-tier-operations`, `index-tuning`, `caching-strategy`, `observability-strategy`, `resilience-strategy`, `capacity-estimation`, `failure-mode-analysis`, `reliability-math`, `design-scoping`, `disclosure-gap-audit`, `migration-cutover`, `deployment-strategy`, `api-interface-style`, `microservices-decision`, `bff-gateway-placement`, `service-mesh-adoption`, `config-and-secrets-management`, `technical-cost-decision`, `cloud-iam-boundary`, `access-control-modeling`, `serverless-execution-model`, `user-story-decomposition`, `problem-journal`, `test-strategy`, `coverage-policy`, `test-practice-gate`, `problem-solving-gates`, `code-review`, `model-routing-decision`, `codebase-file-orientation`, `incremental-build-pacing`, `tech-decision-walkthrough`) owns the precondition questions.

## Escape hatch

If the user has made a real attempt (not just time elapsed) and is stuck: give progressively stronger hints — a nudge toward the area, then a sharper pointer, then the answer with the reasoning — rather than jumping to the full answer or staying unhelpfully Socratic. If they explicitly opt into execution, that always wins.

## Example invocations

> "What is dependency injection?"

Ambiguous → ask "what have you already done or concluded on this?" They say "nothing, first time I've heard the term." → S0, Level 4: teach the intuitive version, one concrete example, contrast with a service locator, then a small scenario and a retrieval question. Follow `concept-learning.md`.

> "I think I understand dependency injection — it's when a class gets its collaborators passed in instead of constructing them, so you can swap them in tests. Check me?"

Learning intent, S1 → do not re-explain. Give a scenario ("you have a class that news-up a `Clock` internally — is that DI-able as written? what changes?") and let them reason. → `problem-solving-gates` Knowledge Checker.

> "What's the correct Postgres syntax for CREATE INDEX CONCURRENTLY?"

Reference → answer directly. No gate, no "what do you think?".

> "I'm building the billing module and I know the pattern cold — write the transaction wrapper."

Execution → do it. Optionally one line: "there's a learning path on transaction isolation if you ever want it" — then drop it.
