---
name: design-scoping
description: The front-door gate for a system-design effort — it refuses to start designing until the user has stated the purpose and the audience, the functional requirements plus an explicit out-of-scope list, the non-functional numeric targets (RPS ceiling, concurrency, latency budget, uptime, error budget, cost cap), the constraints (team, timeline, existing stack, target platforms, compliance regime — GDPR / HIPAA / PCI DSS), and which one or two features are worth designing deeply. Its output is a written scope statement that then sequences into the specialist skills — `capacity-estimation` for the numbers, `microservices-decision` for the service split, `api-interface-style` for the surface, `database-architecture` for where the data lives, `failure-mode-analysis` for the failure surface. Use when someone says "design a system for X", "architect a Y", "we're building a new service — how should it be structured", "I'm building X, where do I start", "what's the architecture for this", "scope this project", or hands over a design doc and wants its scope pressure-tested. It is NOT for resolving what a vague request even asks for ("help with my system", "make the architecture better", "clean this up") — that is `ambiguity-gate`, and this skill takes over only once "design or architect a system or feature" is the established intent. It is NOT for judging or sizing an already-defined ticket — that is `ticket-evaluation`; this skill elaborates scope on an under-specified design ask. It does not do the deep design itself — it decides which one or two decisions deserve it and hands those to the specialist skills. It is also NOT for rehearsing or practicing system-design communication — "walk me through this design," "give me a mock system design interview," "help me defend microservices over a monolith here" — even though the vocabulary can sound identical to a real design ask; the tell is stakes and intent, a real system someone is about to build vs. interview prep or practice on a hypothetical. That's `system-design-communication`. Not for the candidate-by-candidate technology conversation across a build's decisions — that is `tech-decision-walkthrough`, downstream of this skill's decision list. Not for gating a multi-file build behind a written spec or diffing work against it — that is `spec-drift-gate`; not for pacing file-by-file delivery of a chosen design — that is `incremental-build-pacing`. Not for auditing a shipped product's disclosures against its practice — that is `disclosure-gap-audit`; a compliance regime here is only an input constraint. Not for sizing the dollar cost of a stated cost cap — that is `technical-cost-decision`. Not for turning the settled functional list into sprint-ready backlog stories — that is `user-story-decomposition`. NOT for a user stalled or overwhelmed before beginning, rather than asking for an architecture — that is `entry-point-first`.
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
- The user asks **"what should v1 include?"** for a product they haven't listed features for.
  No skill in this catalog invents a feature list for them; this gate withholds by design.
  Sequence: they state purpose and audience → they list candidate features (Claude may prompt
  by category, not supply the list) → this gate pins scope and out-of-scope → for a competing
  batch, `user-story-decomposition`'s MoSCoW pass (`moscow.md`) makes the categorical cut.

## Out of scope — hand these off

Each is NOT this skill; route to the sibling (full reasoning and boundary cases in `out-of-scope.md`):

- Vague request, unclear what is asked → `ambiguity-gate` (this skill takes over once "design / architect" is settled).
- Judging or sizing a defined ticket → `ticket-evaluation`.
- Deriving QPS / storage / bandwidth from the stated targets → `capacity-estimation`.
- Service split and boundaries → `microservices-decision`; API surface style → `api-interface-style`; where data lives → `database-architecture`; failure surface → `failure-mode-analysis`.
- Who/what gets access, network placement → `cloud-iam-boundary`; what compute primitive runs a unit of work → `serverless-execution-model`.
- The deep design of the 1–2 chosen features → the specialist skills above, one at a time.
- Cost of reversing a decision → `technical-cost-decision`; sizing a stated cost cap → `technical-cost-decision`.
- Auditing a shipped product against its public claims → `disclosure-gap-audit`.
- Candidate-by-candidate technology comparison and ADRs → `tech-decision-walkthrough`; gating a build behind a spec → `spec-drift-gate`; pacing file-by-file delivery → `incremental-build-pacing`.

**Read `out-of-scope.md`** when a request sits near one of these boundaries and the one-liner does not settle it.

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

For gate item 6: which decisions deserve deep design now, which are acknowledged-and-deferred.
Ask the **blast-radius question** — "if I change this later, how much of the system breaks?"
Whole system or data model → high-level → **deep-dive now** (these are the 1–2); many
modules / several teams → maybe, if on the critical path; one function / module → decide
during implementation. Cross-check with the **who-cares test** (architect → deep-dive
candidate; team lead → mid; individual dev → not now) and the **migration tell**: if
changing it later needs a migration plan, data rewrite, or operational change, it was never
low-level (ORM, serialization format, auth mechanism, primary datastore, service boundaries,
public API shape all get mislabeled "implementation detail"). A decision that is whole-system,
an architect's call, and needs a migration to undo is exactly one of the 1–2. This filter is
*scope of impact*, not *cost to replace* — that axis is `technical-cost-decision`'s.

**Read `significance-filter.md`** for the full classifier and worked examples.

---

## Challenge a proposed scope

If the user opens with scope already sketched (a design doc, a set of requirements), put it under the gate and test it. Flag the load-bearing gap as a question, not a correction.

**Read `scope-challenges.md`** for the six standard pushbacks (all-functional requirements, "everything is v1", no out-of-scope list, compliance unmentioned, jumped to technology, ten "critical" features).

---

## The process

Work `scope-dimensions.md` (five dimensions expanded, incl. the compliance cheat-sheet) in order once the gate is satisfied: restate purpose + audience
and the user-base characterization → confirm the functional list and *write the
out-of-scope list* → pin each non-functional target to a number or an explicit "not
constrained" → list the constraints, compliance last and explicitly → run the significance
filter over the in-scope decisions and pick the 1–2 → assemble the scope statement →
sequence the deep work to the specialist skills.

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

Not every design needs all seven, and the sequence is not a closed list — name the skills this scope actually needs, in dependency order. **Read `extra-handoffs.md`** for the additional skills a scope can pull in (`data-tier-operations`, `caching-strategy`, `access-control-modeling`, `bff-gateway-placement`, `service-mesh-adoption`, `config-and-secrets-management`, …) and when.

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

**Read `worked-examples.md`** when unsure how to respond to a specific opening (bare "design X", a fully-scoped dump, a vague "help with my system", a ticket-sizing ask).

---

## Portability

Repo-agnostic. Writes a living scope statement to `docs/architecture/scope/`; the deep-dive
decisions get their own ADRs from the specialist skills. Copy the `design-scoping/`
directory into another repo's `.claude/skills/` to use it there. See `README.md` for where
it sits among the sibling skills.

**Not a stalled start:** if the user cannot begin at all ("I don't know where to start", overwhelmed) rather than needing a scope statement, that is `entry-point-first` -- one low-resistance rep first, then return here.
