---
name: model-routing-decision
description: Gated decision for routing LLM calls across more than one model: tiering by task, choosing across providers, adopting a routing proxy, or in-session model choice. Triggers: "when should I use Haiku vs. Sonnet vs. Opus", "should I build a model router", "is a routing proxy worth it". Not for pricing tiers — `technical-cost-decision`. Not for volume sizing — `capacity-estimation`.
---

# Model Routing Decision

Most "should I route between models" conversations skip straight to a recommendation (usually "use OpenRouter" or "write a Haiku classifier") without checking that the request is actually a model-selection problem, and without any real numbers behind the tier table. This skill forces both: place the request correctly, then require the inputs that make an architecture recommendation defensible instead of a guess.

## Step 1 — Place the request

"Model routing" covers at least seven distinct things. Only some are this skill's job. Before recommending anything, say out loud which row the request is actually in:

| What's being asked | What it actually is | Owned by |
|---|---|---|
| Cheapest/fastest model that can still do the task, tiered by task type (classification/extraction → cheap model, analysis/drafting → mid model, complex multi-step reasoning → strongest model) | Model selection | This skill |
| Picking across *different companies'* models (Claude, GPT, Gemini), often through a proxy | Model selection + API normalization | This skill (name the added normalization/lock-in cost explicitly) |
| Within one agentic session, different sub-tasks get different models automatically (background/summarization → cheap, planning → strongest, long-context compaction → big-context model) | Model selection by function-in-workflow | This skill (a distinct axis from per-request complexity tiering — the two can coexist) |
| Routing decisions that adapt over time from observed outcomes rather than a fixed rule table | Model selection, adaptive | This skill, but name it as a maturity step layered on a working static router, not a v1 |
| If a call times out, errors, or hits a rate limit, retry on a different model or region | Availability / failover | **Not this skill.** It's a reliability pattern — motivation is uptime, not cost or capability match. Say so plainly and don't build a tier table for it. |
| Classify an incoming ticket/request (intent, urgency, department) and route it to the right downstream team or system | Ops/workflow triage | **Not this skill.** The classifier may be an LLM call, but the "routing" destination is a workflow or a human team, not another model. |
| Mid-session in Claude Code: which model/agent should run the step in front of us, or whether to escalate after a failure | Model selection, live | This skill, **In-session mode** below (skip Step 2's input gate only for a step in the current session; any request about a deployed or to-be-built system, however phrased, still goes through Step 2) |
| A lead agent delegates subtasks to specialized sub-agents | Multi-agent orchestration / labor division | **Not this skill.** That's an agent-architecture decision. Once the delegation structure exists, this skill can be reapplied to decide each sub-agent's own model. |

If the request lands in one of the **Not this skill** rows above (failover, ops triage, multi-agent delegation), name that plainly and stop — do not produce a routing architecture for a problem the user doesn't actually have. This is the most common failure mode: fluently discussing "routing" while quietly answering a different question than the one asked.

## Step 2 — Gate: real inputs before an architecture recommendation

A bare conceptual/definitional question with no real system behind it ("what is model routing, conceptually," "how does this classifier-then-dispatch pattern work") is `learning-gate` territory — explain from the Step 1 table and don't slam this step's input gate onto a question that isn't asking for an architecture yet.

Once the request is confirmed to be genuine model selection *for a real system*, refuse to recommend build-your-own vs. a proxy, or hand over a tier table, until these are stated (assume-label-compute the ones that are reasonable to estimate, same discipline as `technical-cost-decision` — but do not skip stating them):

- The actual task-type categories in play, and how distinguishable they are. Two categories with a clean signal (e.g. "extraction" vs. "open-ended drafting") is a different problem than eight fuzzy ones.
- Request volume — calls per day or month. If this routing sits inside a larger system whose overall traffic isn't sized yet, that's `capacity-estimation`'s job first.
- Latency budget per call.
- Cost sensitivity. Is this "we're burning real money and need to cut it" or "curiosity, not yet a problem"? If the volume is low enough that tiering saves single-digit dollars a month, say that plainly and recommend against building anything — a routing layer has its own maintenance cost.
- Single-provider tolerance (staying inside one vendor's ecosystem) vs. a real multi-provider requirement, and why (benchmarking across providers, avoiding lock-in, chasing best-in-class per task).
- Whether routing decisions need to be inspectable/auditable. A black-box third-party auto-router (picks a model per-request using its own internal or community-usage logic) is disqualified outright if the answer is yes.

## Step 3 — Build-your-own vs. a proxy

| Situation | Recommendation |
|---|---|
| One provider, team wants full control and auditability of the routing logic, a handful of task categories | Build your own: a cheap/fast model classifies (outputs a task-type label only, not a graded judgment), a lookup table dispatches to the right tier. This is the most controllable option and what most teams that don't want extra infra actually do. |
| Many providers genuinely in play, or the team doesn't want to own routing logic | A proxy (OpenRouter-style cross-provider auto-selection, or a routing-focused local proxy). Name the real cost plainly: traffic goes through a third party, you inherit its judgment and uptime, and you lose per-decision control — the proxy earns its keep mainly when routing across *many* providers, not when tiering within one. |
| Within one agentic coding/tool-use session specifically | Task-functional routing (config-based: `background` / `think` / `longContext` rules dispatching automatically) is a different axis from per-request complexity classification and can run alongside it. |

## Step 4 — If build-your-own: force the actual pipeline

Don't let the recommendation stop at "write a classifier." Require:

- **Classifier model** named explicitly (the cheapest/fastest tier available) — and confirm its only job is emitting a task-type label, not making a graded quality call.
- **Lookup table** stated explicitly (task-type → tier), not implied or left as "the router figures it out."
- **A default/fallback tier** for when the classifier call itself fails, times out, or returns an unrecognized label. A router with no fallback is a new single point of failure, not a cost optimization.
- **Logging of actual outcomes** (task-type, tier used, latency, whether the result was good enough). A tier table set once and never revisited is the most common way this degrades — it's also the precondition for ever reaching Step 1's "adaptive" row.

## Step 5 — Cost, handed off, not repeated here

This skill decides the *architecture*; it does not price it. Once tiers, volume, and rough token counts per call are known, hand off to `technical-cost-decision` for the actual Cost Surface. Do not assert "this saves money" or "this is cheaper" without that arithmetic — the same rule that skill enforces on every other cost claim applies here: a magnitude asserted without a division behind it is a guess wearing a finding's clothes.

## In-session mode

For a step in a live session there is no volume or architecture to gate on, and a plain session already tiers by cost of being wrong, keeps trivial steps inline, and won't claim it switched its own model. Only the parts a plain session doesn't reliably do live here:

- **Escalate one tier per concrete failure** (tests fail after a reasonable try, output contradicts the spec, the same fix attempted twice), name the trigger in one line, and pass the failed attempts along. Don't jump tiers, and don't escalate because the task feels important.
- **Load-bearing work is written by Opus, not just reviewed by it.** Load-bearing = hard to reverse or wrong-in-silence (migrations, money/ledger math, locking and concurrency, auth, data-repair jobs). Spawn a subagent with `model: "opus"` to write the item from a self-contained brief; the main session then reads the diff, runs the tests and any mutation check, and presents it. Structural/plumbing steps stay inline on the main model. The main session explains and presents it from its own reading of the diff, not from the subagent's report (so `incremental-build-pacing`'s explain-back still works). Inside a `spec-drift-gate` slice, that gate's Step 3a owns the delegation mechanics and its Step 4 drift check follows this review. If the user says "no questions", ask once up front anyway or list stated assumptions in the brief (`spec-drift-gate` Step 2a); a tripped tripwire is reported back, never silently defaulted. If the user has set a project convention of "write, then Opus-review", this replaces it. A subagent can't ask the user questions, so settle open decisions in the brief first. Anything unverified in the diff goes back to Opus, not patched from memory.
- **Mechanical, low-risk steps can go down to Haiku** via a subagent with `model: "haiku"`: docs/README edits, renames outside money/auth/schema/concurrency code, boilerplate scaffolding, formatting, bulk find-and-replace. The guard: a wrong result is obvious on a glance at the diff and cheap to fix, and it touches no money, auth, schema or concurrency code. The main session still reads the diff before presenting it. If the step needs judgment about this codebase, or the brief would be longer than the edit, keep it inline instead.
- **Effort is a second dial, separate from the model.** Match it to the cost of being wrong: low for Haiku-tier mechanical steps, default for structural steps, high for load-bearing ones. On a failure, raise effort on the same model first (that counts as the one retry), then escalate a tier; load-bearing work already starts at Opus, so effort is its only lever (this refines the one-tier-per-failure rule; it doesn't add a second escalation). A spawned subagent's effort isn't a call parameter: it comes from its agent definition or the session setting, so for load-bearing work say in the brief what depth is expected (enumerate failure modes and check them before writing) and tell the user once if the session's `/effort` is set low for such a step. Don't claim to have set effort when you only asked for it.
- **Brief a subagent self-contained:** goal, files, constraints, done-criteria, compact return format, plus any failed attempts. It can't see this conversation.
- **A named agent's own model wins** over a tier guess; don't override it from inside the task. If it runs on the wrong tier, say so once and suggest editing the agent.
- **If asked whether a tier is worth the price,** answer the risk call here and hand any dollar figure to `technical-cost-decision`; don't state a cost multiple from memory.
- **Factual model questions** ("which IDs do I pin?") aren't a system-design request: answer from the current models docs or the `claude-api` skill, don't run Step 2.

## Red flags — not done

- Recommended a proxy, a router, or a tier table before placing the request in the Step 1 table
- Said "route to the cheapest model that can handle it" without naming the actual task-type categories
- Recommended a third-party proxy without naming the control/trust/lock-in tradeoff it costs
- Treated a failover/retry-on-error request as if it were cost-tiering, or vice versa
- No fallback named for when the classifier call itself fails
- Asserted cost savings without a handoff to `technical-cost-decision`'s arithmetic
- Answered a low-volume "curiosity" question with a full build-vs-proxy architecture instead of saying the volume doesn't justify one yet
- (In-session mode) Spawned a fresh subagent for work an existing named agent already covers, or tried to override a named agent's model from inside the task
- (In-session mode) Wrote a load-bearing item on the main model and only had Opus review it, or sent a plumbing step to Opus
- (In-session mode) Sent a step to Haiku that needs judgment or touches load-bearing code, or presented Haiku's diff without reading it
- (In-session mode) Escalated a tier when raising effort on the same model wasn't tried, or claimed to have set a subagent's effort
- (In-session mode) Delegated a small, context-loaded step and paid brief overhead that exceeded the step itself
- (In-session mode) Escalated more than one tier on a single failure, or spawned a subagent for work an existing named agent already covers

## Routing boundaries (full)

- Use when someone wants to route calls to an LLM across more than one model — tiering by task type (cheap/fast model for simple work, strongest model for hard reasoning), picking across providers (Claude vs. GPT vs. Gemini), adopting a proxy (OpenRouter, Claude Code Router, RelayPlane or similar), or asking "when should I use Haiku vs. Sonnet vs. Opus" / "should I build a model router" / "is a routing proxy worth it." "Model routing" is used loosely for several distinct problems, and only some of them are actually about picking a model — this skill's first job is placing the request correctly before recommending anything.
- Whether a step should be delegated at all (who owns the decision, how load-bearing it is) is a who-owns-the-decision question (how load-bearing and reversible the choices are), not a model-tier one, and no skill here owns it; handing a settled spec's slice to `spec-executor` is `spec-drift-gate` Step 3a.
- A bare "what agent framework should I use" with no per-call model-tier question is `problem-solving-gates` (Options Generator), not this skill.
- Also covers the live-session version: mid-task in Claude Code (or similar), "which model or agent should run this step," "use a cheaper model for this," "switch models," "escalate" — see In-session mode.
