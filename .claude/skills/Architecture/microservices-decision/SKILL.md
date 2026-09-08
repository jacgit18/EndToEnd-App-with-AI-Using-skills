---
name: microservices-decision
description: Use when someone is deciding whether to adopt microservices, split a monolith, extract or add another service, or design service boundaries — including when the decision is presented as already made ("our CTO decided", "we've made the call", "don't relitigate it", "just tell me how to split it"), when repos or CI for services are already scaffolded, or when the ask is for a service list, service boundaries, data ownership across services, how many services to have, or a decomposition/migration sequence. Also covers repo layout — one repo, repo-per-service, or a hybrid — including monorepo tooling choice (Nx/Turborepo/Bazel), CODEOWNERS, affected-graph CI, and version-skew-vs-dependency-hell, since the layout follows mechanically from the same headcount/ownership/independent-deploy facts this skill already gates on; also use when someone proposes a service count and wants it checked. Also covers frontend decomposition into micro-frontends — one frontend app, micro-frontends per team, or a hybrid, and the integration technique (server-side / client-side / edge composition, module federation) — since it's the same headcount-and-ownership arithmetic applied to the client side; use when someone says "should we split the frontend into micro-frontends", "each frontend team wants their own deploy", or "should the mobile/web frontend be one app or several". Not for diagnosing why a specific endpoint is slow. Not for database sharding or shard-key choice, or replication/partitioning topology (that is `data-tier-operations`), even when phrased as an already-made decision — "we're sharding, just tell me the key" is a data-tier question, not a service-split one. Not for what layer sits between clients and backend services — a shared API gateway, a Backend-for-Frontend, or direct-to-service calls — that is `bff-gateway-placement`, which takes this skill's service boundaries as input.
---

# Microservices Decision

The number of services an organization can run is bounded by the number of people who can own and carry them — not by how cleanly the domain factors. A domain will always factor into more services than the team can staff. This skill forces that arithmetic into the open *before* any boundary is drawn, because a service list is the one artifact a reader will copy and act on regardless of what surrounds it.

## Out of scope

