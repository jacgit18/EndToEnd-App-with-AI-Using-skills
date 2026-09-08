---
name: database-architecture
description: A gated decision process for data-architecture choices — where the source of truth for a piece of data should live (database-first, code-first, or contract-first), what the system boundaries and consumers are, and what artifacts get generated from that. Use this skill whenever the user is about to design or change a database schema, an API shape, a domain model, or is asking "should we use Prisma / an ORM / OpenAPI / GraphQL", "how should we model X", "where should the schema live", "we've picked GraphQL — is the schema our source of truth or generated from code", or proposes an architecture ("I think we should go contract-first") and wants it evaluated. The skill forces the boundary/ownership/source-of-truth questions to be answered — by the user, not by Claude — before any schema or recommendation is produced, then records the outcome as an ADR. It exists to stop architecture from being decided implicitly while 40 files get generated on top of a bad first assumption, so err toward running the gate rather than skipping to a schema. This skill decides *where the authoritative definition lives* (contract-first vs code-first vs database-first); the orthogonal choice of *which wire protocol and interaction model an API surface uses* (REST / GraphQL / gRPC / WebSocket / SSE / webhooks / async messaging) is `api-interface-style`. Not for how a live workload crosses to a chosen new store — the data copy, cutover pattern, rollback window and verification bar — that is `migration-cutover`, which chains from this decision.
---

# Database Architecture

Turn "design my data model" into an explicit decision with a recorded rationale. The skill's job is **not** to push a favorite approach (it is not "always contract-first"). It is to run a decision process, make the user do the load-bearing thinking, recommend one approach with tradeoffs, and write an ADR so the choice is legible six months later.

## When to use

- The user is about to create or change a **database schema**, **API contract**, or **domain model**.
- The user asks which tool to reach for — ORM, query builder, schema/validation library, OpenAPI, GraphQL, protobuf.
- The user proposes an architecture and wants it checked ("I'm leaning contract-first — what am I missing?").
- The user asks, months later, *why* the system is shaped a certain way — read the existing ADRs in `docs/architecture/decisions/` and answer from them.

## Out of scope

- **Implementation.** This skill stops at a recommendation and an ADR. It does not write migrations, models, resolvers, DTOs, or wiring. That is a separate step the user starts explicitly after the ADR exists.
- **Data modeling detail** — normalization, index choice, constraint design, key strategy, lifecycle columns. Note that it is needed and hand off after this ADR exists — `relational-modeling` for an OLTP store, `dimensional-modeling` for an analytical/warehouse model; don't do it here.
- **API interaction style** — REST vs GraphQL vs gRPC vs WebSocket vs SSE vs webhooks vs async messaging, sync-vs-async, request-response-vs-push. That is the wire protocol and interaction model for a surface, orthogonal to the source-of-truth call this skill makes → `api-interface-style`. This skill still owns "is a formal contract warranted, and what is authoritative"; it does not pick the protocol.
- Rewriting or "just getting started on" the schema to be helpful. See the gate below.

---

## The hard gate

Before producing any schema, recommendation, or ADR, the following must be answered. Split them into two kinds:

**Facts you may surface from the repo** (fill these in from `package.json`, config, migrations, existing code — then show them for confirmation):

1. **Persistence** — what database technology is in use or intended. If an existing database or the surrounding system fixes this, surface it for confirmation. If it's genuinely open, it is a **prerequisite decision, not a fact** — see "When persistence isn't decided yet" below and settle it first.
2. **Existing contracts / consumers visible in the codebase** — other services, published API specs, client SDKs, event/webhook payloads.

**Judgment calls that must come from the user in their own words.** These are the rep. Do not supply them, do not offer a shortlist to pick from, do not infer them from the repo and present them as fact. If any is missing, say plainly what's missing and stop — do not proceed "helpfully":

3. **Consumers** — who or what reads this data, and how many distinct consumers: one application, multiple applications, other services, third parties.
4. **Ownership** — who owns the database: this service exclusively, shared with other services, or external/managed elsewhere.
5. **Exposure** — is this data internal-only, or is it exposed across a boundary the user does not fully control.
6. **Evolution** — how fast is the shape expected to change, and what stage is the work in: exploratory/discovery, stabilizing, or stable.
7. **Source-of-truth leaning** — the user's initial position on where the authoritative definition should live (database, code, or contract) *and why*. A leaning, even a tentative one — not "I don't know".
8. **Contract leaning** — does the user think a formal API contract (OpenAPI/GraphQL/protobuf) is warranted here, and why or why not.

"Design my database" with items 3–8 absent is not valid input. Ask for them and stop.

**Pressure does not open the gate.** A deadline, "I've been going back and forth on this for days", or "just pick one" are reasons the user *wants* the gate skipped, not evidence it's satisfied. Under real time pressure the fastest correct move is to get the user to a one-sentence answer for each of 3–8, not to fill them in yourself.

### When persistence isn't decided yet

Item 1 is normally a fact. When it genuinely isn't — greenfield, or the surrounding system doesn't fix it — **the database paradigm is its own gated decision, and it comes first.** The main framework's vocabulary (migrations, referential integrity, joins) and the source-of-truth options themselves assume you already know whether the store is relational; picking wrong here invalidates everything downstream.

Settle it under the same rules — these come from the user, in their own words, not from you. If any is missing, name it and stop:

