---
name: model-routing-decision
description: Use when someone wants to route calls to an LLM across more than one model — tiering by task type (cheap/fast model for simple work, strongest model for hard reasoning), picking across providers (Claude vs. GPT vs. Gemini), adopting a proxy (OpenRouter, Claude Code Router, RelayPlane or similar), or asking "when should I use Haiku vs. Sonnet vs. Opus" / "should I build a model router" / "is a routing proxy worth it." "Model routing" is used loosely for several distinct problems, and only some of them are actually about picking a model — this skill's first job is placing the request correctly before recommending anything. Retry-on-timeout or fallback-to-another-model-on-rate-limit is an availability/failover pattern, not this skill (it's a reliability mechanism dressed in the same vocabulary). Classifying an incoming ticket/request and handing it to a downstream team or system is ops/workflow triage, not this skill, even though the classifier is often an LLM call. A lead agent delegating subtasks to specialized sub-agents is an agent-architecture / labor-division decision, not this skill — this skill re-enters once that structure exists and each sub-agent's own model choice needs deciding. Pricing the tiers once volume and token counts are known is `technical-cost-decision`, which this skill hands off to rather than repricing itself. Sizing the overall request volume this routing sits inside is `capacity-estimation`. A bare "what agent framework should I use" with no per-call model-tier question is `problem-solving-gates` (Options Generator), not this skill.
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
| A lead agent delegates subtasks to specialized sub-agents | Multi-agent orchestration / labor division | **Not this skill.** That's an agent-architecture decision. Once the delegation structure exists, this skill can be reapplied to decide each sub-agent's own model. |

If the request lands in one of the last three rows, name that plainly and stop — do not produce a routing architecture for a problem the user doesn't actually have. This is the most common failure mode: fluently discussing "routing" while quietly answering a different question than the one asked.

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

## Red flags — not done

- Recommended a proxy, a router, or a tier table before placing the request in the Step 1 table
- Said "route to the cheapest model that can handle it" without naming the actual task-type categories
- Recommended a third-party proxy without naming the control/trust/lock-in tradeoff it costs
- Treated a failover/retry-on-error request as if it were cost-tiering, or vice versa
- No fallback named for when the classifier call itself fails
- Asserted cost savings without a handoff to `technical-cost-decision`'s arithmetic
- Answered a low-volume "curiosity" question with a full build-vs-proxy architecture instead of saying the volume doesn't justify one yet
