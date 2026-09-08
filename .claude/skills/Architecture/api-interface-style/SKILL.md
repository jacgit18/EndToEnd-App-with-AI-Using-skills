---
name: api-interface-style
description: A gated decision for choosing the interaction style of one API surface — REST/HTTP-JSON, GraphQL, gRPC, WebSocket, Server-Sent Events, webhooks, or async messaging — plus the sync-vs-async and request-response-vs-push questions that come with it. Use when someone is picking or changing how a service exposes itself or how two systems talk: "REST or GraphQL", "should we use gRPC", "how should the frontend talk to the backend", "we need real-time updates — websockets?", "webhooks vs polling", "is our API over-fetching", or proposes a style and wants it checked ("we're going GraphQL, right?"). It forces the surface, the consumers and their platform constraints, the interaction shape (request/response, server-push, streaming, bidirectional, events), the query-shape and latency needs, and public-vs-internal to be stated by the user before any protocol is recommended, then records the outcome as an ADR. Not for where the authoritative API definition lives (contract-first vs code-first; OpenAPI / GraphQL schema / protobuf as source of truth) — that is `database-architecture`. Not for whether to split into services or where service boundaries go — that is `microservices-decision`. Not for cost-sizing against request volume or managed-gateway-vs-self-hosted — that is `technical-cost-decision`. Not for whether a gateway or backend-for-frontend sits in front of multiple services/clients at all — that is `bff-gateway-placement`, which this skill hands the new layer's own surface style to once its topology is picked.
---

# API Interface Style

Given an API surface that needs to exist — one service's external interface, or one integration between two systems — decide how it talks: which protocol, request/response or push, sync or async, streaming or not. The skill makes the user name the surface, its consumers, and what actually needs to flow before any style is on the table, recommends one primary style (and names a secondary where a sub-case needs it), and writes an ADR.

## When to use

- The user is choosing the style for a **new** API surface, or reconsidering an existing one.
- The user asks a style question directly: REST vs GraphQL vs gRPC, WebSocket vs SSE, webhooks vs polling, sync API vs message queue.
- The user asks **how two things should communicate** — frontend to backend, service to service, your system to a third party, your system to many subscribers.
- The user reports a symptom that is really a style question: "the mobile app hits six endpoints per screen", "we're polling every few seconds", "clients over-fetch", "we need live updates".
- The user proposes a style and wants it pressure-tested ("we'll use GraphQL for everything" / "gRPC between all services").

## Out of scope — hand these off

- **Where the authoritative API definition lives** — contract-first vs code-first, whether OpenAPI / a GraphQL schema / a `.proto` is the source of truth, what gets generated from it → `database-architecture`. That decision is orthogonal to this one: you can be contract-first with gRPC or code-first with REST. If the user is really asking "where should the schema live", send them there.
- **Whether to split into services, and where the boundaries go** → `microservices-decision`. This skill designs the interface of a surface that already exists as a concept; it does not decide how many surfaces there are.
- **Cost-sizing against a request/event volume, managed API gateway vs self-hosted, egress** → `technical-cost-decision`.
- **Schema / table design** behind the API → `relational-modeling` (OLTP) or `dimensional-modeling` (analytical).
- **Replication, sharding, connection pooling, transaction patterns** behind the API → `data-tier-operations`.
- **Implementation** — writing the OpenAPI spec, the `.proto`, resolvers, handlers, client SDKs. This skill stops at a recommendation and an ADR.
- **Versioning mechanics** (URI vs header vs query) and **auth-scheme selection** (API key vs OAuth2 vs mTLS). Name that each is needed and defer it; don't decide it here.
- **Gateway / BFF placement** — whether a shared gateway or a backend-for-frontend sits in front of multiple services or client types → `bff-gateway-placement`. This skill decides one surface's protocol; that skill decides whether a layer exists at all, and this skill picks up again for that layer's own client-facing surface once its topology is chosen.

---

## The gate

Do not name a protocol until these are answered. Split into what you may surface from the repo and what must come from the user.

**Facts you may surface from the codebase** (fill in, then show for confirmation):

- **Existing styles in play** — what the service already exposes or consumes (HTTP handlers, a GraphQL schema, `.proto` files, a WebSocket server, a message-broker client). A new surface usually wants a reason *not* to match what's already there.
- **Client platforms visible in the repo** — a browser SPA, a React Native app, other internal services, a published SDK.

**Judgment calls that must come from the user, in their own words.** These are the rep. Do not infer them and present them as fact. If any is missing, say what's missing and stop:

