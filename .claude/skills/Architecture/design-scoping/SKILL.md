---
name: design-scoping
description: The front-door gate for a system-design effort — it refuses to start designing until the user has stated the purpose and the audience, the functional requirements plus an explicit out-of-scope list, the non-functional numeric targets (RPS ceiling, concurrency, latency budget, uptime, error budget, cost cap), the constraints (team, timeline, existing stack, target platforms, compliance regime — GDPR / HIPAA / PCI DSS), and which one or two features are worth designing deeply. Its output is a written scope statement that then sequences into the specialist skills — `capacity-estimation` for the numbers, `microservices-decision` for the service split, `api-interface-style` for the surface, `database-architecture` for where the data lives, `failure-mode-analysis` for the failure surface. Use when someone says "design a system for X", "architect a Y", "we're building a new service — how should it be structured", "I'm building X, where do I start", "what's the architecture for this", "scope this project", or hands over a design doc and wants its scope pressure-tested. It is NOT for resolving what a vague request even asks for ("help with my system", "make the architecture better", "clean this up") — that is `ambiguity-gate`, and this skill takes over only once "design or architect a system or feature" is the established intent. It is NOT for judging or sizing an already-defined ticket — that is `ticket-evaluation`; this skill elaborates scope on an under-specified design ask. It does not do the deep design itself — it decides which one or two decisions deserve it and hands those to the specialist skills. It is also NOT for rehearsing or practicing system-design communication — "walk me through this design," "give me a mock system design interview," "help me defend microservices over a monolith here" — even though the vocabulary can sound identical to a real design ask; the tell is stakes and intent, a real system someone is about to build vs. interview prep or practice on a hypothetical. That's `system-design-communication`.
---

# Design Scoping

Before any boxes-and-arrows, any technology names, any schema — establish what is actually
being built and for whom, what it must do and explicitly must not, the numbers it has to
hit, the constraints it lives inside, and which one or two decisions are load-bearing
enough to design deeply and write down. The skill makes the user state each of these in
their own words, because a design built on an unstated assumption gets a hundred decisions
deep before anyone notices the foundation was wrong. It produces a scope statement, then
routes the deep work to the specialist skills.

## When to use

- The user asks to **design or architect a system, service, or feature** — "design a URL
  shortener", "architect the notification service", "how should we structure this".
- The user is **starting a greenfield build** and wants to know where to begin.
- The user has a **design doc or a rough sketch** and wants its scope pressure-tested
  before the team commits.
- A design review is coming and someone wants the **scope pinned down** — what's in, what's
  out, what the targets are — before the review, not during it.
- The user names a system and jumps straight to a technology ("let's use Kafka and
  Postgres for this") without having stated what it's for or how big it is.

## Out of scope — hand these off

- **Working out what a vague request even asks for** — "help me with my system", "improve
  the architecture", "can you look at this" with no design intent established → `ambiguity-gate`.
  That skill resolves *which task this is*; this skill takes over once "design / architect a
  system or feature" is the settled intent. (Same split as `test-practice-gate` ↔
  `ambiguity-gate`.)
- **Judging or sizing a defined ticket** — "should this be in the sprint", "how risky is
  this ticket", "estimate this" → `ticket-evaluation`. That skill works a *specified* unit
  of work; this skill elaborates scope on an *under-specified* design ask.
- **The capacity numbers themselves** — turning "≈2M DAU" into QPS, storage, bandwidth,
  server count, and what binds first → `capacity-estimation`. This skill makes the user
  *state the non-functional targets*; that skill *derives the physical quantities* from the
  usage assumptions. Chain: scope here, size there.
- **Whether to split into services and where the boundaries go** → `microservices-decision`.
- **The API surface style** (REST / GraphQL / gRPC / events / streaming) → `api-interface-style`.
- **Where the source of truth lives and which store** → `database-architecture`.
- **The failure surface** — enumerating and ranking every way the design can break →
  `failure-mode-analysis`.
- **Who/what gets access to a resource, and its network placement** →
  `cloud-iam-boundary`, once a specific resource and principal exist to grant access to —
  this skill states the compliance regime (GDPR/HIPAA/PCI) that shapes how strict that
  skill's gate needs to be, not the grant itself.
- **What compute primitive runs a given unit of work** — Lambda vs container vs a
  long-running service, orchestration vs choreography → `serverless-execution-model`, once a
  specific operation exists to run, not for the system as a whole.
- **The deep design of the 1–2 chosen features** — this skill *selects* them (via the
  significance filter) and states why they matter; the actual design is the specialist
  skills above, run one at a time.