- **Data shape** — structured, semi-structured, or unstructured; how uniform one record is to the next. "Unstructured" does not automatically mean NoSQL — landing data raw and projecting structure over it (a search index, an extraction pipeline) while keeping a relational system of record is a valid third option; force the choice, don't assume it.
- **Consistency** — does this data need strong consistency and multi-row transactions, or is eventual consistency acceptable for parts of it (a CAP leaning: CP or AP).
- **Access patterns** — read/write ratio, and the query shapes: point lookups, range scans, multi-table joins, graph traversal, time-ordered scans, full-text search.
- **Scale** — rough volume and growth; is horizontal scale a near-term requirement or a someday.
- **Regulatory class** — PII, PHI, financial, or none; anything that forces audit trails or retention rules.
- **Operational capacity** — what the team already runs and knows.

Output: a **paradigm** (relational / document / key-value / wide-column / graph / time-series / ledger / search) and a specific technology leaning, with tradeoffs named — recorded as its own ADR (`NNN-<slug>-persistence.md`) *before* the source-of-truth ADR. `store-options.md` has a paradigm-to-AWS-service mapping table once the shape is decided and the conversation moves to naming an actual product — don't name a service before the paradigm is settled. Then run the main framework, translating its relational terms where needed (for a document store: "migrations" → schema/index definitions; "referential integrity" → invariants enforced in application code).

If any of the data is **large binaries** — files, media, documents, exports, backups — that is a *separate* store choice from the paradigm above, not a column type. The default is object storage (S3 / GCS / Azure Blob) holding the bytes with a pointer row in the primary store, not a multi-MB blob in a database row. See `store-options.md` for the blob-vs-row decision, block vs object vs distributed-file-system, the large-binary patterns, and the controls that make object storage acceptable for regulated data.

---

## Challenge a proposed approach

If the user opens with a decision already made ("we should use contract-first" / "let's just use Prisma"), do not accept it at face value. Before evaluating it, put their own reasoning under the gate above, then test the specific claim:

- **contract-first** — who consumes the contract, is the API actually public, how many consumers, is the domain stable enough that the contract won't churn, who maintains it.
- **code-first / ORM** — will this database be shared with anything that doesn't go through this code, do you need constraints the ORM won't express, is the ORM's model about to become the public API by accident.
- **database-first** — does the team write enough SQL for this to pay off, will application types drift from the actual constraints.

Flag load-bearing assumptions as questions ("is 'the API is public' actually true, or is it public-in-principle?"), not corrections. The point is to turn Claude from a code generator into an architecture reviewer.

---

## The decision process

Once the gate is satisfied, work through `decision-framework.md`. In short: fix the boundaries and consumers, decide who owns the store, decide where the source of truth lives, weigh database-first vs. code-first vs. contract-first against *this* project's stage and consumer set, recommend one, name the tradeoffs, and list the artifacts that get generated from the chosen source of truth.

Do not conflate the different meanings of "schema". Every time the word is used, say which one: **database schema**, **domain model**, **API schema**, **validation schema**, or **type definitions**. They overlap but are not the same artifact and should not be assumed to have the same shape. See `schema-taxonomy.md`.

The lifecycle recommendation is usually *not* "contract-first from line one". A project in discovery can start with an ORM or query builder and introduce a formal contract once its external boundary matters. Say so when it applies.

---

## Output

**1. Recommendation block** (in chat), in this shape:

```
Decision:            <database-first | code-first | contract-first>
Source of truth:     <what artifact is authoritative>
Persistence:         <database technology>
Database modeling:   <how the DB schema is defined — SQL migrations, ORM schema, etc.>
Application access:  <ORM / query builder / generated client>
Validation:          <where runtime validation comes from>
Mapping:             <the translation boundary, e.g. DB row → domain model → API DTO>
Tradeoffs accepted:  <2–4 concrete costs of this choice>
Not chosen because:  <one line per rejected approach>
```

**2. On the user's approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `adr-template.md`. Number it as the next integer after the highest existing ADR in that directory (start at `001` if none, create the directory if absent). Fill every field; do not leave `TBD` in Context or Decision.

Then stop. Implementation is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked the decision themselves — approaches considered, tradeoffs named, a position held — and wants a second opinion or a tie-broken rather than a Socratic pass, they can say so explicitly and you can give a direct recommendation with reasoning. That is an opt-in mode switch, not a default you slide into because the gate is tedious.

---

## Example invocation

> "I'm adding billing to the app. Consumers: just our web frontend for now, plus Stripe webhooks coming in. We own the Postgres DB exclusively. Billing data is internal — nothing external reads it directly. Shape will churn for a few weeks then settle. My lean: code-first with an ORM, because there's no external API consumer to justify a contract yet. Do I need a contract?"

Gate is satisfied (consumers, ownership, exposure, evolution, source-of-truth leaning, contract leaning all present, in the user's words). Claude works `decision-framework.md`, likely agrees code-first is right for now, notes the one boundary to watch (don't let the ORM model become the webhook response shape by accident), recommends a mapping layer at the webhook edge, and — on approval — writes `docs/architecture/decisions/00N-billing-source-of-truth.md`.

> "Design the schema for our new notifications service."

Gate is not satisfied — items 3–8 are all missing. Response: name what's missing, ask for it, stop. Do not produce a schema, and do not offer a draft "to react to".

---

## Portability

This skill is repo-agnostic. It reads and writes `docs/architecture/` relative to whatever repo it's invoked from. To use it in another project, copy the `architecture/` directory into that repo's `.claude/skills/`. See `README.md` in this directory for notes.