1. **The surface** — which interface is this, and what are its two ends? "Our public API, called by external developers." "The browser SPA talking to our backend." "The orders service calling the inventory service." "Our system notifying partner systems of shipment events."
2. **Consumers** — who calls it: browsers, mobile apps, your own other services, named external partners, unknown public. How many distinct client *types*, and do you control their release cycle.
3. **Interaction shape** — what actually needs to flow, and in which direction: request→response, server→client push, client→server stream, bidirectional session, or fire-and-forget events. Be concrete about the direction.
4. **Data / query shape** — fixed resources with predictable reads, *or* highly variable client-driven queries (many screens each needing a different slice), *or* RPC-style "run this operation and tell me what happened". And: is over-fetching / under-fetching an *observed* problem or a hypothetical.
5. **Latency & throughput** — is this a latency-sensitive hot path (internal, high call volume, tight budget) or ordinary user-facing CRUD? Rough call rate and payload sizes.
6. **Real-time need** — does a client need updates within seconds *without polling*, or is poll-on-interval / poll-on-refresh acceptable? If real-time: one-directional (server→client) or truly two-way?
7. **Consumer reachability & platform limits** — can every consumer be reached the way the style needs (a browser can't speak raw gRPC; a webhook consumer must expose a public HTTPS endpoint and not sit behind a firewall)? What do the clients' platforms actually support?
8. **Public / stability** — is this a published boundary that outside consumers depend on staying stable, or internal and free to churn?

"How should our API work" with items 1–8 absent is not valid input. Ask for what's missing and stop. Do not offer a shortlist of protocols "to react to".

**Pressure does not open the gate.** "Just tell me REST or GraphQL", a deadline, or "the team already voted" are reasons the user wants the gate skipped, not evidence it's satisfied. The fastest correct move under time pressure is a one-sentence answer to each of 1–8.

---

## Challenge the framing

If the user opens with the style already chosen, put their reasoning under the gate first, then test the specific claim against `style-tradeoffs.md`:

- **"GraphQL"** — how many *distinct* client query shapes actually exist today? One client with stable screens does not need a query planner. Is the over/under-fetching measured, or assumed? Who owns resolver performance (N+1, cost limiting, depth limiting) once HTTP-layer caching is gone?
- **"gRPC"** — does any consumer run in a browser (needs grpc-web + a proxy)? Will external partners accept a `.proto` and binary framing, or do they expect REST + JSON? gRPC earns its keep on internal, hot-path, service-to-service calls — is that this surface?
- **"REST for everything"** — is one of these surfaces actually an event stream you're about to build as a poll loop? A bidirectional session about to be faked with long-polling? Name the sub-case that doesn't fit.
- **"WebSocket"** — do you need bidirectional, or only server→client? SSE rides plain HTTP, auto-reconnects, and carries a fraction of the operational weight. Reserve WebSocket for genuine two-way sessions.
- **"Webhooks"** — are the consumers internet-reachable? Do you have a retry, ordering/dedup, signature-verification, and replay story? Without it you get silently lost and spoofable events; a pull feed or a hosted queue may be more reliable.

Flag the load-bearing assumption as a question ("is 'clients over-fetch' something you've measured, or a worry?"), not a correction.

---

## The process

Once the gate is satisfied, work `selection-framework.md` in order: name the surface and its ends, classify the interaction shape, map each consumer to the protocols its platform allows, score the surviving candidates against data-shape / latency / real-time / team, pick the primary style, name any secondary style for a sub-case, and list what you're deferring (versioning, auth, gateway, contract source-of-truth).

`style-tradeoffs.md` backs it: each style in one line, what it fits, what it costs, which consumers it rules out, and its failure mode when misapplied — plus a note that **combining styles is normal** (REST for CRUD + SSE for a live feed; gRPC between services + REST at the edge; a sync API + webhooks for events). Picking a primary and a secondary is a valid outcome, not a failure to decide.

---

## Output

**1. Recommendation block** (in chat):

```
Surface:             <what interface, and its two ends>
Primary style:       <REST | GraphQL | gRPC | WebSocket | SSE | webhooks | async-messaging>
Serialization:       <JSON | Protocol Buffers | ...>
Secondary style:     <style for a named sub-case, e.g. "SSE for the live order feed" — or "none">
Interaction shape:   <request-response | server-push | client-stream | bidirectional | events>
Consumers covered:   <each client type and how it reaches the surface>
Tradeoffs accepted:  <2–4 concrete costs of this choice>
Not chosen because:  <one line per rejected style>
Deferred:            <versioning / auth scheme / gateway or BFF / contract source-of-truth — to which skill, and the trigger>
```

**2. On the user's approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `adr-template.md`. Number it as the next integer after the highest existing ADR in that directory (start at `001`, create the directory if absent). Fill every field; no `TBD` in Context or Decision.

Then stop. Writing the contract, the handlers, or the SDKs is a separate step the user starts explicitly.

---

## Escape hatch

If the user has genuinely worked the decision — styles considered, consumer constraints named, tradeoffs weighed, a position held with reasons — and wants a second opinion or a tie broken rather than a Socratic pass, they can say so and you give a direct recommendation with reasoning. That is an opt-in mode switch, not a default you slide into because the gate is tedious.

---

## Example invocations

> "New surface: our public API for third-party developers. Consumers: external devs on every platform, we don't control their release. Mostly request/response — read and write our core resources, plus they want to be told when a record changes rather than polling. Ordinary CRUD latency, nothing hot. Updates within a minute are fine, one-directional. They can host HTTPS endpoints. This is a published boundary, has to stay stable. I'm leaning REST but unsure about the change-notification part."

Gate satisfied (surface, consumers, interaction shape, data shape, latency, real-time, reachability, stability all present in the user's words). Work `selection-framework.md`: primary **REST + JSON with OpenAPI** for the CRUD surface (ubiquitous tooling, cacheable, what external devs expect, stays stable); secondary **webhooks** for change notification, with the note that retries + signature verification + a replay endpoint are required and are their own build. Defer: versioning scheme, auth (OAuth2 likely, → separate decision), whether a gateway fronts it (→ `technical-cost-decision` if volume-driven). On approval, write `docs/architecture/decisions/00N-public-api-style.md`.

> "What should our API look like?"

Gate not satisfied — items 1–8 all missing, and it's unclear whether this is one surface or several (which would be `microservices-decision` first). Response: name what's missing, ask for it, stop. Do not list protocols to react to.

---

## Portability

Repo-agnostic. Reads `docs/architecture/decisions/` for context and writes new ADRs there. Copy the `api-interface-style/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling decision skills.