- **Cost of reversing a decision** — how expensive a choice is to change later →
  `technical-cost-decision`. The significance filter here uses *blast radius* (how much
  breaks if this changes), which is a different axis; don't duplicate the cost analysis.
- **Auditing a system that already exists and already makes public claims** — for the gaps
  between what a shipped product does and what its privacy policy / cookie banner / security
  posture disclose → `disclosure-gap-audit`. This skill states the compliance regime as an
  input *before* the design; that skill is the post-build audit that checks the built thing
  against its commitments. Scope here, audit there.
- **The delivery cadence of the build that follows** — building the scoped system slowly,
  one file at a time, so the user learns it → `incremental-build-pacing`, after
  `spec-drift-gate` turns this scope statement into a build spec and names the first slice.
  This skill scopes; that one paces delivery.

---

## The gate

Before producing any design, structure, or technology recommendation, all five must be
stated. **Do not invent them.** If any is missing, name it and stop.

**Facts you may surface from the repo / an existing doc** (state them for confirmation):

1. **What exists already** — the current system or the absence of one, the stack in use,
   the team's languages and platforms, any written requirements or tickets.

**Judgment calls that must come from the user, in their own words:**

2. **Purpose and audience** — the one-sentence reason this system exists, and who uses it:
   the target demographic (general public / enterprise / internal / a specific segment),
   roughly how many, where they are (one region / global), and on what (web / mobile /
   desktop / API / all). "A chat app" is not a purpose; "team collaboration chat for
   engineering orgs of 50–500, web and mobile, mostly US/EU" is.
3. **Functional requirements + an explicit out-of-scope list** — the handful of things the
   system must do, *and* the things a reasonable person might expect it to do that it
   deliberately will not (v1 has no voice calls, no third-party integrations, no admin
   console). The out-of-scope list is not optional — an unstated exclusion is a scope
   fight later.
4. **Non-functional numeric targets** — real numbers, or an explicit "not a constraint":
   - **Throughput ceiling** — peak RPS / requests per day the design must survive.
   - **Concurrency** — simultaneous users / connections / sessions.
   - **Latency budget** — p50 and p99 targets for the key operations. A single percentile
     (just "p95 < 3s") satisfies the gate; note the unstated one as a non-blocking gap.
   - **Availability** — the uptime target (99.9 / 99.95 / 99.99) and, if known, what an
     hour of downtime costs. The cost-of-downtime figure is the one sub-item that may be
     left as "not quantified" without failing the gate — but say so, and characterise the
     impact qualitatively ("dispatch stalls, revenue-impacting, not safety-critical").
   - **Error budget** — the acceptable error rate for the critical path.
   - **Cost cap** — a monthly infrastructure ceiling, or a unit-economics target
     (cost per user / per request / per GB).
   "Fast" and "reliable" are not targets. A number, or "we accept whatever the simple
   design gives us" — stated, not assumed.
5. **Constraints** — the box the design lives in:
   - **Team** — how many engineers, their experience, who operates it.
   - **Timeline** — when v1 has to ship, and whether that's hard.
   - **Existing stack** — languages, datastores, cloud, deployment platform the design must
     fit or is free to ignore.
   - **Platforms** — the clients that must be supported (browser matrix, mobile OS
     versions, offline).
   - **Compliance** — GDPR, HIPAA, PCI DSS, SOC 2, data residency, audit retention — or an
     explicit "none apply". This one is load-bearing and frequently forgotten.
6. **The 1–2 features to design deeply** — of everything in scope, which one or two
   decisions are significant enough (see the significance filter) to design in depth and
   write down now. Everything else is acknowledged and deferred. If the user can't name
   them, the filter below is the tool to find them — but the user makes the call. If the
   user *has* named them, still run the filter over each pick — to confirm it's genuinely
   deep-dive-worthy and to generate the blast-radius line the scope statement records.

"Design a system for real-time collaborative editing" with items 2–6 absent is not valid
input. The reply is the list of what's missing, framed as the scope the user needs to
commit to.

**Pressure does not open the gate.** "We already know what we're building, just design it",
"there's no time for a scoping doc", "the requirements are obvious" are reasons to want the
gate skipped. The fast path is items 2–6 in a few sentences each — not Claude inventing a
purpose, a user base, and a set of numeric targets that the whole design then rests on.

---

## The significance filter (choosing the deep-dive features)

For gate item 6, use this to decide which decisions deserve deep design now and which are
acknowledged-and-deferred. Ported from `Architecture/Boundaries of LLD and HLD.md`.

**The blast-radius question** — "if I change this later, how much of the system breaks?"

| Blast radius | Level | Deep-dive now? |
|---|---|---|
| The whole system, or the data model | High-level design | **Yes** — these are the 1–2 |
| Many modules / several teams | Mid-level | Maybe — if it's on the critical path |
| One function / one module | Low-level | No — decide it during implementation |