- **A greenfield system that has not been scoped yet.** "We're building a new platform from scratch — how do we split it into services" with no stated purpose, functional decomposition, load targets, or headcount context → `design-scoping` first. It produces the scope statement and then sequences the service-split decision back here. This skill needs the system to exist (or be fully scoped) before it can size a split of it.
- **Performance triage.** If the presenting problem is a slow endpoint, that is a profiling question, not this one.
- **Implementation.** This skill stops at a decision, a design posture, and an ADR. Contracts, schemas, and saga code are a separate, explicitly-started step.
- **How the services talk once the boundaries exist** — REST vs GraphQL vs gRPC vs an event broker vs webhooks for inter-service communication → `api-interface-style`, run per surface after this decision. This skill decides *whether and where* to split; not the wire protocol between the pieces.
- **Release ordering and rollout mechanism once code is merged** — coordinating a release train across repos, canary/blue-green/rolling for a specific deployable unit → `deployment-strategy`. This skill decides how many repos; not how each one ships once merged. (Build/test CI shape — one pipeline running everything vs affected-graph/path-scoped checks per repo — stays *in* scope here; see "Repo layout follows from this" below. `deployment-strategy` explicitly disclaims CI/pipeline mechanics, so don't send that half of the question there.)
- **CI cost at scale** — build-minute spend, self-hosted-runner vs SaaS-CI tradeoffs, remote-cache hosting cost → `technical-cost-decision`, once the layout below names what's running.
- **Executing a repo split or merge** — moving code between repos with history, cutting over CI, redirecting collaborators → `migration-cutover`. This skill decides the target layout; that skill sequences getting there safely.
- **What compute primitive runs one already-scoped service** — Lambda vs a container task vs a long-running process, invocation model, and orchestration vs choreography for that service's own workflow → `serverless-execution-model`, once the service boundary here is settled. This skill decides *how many* services and where the lines are; not what runs inside one of them.
- **What layer sits between clients and backend services** — a shared API gateway, a Backend-for-Frontend per client type, or direct-to-service calls, and where cross-cutting concerns like auth termination or rate limiting centralize → `bff-gateway-placement`, which takes this skill's service boundaries and count as a given input. This skill decides how many backend services exist; not what a client talks to in order to reach them.

---

## The output contract

Your response has these parts, **in this order**. This ordering is the skill.

1. **Readiness Block** (below) — always first
2. Gate questions that remain unanswered, if any — then **stop**
3. Recommendation, only once the block is filled
4. Boundaries and data ownership, only if the recommendation was to split

**No service name, service list, boundary, or diagram may appear before the Readiness Block is complete.** Not as a preview, not as an illustration, not as "here's the end state, and here's the sizing caveat after it." A caveat placed after a service list does not modify that list — the reader has already taken the list.

```
Headcount:            <N engineers>
Services to run:      <M — every service that will exist, including the residual monolith>
Engineers per service: <N ÷ M>  →  <verdict: see arithmetic below>
Owner per service:    <named person or team for EACH service, or UNASSIGNED>
On-call:              <exists / does not exist — who carries the pager today>
Independent deploy:   <can one service ship without coordinating a release: yes/no>
Problem being solved:  <the problem services are meant to fix, one sentence>
Cheaper option tested: <the non-distributed option considered, and why rejected>
Sunk cost at risk:    <what has actually been spent, in days>
Readiness verdict:    <ready for M | ready for K < M | not ready>
```

Any field you cannot fill from the user's own words is `UNANSWERED`. A block with `UNANSWERED` fields ends the response. Do not fill them with assumptions and proceed.

## Do the arithmetic out loud

Write `N ÷ M` as a number in the block. Never leave it implied.

**Count the residual monolith as one of the services.** Extracting three services from a monolith leaves you four things to run, not three — the monolith still needs owners, on-call, CI, and migrations exactly like the new ones. Teams reliably forget this, and it is usually the difference between a number that looks comfortable and one at the floor.

Below roughly **3 engineers per service**, services become orphaned: nobody owns them, nobody is on call for them, and each one still costs CI, deploys, migrations, and a local dev story. Two to three services for four engineers is not a smaller version of the right architecture — it is one system with extra network calls between its halves.

When `N ÷ M` is under the threshold, say the number and the consequence in the same breath, and name the largest `K` the headcount actually supports.

## Authority is not architecture

"Our CTO decided," "we've made the call," and "every serious company ends up here" are facts about the organization or the industry. They are not evidence about this system. Record them in the block as constraints. Do not convert them into a technical conclusion.

## Concessions do no work

Do not write a sentence whose job is to reassure the user you will not press the decision. Not as an opener, not as a closer, not in passing, not parenthetically.

**Banned moves** — these, however phrased and wherever they sit:

- "Not going to relitigate it."
- "Fine — decision's made."
- "I won't reopen the decision, but…"
- "Regardless of who's right about the long-term call…"

Give the Readiness Block instead. It is shorter than the concession and it is not an argument.

Where the decision is genuinely not yours to reopen, say so **once, in the Recommendation, after the block is filled** — never before it, and never in place of a field.

Likewise, never soften a load-bearing finding into an aside: "worth a five-minute conversation," "one thing worth pinning down," "if that's a bridge too far, fine." If it changes the decision, it goes in the block.

## Red flags — stop and restart the response

- A sentence anywhere before the filled block reassures the user you will not press the decision
- A service name appears before the Readiness Block is filled
- Your questions are in a closing section titled something like "two things I'd want to know"
- You wrote a sizing caveat *after* a service list
- You know the headcount but never wrote `N ÷ M`
- Your denominator counts only the new services and not the monolith they leave behind
- You are explaining why you are allowed to raise a concern
- On-call and per-service ownership are absent from your response

**All of these mean: the block was not first, or was not honest. Start the response over.**

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "They said don't lecture them" | That vetoes repeating pros and cons. It does not veto asking for inputs the answer depends on. Efficiency is not the same as rigor. |
| "The decision is already made" | Then the block takes thirty seconds and costs nothing. If it changes nothing, nothing is lost. |
| "The repos are already scaffolded" | Scaffolding and CI is days of work. Say the number of days out loud — it is almost always cheap to discard, and that is the single most useful fact about it. |
| "The monolith doesn't count, it already exists" | It exists and it still needs an owner, a pager, and a deploy pipeline. It is a service. Count it. |
| "There's a deadline" | A deadline is when the cost of a distributed system is highest and its benefit is zero. Pressure is a reason to state the arithmetic sooner, not to skip it. |
| "They're exhausted, be kind" | Handing someone a ten-service list they cannot staff is not kindness. |
| "I'll add a sizing caveat at the end" | Readers act on the list. A caveat after it is decoration. |
| "It's their CTO's call, not mine" | Correct — and unrelated to whether the arithmetic gets stated. |
| "I asked my questions, at the bottom" | Questions after a recommendation cannot change the recommendation. |

---

## When they proceed anyway

A filled block reading "not ready" and a user who splits regardless is a **completed** decision, not a failed one. Record it in the ADR and continue. The arithmetic is stated once, in the block, and not repeated afterward.

What changes is which design you give. Above the headcount the team can staff, design for **survivable failure** rather than for scale, and say that is what you are doing:

- One service orchestrates each cross-service flow, in one readable file. No choreography — a flow that lives in no single place cannot be debugged by an under-staffed team.
- Every cross-service write takes an idempotency key and a timeout.
- Every hold on a resource carries a TTL that expires on its own, so a flow that dies halfway self-heals without anyone writing a recovery daemon.
- Data that must stay transactionally consistent stays together, in one service, on one database.

## Recommendation and ADR

Once the block is filled, recommend one of: **monolith**, **modular monolith** (module boundaries enforced in-process, one deployable), **K services**, or **full decomposition** — with two to four concrete tradeoffs accepted, and one line per rejected option.

On the user's approval, write an ADR to `docs/architecture/decisions/NNN-<slug>.md`, numbered as the next integer after the highest existing ADR (start at `001`, create the directory if absent). Carry the Readiness Block into the ADR's Context verbatim — the headcount and ownership facts are what make the decision legible later.

Then stop. Implementation is a separate step.

## Repo layout follows from this

Once the Readiness Block is filled and a boundary recommendation exists, "how many repos" is not a fresh decision — it reads off three fields you already have.

**Services that already exist, no new split proposed.** If the question is purely repo layout for services whose boundaries are already settled — nothing is being extracted, sized, or justified against a cheaper option — `Problem being solved`, `Cheaper option tested`, and `Sunk cost at risk` don't apply to a new decision; write `N/A — layout question, no new service proposed` for each rather than treating them as unanswered. `Owner per service`, `On-call`, and `Independent deploy` still gate: those are exactly the three facts the layout call below reads off.

- **Independent deploy = yes, for a service with its own owner** → that service gets its own repo. It ships on its own schedule; forcing it into a shared repo means every unrelated change on the main branch can block or complicate its release.
- **Independent deploy = no** (a shared release train), or the recommendation was **monolith** / **modular monolith** → one repo. Splitting repos you deploy together buys nothing and adds the coordination tax described above (multi-repo PR sequences for one logical change).
- **Mixed** — some services deploy independently, most don't → **hybrid**: one repo for the shared-release-train core, separate repos for the services that genuinely deploy on their own. Don't split a service out "for symmetry" if its `Independent deploy` field says no.

This is a default, not a mandate — a team can accept the coordination tax of full repo-per-service, or the CI/ownership tax of a large monorepo, deliberately. State it as a rejected alternative in the ADR, same as any other tradeoff in this skill's output.

**The trade you're actually making, either direction:**

- **Split further → version skew.** Shared code between repos gets published and versioned (a dependency each consumer bumps on its own clock — drift, "works on repo A, breaks on repo B" bugs) or duplicated (drift a different way, silently). Neither is free; name which one you're accepting.
- **Stay together → dependency hell's cousin, undifferentiated CI.** A monorepo without path-scoped tooling runs the whole suite on every PR regardless of what changed, and "who owns this" degrades to tribal knowledge. This is fixable, not inherent — see below — but it isn't automatic.

**If the layout is (or stays) one repo, three pieces of tooling make it not hurt** — detail and tool comparison in [repo-layout.md](repo-layout.md):

1. **Affected-graph or path-scoped CI**, so a PR only runs checks for what it touched, not the whole tree.
2. **`CODEOWNERS`**, mapping the top-level layout to the `Owner per service` field already in the block — this is what actually answers "who owns what," not the repo split.
3. **A directory layout that matches the service boundaries** from the recommendation above — the affected-graph and ownership tools both key off directory boundaries, so they need to be clean.

## Frontend decomposition follows the same arithmetic

"Should we split the frontend into micro-frontends" is the same headcount-and-ownership question this skill already gates on, applied to the client instead of the backend — run the same Readiness Block, substituting frontend teams for backend service owners and independently-deployable frontend pieces for services. Don't build a second decision procedure for it.

- **Services to run** counts each independently-deployable frontend piece (a shell app plus each micro-frontend), same as it counts the residual monolith on the backend side — a "product listing" micro-frontend and a "checkout" micro-frontend are two things to own, build, and deploy, not one "frontend" line item.
- **Engineers per service** applies identically: a micro-frontend with no team large enough to own its build pipeline, dependency upgrades, and on-call for production UI bugs is exactly as orphaned as an unowned backend service.
- **Problem being solved / cheaper option tested** still gates. "Independent deploy cadence per team" and "isolating a legacy UI section during a rewrite" are real problems a micro-frontend split solves; "the backend is microservices, so the frontend should match" is not — architectural symmetry between layers is not a reason on its own, same as authority-without-evidence is rejected on the backend side.

**Once the split is justified, the remaining decision is integration technique** — how the shell application composes the independently-built pieces at runtime: server-side composition, client-side composition (e.g. Module Federation, Single-SPA), or edge-side composition. This is mechanical once the split and ownership are settled, not a fresh architectural debate — detail in [frontend-layout.md](frontend-layout.md).

This section does not decide what backend layer a client (single frontend or several micro-frontends) talks to — a shared API gateway, a Backend-for-Frontend, or direct-to-service calls is `bff-gateway-placement`, a separate decision that takes the client's shape as given.

## Escape hatch

If the user has genuinely worked the decision — options considered, tradeoffs named, headcount and ownership already accounted for — they can say so and get a direct recommendation without the Socratic pass.

This changes the depth of discussion. It does not move the Readiness Block, and it does not let `N ÷ M` go unstated.
