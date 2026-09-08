# Scope Dimensions

The five things the gate in `SKILL.md` requires, expanded — what to ask, and what each
answer drives downstream. Consolidated from `Architecture/01. System Design/Specifying Scope
indepth.md`, `Architecture/01. System Design/Userbase.md`, and `Architecture/Define system
threshold.md`.

Work them in order. Each produces a block of the scope statement.

---

## 1. Purpose and audience

### Purpose

One sentence: why this system exists and what changes for someone when it does. Not the
mechanism ("a chat app"), the outcome ("engineering teams stop losing decisions in DMs").
If the user can't say it in one sentence, the design will wander.

### Audience — user-base characterization

From `Userbase.md`. Ask:

- **Who** — general public / enterprise buyers / internal staff / a named segment
  (developers, clinicians, drivers). Personas if they exist.
- **How many** — today and the 12–24 month projection. A round number.
- **Where** — one country / one region / global. Drives data residency, multi-region,
  latency-from-edge.
- **On what** — web (which browsers), mobile (iOS/Android, min versions), desktop, API-only,
  embedded. Multiple clients means a shared contract is itself a design decision.
- **Growth shape** — flat, steady, or a launch spike / seasonal peak. Feeds the
  peak:average ratio `capacity-estimation` needs.
- **Concurrency** — how many are active *at once* at peak, not just registered.
- **Offline** — do clients need to work disconnected and sync later? That's a large design
  commitment; get it stated now, not in month three.

Output: the `Audience:` line — segment, count, geography, platforms, and any of
growth/concurrency/offline that are load-bearing.

---

## 2. Functional requirements + the out-of-scope list

### In scope

The 3–7 things the system must do to deliver the purpose. Verbs, from the user's world:
"post a message", "redirect a short link", "export a report". Not components ("a queue"),
not qualities ("be fast"). If the list is longer than ~7, the scope is a program, not a
system — split it or pick the v1 subset.

### Explicitly out of scope

**Required, not optional.** List the things a reasonable person would assume are included
that deliberately are not — for v1, for this team, for now. Examples of the shape:

- "No SSO / SAML — email+password only in v1."
- "No mobile app — responsive web only."
- "No third-party API for external developers."
- "No self-serve admin — support handles account changes manually."
- "No real-time collaboration — last-write-wins, refresh to see others' changes."

An unstated exclusion becomes a scope argument during the build, or a silent assumption
that someone designs around at cost. Naming five now is cheap.

---

## 3. Non-functional numeric targets

From `Define system threshold.md`. Each gets a **number** or an explicit **"not
constrained — we accept whatever the straightforward design gives us"**. "Fast", "scalable",
"reliable" are not entries.

| Target | Ask | What it drives |
|---|---|---|
| **Throughput ceiling** | Peak requests/sec (or requests/day) the design must survive without falling over. | The whole of `capacity-estimation`; the service count; whether a queue is needed. |
| **Concurrency** | Simultaneous users / connections / open sessions at peak. | Connection-pool sizing, whether long-lived connections (WebSocket/SSE) are viable, stateless-vs-sticky. |
| **Latency budget** | p50 and p99 for the 2–3 key operations, from the user's point of view. | Sync vs async boundaries, caching, how many network hops are affordable, read-model design. |
| **Availability** | Uptime target (99.9 / 99.95 / 99.99) and what one hour of downtime costs the business. | Redundancy, multi-AZ/region, failover design, whether the cost of HA is justified. |
| **Error budget** | Acceptable error rate on the critical path (e.g. < 0.1% of checkouts fail). | How hard to work on resilience; what `failure-mode-analysis` scores as severe; SLO targets. |
| **Cost cap** | A monthly infra ceiling, or a unit-economics target (¢ per user / per request / per GB). | Managed-vs-self-hosted, instance choices, data-retention policy; hands to `technical-cost-decision`. |

If the user resists numbers: a rough order of magnitude is enough ("hundreds of RPS, not
tens of thousands"; "seconds is fine, not milliseconds"). The point is to rule out the
designs that can't possibly hit it and the ones that are massively over-built for it.

---

## 4. Constraints

The box the design must fit inside. From `Specifying Scope indepth.md` and `Userbase.md`.

- **Team** — how many engineers will build and then operate it; their depth in the relevant
  areas; whether there's an ops/SRE function or the builders carry the pager. A 2-person
  team and an 8-person team get different architectures for the same requirements.
- **Timeline** — when v1 must ship, and whether that date is hard (a contract, an event) or
  aspirational. A hard near-term date shrinks the deep-dive list.
- **Existing stack** — the languages, datastores, message brokers, cloud, and deployment
  platform already in use that the design must fit — or an explicit "greenfield, free to
  choose". "We're a Postgres shop on AWS ECS" removes a lot of the option space, usefully.
- **Platforms** — the client environments that must be supported: browser matrix, mobile OS
  floor, offline, low-bandwidth regions, screen-reader / accessibility obligations.
- **Compliance** — ask directly, because it is the most-forgotten and most-expensive-to-retrofit:

  | Regime | Triggers when | Forces into the design (examples) |
  |---|---|---|
  | **GDPR** (and similar) | EU/UK personal data | Lawful basis, data-subject access/erasure, data-residency options, consent records, breach notification, minimization. |
  | **HIPAA** | US protected health information | BAAs with every processor, encryption at rest + in transit, audit logging of PHI access, access controls, retention rules. |
  | **PCI DSS** | Storing / processing / transmitting card data | Network segmentation, no PAN in logs, tokenization/vaulting, quarterly scans; scope-minimizing designs (hosted fields, redirect) are usually the point. |
  | **SOC 2** | Selling to enterprises that require it | Change management, access review, monitoring/alerting evidence, vendor management — process as much as architecture. |
  | **Data residency** | Contractual / national rules | Region-pinned storage and processing, sometimes region-pinned keys. |

  "None of these apply" is a valid, and common, answer — but it should be *stated*, so a
  reviewer can check it rather than assume it.

---

## 5. The 1–2 deep-dive decisions

Run `significance-filter.md` over the in-scope items. The output is:

- **Deep-dive now** — the one or two decisions that are whole-system / data-model blast
  radius, an architect's call, and would need a migration to undo. Each gets designed in
  depth (by the specialist skill that owns it) and written down now.
- **Acknowledged, deferred** — everything else. Named, so it's not forgotten, but decided
  later during implementation or a follow-up design pass. Most decisions land here, and
  that's correct — designing all of them up front is waterfall.

The user makes the final call on which 1–2; the filter is how you get there and how you
justify it in the scope statement.

---

## Assembling the scope statement

Fill the template in `SKILL.md`'s Output section from blocks 1–5, then build the
**sequence**: which specialist skill runs next, on which decision, in what order. The
default order is `capacity-estimation` → `microservices-decision` → `api-interface-style`
→ `database-architecture` → `failure-mode-analysis`, but a given scope statement usually
only invokes a subset — a 20-user internal tool skips capacity and microservices; a
data-heavy pipeline may start at `database-architecture`. Name the ones this scope actually
needs and the order they unlock each other.