**The "who cares?" test** — who in the org would need to be in the room for this decision:

- An **architect** cares → high-level → deep-dive candidate.
- A **team lead** cares → mid-level.
- An **individual developer** cares → low-level → not now.

**The migration tell** — if changing the decision later would require a **migration plan, a
data rewrite, or an operational change**, it was never low-level design, regardless of how
small the code change looks. Choosing the ORM, the serialization format, the auth
mechanism, the primary datastore, the service boundaries, the public API shape — these
routinely get mislabeled "implementation detail" and then box the system in.

Apply all three. A decision that is whole-system blast radius, an architect's call, and
would need a migration to undo is exactly one of the 1–2. This filter is about *scope of
impact*, not *cost to replace* — the reversibility / expense-to-rebuild axis lives in
`technical-cost-decision`; don't re-derive it here.

---

## Challenge a proposed scope

If the user opens with scope already sketched (a design doc, a set of requirements), put it
under the gate and test it:

- **"the requirements are all functional"** — where are the numbers? A design with no
  throughput, latency, or availability target will be over- or under-built and nobody can
  tell which. Push for item 4 or an explicit "no constraint".
- **"everything is in scope for v1"** — then nothing is prioritized and the timeline
  (item 5) is fiction. What is the *smallest* thing that delivers the purpose (item 2)?
- **no out-of-scope list** — add one. Name the five things people will assume are included
  that aren't.
- **compliance not mentioned** — ask directly. "Do any of GDPR, HIPAA, PCI DSS, SOC 2, or
  data-residency rules apply?" A retrofitted compliance boundary is a redesign.
- **jumped to technology** — "we'll use Kafka and Cassandra" before purpose and numbers is
  a solution in search of a problem. What load and what access pattern make those the
  answer?
- **10 features all "critical"** — run the significance filter. Usually one or two are
  whole-system blast radius and the rest are deferrable.

Flag the load-bearing gap as a question, not a correction.

---

## The process

Work `scope-dimensions.md` in order once the gate is satisfied: restate purpose + audience
and the user-base characterization → confirm the functional list and *write the
out-of-scope list* → pin each non-functional target to a number or an explicit "not
constrained" → list the constraints, compliance last and explicitly → run the significance
filter over the in-scope decisions and pick the 1–2 → assemble the scope statement →
sequence the deep work to the specialist skills.

Reference files:

- `scope-dimensions.md` — the five dimensions expanded: the purpose/audience framing and
  the user-base questions (demographics, growth, concurrency, geography, platform
  diversity, offline needs); the functional / out-of-scope method; the non-functional
  target checklist with what each number drives downstream; the constraints list with the
  compliance-regime cheat-sheet (GDPR / HIPAA / PCI DSS / SOC 2 — what each one forces into
  the design).
- `significance-filter.md` — the blast-radius / who-cares / migration-tell classifier in
  full, worked against example decisions, and how it feeds the deep-dive selection without
  duplicating `technical-cost-decision`'s reversibility axis.

---

## Output

**1. In chat, a scope statement:**

```
Purpose:            <one sentence — why this exists>
Audience:           <who — segment, rough count, geography, platforms>
In scope (v1):      <the functional list — 3–7 items>
Explicitly out:     <the deliberate exclusions — 3–7 items>
Non-functional targets:
  Throughput:       <peak RPS / req-day, or "not constrained — accept the simple design">
  Concurrency:      <simultaneous users / connections>
  Latency:          <p50 / p99 for the key ops>
  Availability:     <uptime target + cost of an hour down>
  Error budget:     <acceptable error rate on the critical path>
  Cost cap:         <monthly ceiling or unit-economics target>
Constraints:        team <n, experience> · timeline <date, hard?> · stack <fixed parts> · platforms <clients> · compliance <regimes, or "none">
Deep-dive now:      <the 1–2 decisions — each with its blast radius and why it can't wait>
Acknowledged, deferred: <the rest — decided later, during implementation or a later design pass>
Sequence:           <ordered list of which specialist skill runs next on which decision>
```

**2. On approval**, write the scope statement to
`docs/architecture/scope/<system-slug>.md` (create the directory if absent). This is a
living document — it gets updated as scope changes — not an ADR. Each of the 1–2 deep-dive
decisions gets its *own* ADR later, from the specialist skill that owns it.

Then hand off to the first skill in the sequence. Typical order:

1. `capacity-estimation` — turn the audience + throughput targets into QPS / storage /
   bandwidth / what-binds-first.
