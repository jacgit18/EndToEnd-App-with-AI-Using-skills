---
name: technical-cost-decision
description: Use when a technical decision carries a recurring price — choosing between infrastructure or managed services, sizing a system against a stated volume (requests/day, users, uploads, events, GB, tokens), planning work to bring down a cloud bill, evaluating build-versus-buy, or when the request mentions a monthly spend, a budget, a runway, or a savings target. Also use when someone proposes spending engineering effort to save money, or asks whether something is going to get expensive. Covers AWS/GCP/Azure bills, egress and data transfer, per-request and per-token API pricing, storage growth, and managed-service premiums. Sizes the bill and finds the dominant line item; deciding which signals, sampling rates, or retention tiers to change on a telemetry/observability stack to bring its cost down is `observability-strategy`. Turning a usage volume into the physical quantities that get priced — QPS, GB/day, peak Gbps, server count, cache working-set memory, and what binds first — is `capacity-estimation`, which hands those numbers back here; this skill assumes and labels the *unit prices* ($/GB-month, instance $/hr, egress $/GB, engineer $/week), not the *usage drivers* (DAU, actions/user/day, payload sizes), which come from the user when `capacity-estimation` is in play. Planning the move itself when a cloud-cost or datacentre-exit is the migration driver — cutover pattern, data move, rollback window — is `migration-cutover` (it hands the target's steady-state bill sizing back here). Deciding whether to shed load or add priority tiers instead of scaling capacity — the shed-vs-scale mechanism choice — is `resilience-strategy` (it hands the autoscaling/headroom bill sizing back here). Choosing the repo layout and monorepo build tooling (Nx/Turborepo/Bazel, remote-cache hosting) is `microservices-decision`; this skill sizes the CI-minutes and remote-cache dollar cost once that choice is made. A bare "X or Y, which is cheaper" where X/Y are compute primitives (Lambda vs Fargate, a function vs a container vs a long-running service) goes through `serverless-execution-model`'s technical-fit gate first — duration, statefulness, and concurrency can rule one out before price is even relevant, and that skill hands the resulting duration/concurrency numbers back here to price. Whether a shared API gateway or a backend-for-frontend sits in front of multiple services or client types at all is `bff-gateway-placement`; this skill only prices the chosen layer (managed gateway vs self-hosted) once that topology is settled. Pricing a tiered-model or multi-provider LLM-call setup — should Haiku/Sonnet/Opus (or cross-provider) calls be split by task type, and via a proxy or a build-your-own classifier — is `model-routing-decision`, which hands the settled tiers and token counts back here to price; don't price a routing scheme whose architecture hasn't been decided yet.
---

# Technical Cost Decision

Cost reasoning fails at the division, not at the concepts. The recurring failure is a response that discusses cost fluently, names engineering effort as the dominant expense, and never converts any of it into a number. This skill forces three specific calculations. It teaches no cost concepts, because that is not where the gap is.

## What this does not do

- **Push optimization before it is warranted.** Most cost choices are reversible and should be made late. Producing a number is not the same as acting on it — a Cost Surface showing $80/month is a reason to stop thinking about cost, and saying so is a valid outcome.
- **Manufacture precision.** One significant figure with stated assumptions is the target. `~$3k/month` is an answer; `$2,847.61/month` is a lie.

---

## Trigger

Produce a Cost Surface whenever **any** of these is true:

- The request contains a volume or rate — users, requests, uploads, events, GB, tokens, per day or per month
- The request names a bill, budget, runway, or savings target
- The request asks you to choose between infrastructure or service options that run continuously
- The request proposes spending engineering effort to reduce a cost

A design question that carries a volume is a cost question. The user does not have to say the word "cost."

## The Cost Surface

Goes **before** the recommendation, not after it.

```
Volume assumption:   <the figure everything derives from, and where it came from>

Compute:             $<n>/mo    <basis>
Storage:             $<n>/mo    <basis, including growth per month>
Data transfer:       $<n>/mo    <basis — egress, cross-AZ, NAT>
Third-party / API:   $<n>/mo    <basis — per request, per token, per seat>
Managed premium:     $<n>/mo    <what you pay over self-managed>
Engineer time:       $<n> one-time   (<N> engineer-weeks × $<rate>/week)
                     $<n>/mo ongoing (<fraction> of an engineer, forever)

Run rate:            $<n>/mo
Dominant line:       <which one, and what share of the total>
```

**Every line appears.** A line that is genuinely trivial is written `~$0 — <reason>`, never omitted. Egress is the line most often missing and most often dominant; if data leaves your network, it has a price.

**The Surface is added to the answer, not substituted for it.** Guidance that does not depend on the figures — what to build, what is expensive to reverse — is still owed. Answer the question that was asked, and put the Surface in front of it.

**The billing unit is not always "per request."** Get the actual basis before writing the `Compute:` line — a wrong basis produces a Surface that looks precise and is wrong. Example: AWS Step Functions Standard workflows bill per 1,000 **state transitions**, not per execution or per request — every retry, every `Map`/`Parallel` iteration, and every state entered counts as a transition, so a workflow's *state count* is itself a cost lever (collapsing five sequential validation states into one Lambda call cuts transitions, not just latency); Express workflows instead bill per invocation + GB-seconds, closer to Lambda's model. Check the actual pricing page's unit for any service before assuming request-based billing.

## When a figure is missing

Assume, label, compute, correct. Do not stop for an input you can reasonably estimate:

1. State the figure you assumed, and that it is yours rather than theirs.
2. Compute the Surface with it.
3. Give the **break-even** — the value of that figure at which the recommendation flips.
4. Name your softest assumption and ask for that one number.

Stop only when the plausible range spans orders of magnitude *and* the recommendation flips inside it. Then say which single figure would settle it, and give whatever guidance does not depend on that figure while you wait.

**Exception — usage drivers when `capacity-estimation` applies.** If the missing figure is a *usage driver* (DAU, actions per user per day, payload size, fan-out, read:write ratio) and the request is also a sizing question, that skill's gate owns it — get it from the user, don't assume it. "Assume, label, compute" covers unit prices and figures derived from them, not the usage basis the whole estimate rests on.

## Engineer time is a line item

Convert effort to money every time. Default to **$4,000 per engineer-week** loaded, and say that you used it, so the user can substitute their own figure.

Six weeks of two engineers is not "six weeks." It is `2 × 6 × $4,000 = $48,000`, and in most of these decisions it is the largest number on the page.

Ongoing operational burden is also a line: "10% of an engineer forever" is `~$20k/year`, which is often larger than the infrastructure it was meant to save.

## Payback period

Whenever effort is being spent to reduce a recurring cost, compute:

```
payback months = one-time engineer cost ÷ monthly savings
```

Write the division out. Then state the number of months plainly, and compare it against the alternatives on the table — a lever with a two-week payback and one with a two-year payback are not both "cost savings."

Beyond roughly 12 months, say so directly: at that horizon the savings are competing with the possibility that the system is replaced, repriced, or outgrown first.

## Never assert a magnitude without arithmetic

Do not write **"negligible," "a rounding error," "cheap," "not the expensive part," "the real cost is X,"** or any equivalent, unless a figure appears in the same response supporting it.

These phrases are conclusions of a calculation. Used without one, they are guesses that sound like findings — and they are how a dominant line item gets waved past. If you do not have the volume needed to compute it, ask for the volume. Do not estimate the verdict and skip the estimate.

## Red flags — the Cost Surface is not done

- You wrote "engineer-weeks" or "founder-months" without a dollar figure beside it
- You described effort and savings but never divided one by the other
- A line in the Cost Surface is absent rather than marked `~$0`
- You priced the option the user asked about and no others
- You called something a rounding error without computing it
- The request contained a volume and your response contains no `$`
- You asked for a figure you could have assumed, labelled, and computed with
- Your response is a Surface or a questionnaire, and never answers the question that was asked

**All of these mean: fill in the Surface before writing the recommendation.**

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "It's obviously a rounding error" | You know that after dividing, not before. Divide, then say it in one line. |
| "They asked about compute, not cost" | They gave you a volume. Egress and storage are on the bill whether or not they were asked about. |
| "Engineer time isn't a cloud cost" | It is the biggest cost in most of these decisions and the only one that never appears on the bill. |
| "I said it was six engineer-weeks — that's clear" | Weeks do not divide into dollars saved. Only dollars do. |
| "I don't know their salary" | Use $4,000/engineer-week and label it as an assumption. |
| "An estimate would be wrong" | An order of magnitude with stated assumptions is the deliverable. Silence is not more accurate; it just moves the guess to the reader. |
| "I don't have their volume" | Assume one, label it as yours, compute, and give the break-even. A labelled estimate is a deliverable; a request for data is not. |
| "Cost doesn't matter at their stage" | Then the Surface takes two minutes and says so with a number, which is the reassurance they actually need. |
| "They said they'd optimize later" | Later is usually right. The Surface tells you whether this is one of the few cases where it isn't. |

---

## Recommendation

After the Surface, recommend one option, and name:

- The dominant line and what actually moves it
- Two to four tradeoffs accepted
- One line per rejected option, with its number

Where the Surface shows the spend is immaterial, say that plainly and stop. "Roughly $200/month at your volume — this is not worth optimizing until you have customers" is a complete and useful answer.