2. `microservices-decision` — one service or several, and the boundaries.
3. `api-interface-style` — the surface style for each boundary.
4. `database-architecture` — where the source of truth lives and which store.
5. `serverless-execution-model` — what runs each unit of work, if compute shape isn't already fixed.
6. `cloud-iam-boundary` — who/what gets access to each resource, and its network placement.
7. `failure-mode-analysis` — the failure surface of the resulting design, before sign-off.

Not every design needs all five, and the sequence is not a closed list — a scope statement
may also pull in `data-tier-operations` (scaling an existing store), `technical-cost-decision`
(when the cost cap is tight), `caching-strategy`, `access-control-modeling` (when one of the
deep-dive picks is the permission/authorization model — who may do what to which resource), or
`bff-gateway-placement` (when the audience names more than one client type — web, mobile,
partners — and what sits between them and the services from step 2 is itself a deep-dive pick),
`service-mesh-adoption` (when the service split from step 2 produces enough services calling
each other that encryption, discovery, or uniform resilience between them is itself a deep-dive
pick), or `config-and-secrets-management` (when a named credential or config value's storage
and rotation is itself a deep-dive pick) where the deep-dive decisions imply them. Name the
skills this scope actually needs, in dependency order.

Separately from the deep-dive sequence above, the settled **in-scope functional list** from
item 3 is what `user-story-decomposition` turns into sprint-ready backlog stories — that
skill runs alongside or after the architecture sequence, not instead of it.

When the 1–2 deep-dive decisions are **coupled** (one's output is the other's input — a
location-ingest design that feeds an assignment engine), say so and order them: design the
upstream one first.

---

## Escape hatch

If the user has genuinely done the scoping — purpose, audience, functional and out-of-scope
lists, numeric targets, constraints, and the deep-dive picks all stated — assemble the
scope statement and plan the sequence directly rather than running a Socratic pass over
things they already answered. This applies whether they *ask* for direct assembly or simply
open with a fully-specified message: a complete opening dump is treated as the escape-hatch
case. Re-interrogating a user who already gave you everything is the failure here, not a
safeguard. (Still run the significance filter over their named deep-dive picks — that's
analysis they're owed, not a re-ask.)

---

## Example invocations

> "Design a link-shortening service for us."

Gate not satisfied — items 2–6 absent. Response: this needs scoping before a design, and
the scoping is the work. Ask for: who it's for and roughly how many (internal tool? public
service? marketing team?); the functional list (shorten, redirect, custom aliases,
analytics?) and what's explicitly out (user accounts? link expiry? bulk API?); the numbers
(redirects/sec at peak, acceptable redirect latency, uptime target, monthly cost ceiling);
the constraints (team size, deadline, existing stack, any compliance); and — using the
significance filter — which one or two decisions (the key-generation scheme? the
read-path/storage design? custom-domain support?) are worth designing deeply now. Don't
propose a schema or a technology.

> "We're building an internal analytics dashboard. Purpose: let the ops team see order
> volumes and error rates without asking engineering. ~20 users, all internal, web only,
> US. In scope: 6 predefined dashboards, CSV export, a date-range picker. Explicitly out:
> custom query builder, alerting, mobile, external sharing. Targets: it can be slow (5s
> page load fine), 20 concurrent users max, 99% uptime is plenty, no hard cost cap but
> keep it under ~$200/mo. Team: 2 engineers, 6 weeks, we're a Python/Postgres shop on AWS,
> no compliance beyond SOC 2. Deep-dive: the query/aggregation approach over the orders
> data, since that decides whether we hit Postgres directly or need a rollup layer."

Escape hatch — fully scoped. Assemble the scope statement, note that the one deep-dive
(direct-query vs rollup layer) is a whole-data-model blast-radius call and routes to
`database-architecture` / `data-tier-operations`, and that with 20 users and a 5s budget
the sequence is short: skip `capacity-estimation` (numbers are trivially small), skip
`microservices-decision` (one small app), go straight to the data decision, then a light
`failure-mode-analysis` pass before ship.

> "Can you help me with my system? It's kind of a mess."

Not this skill yet. "Help" and "a mess" don't establish a design task — is this a
refactor, a debugging session, a redesign, a documentation pass? → `ambiguity-gate` to
resolve what's being asked. If it resolves to "redesign it", this skill picks up.

> "Is this ticket worth pulling into the sprint? [pastes a defined ticket]"

Not this skill. A specified unit of work being judged → `ticket-evaluation`.

---

## Portability

Repo-agnostic. Writes a living scope statement to `docs/architecture/scope/`; the deep-dive
decisions get their own ADRs from the specialist skills. Copy the `design-scoping/`
directory into another repo's `.claude/skills/` to use it there. See `README.md` for where
it sits among the sibling skills.
