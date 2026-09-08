---
name: bff-gateway-placement
description: A gated decision for what sits between client applications and backend services — no intermediary (each client calls services directly), a shared API gateway (one layer, uniform for every consumer), a Backend-for-Frontend per client type (an aggregation/shaping layer each frontend team owns), or a hybrid (a shared gateway for cross-cutting concerns with one or more BFFs behind it). Use when someone says "should the frontend call the services directly or through a gateway", "do we need a BFF", "should mobile and web share the same API or get their own", "our API gateway is doing too much", "should auth live at the gateway or in each service", "let's add a BFF for the new mobile app", "each client hits five endpoints and stitches the screen together itself", "reverse proxy vs API gateway vs load balancer, which do we need", or proposes a topology and wants it checked. It forces the user to name the distinct client/consumer types, how many backend surfaces a single screen or operation needs to call, whether those clients' data/aggregation needs actually diverge, and who would own a shared layer, before any topology is recommended, then records the outcome as an ADR. Not for the wire protocol or interaction style of any one surface (REST/GraphQL/gRPC/WebSocket/etc.) — that is `api-interface-style`, which this skill hands the newly-introduced gateway/BFF's own surface to once the topology is picked. Not for whether to split into backend services or where those boundaries go — that is `microservices-decision`, which this skill assumes as given (it takes the service count as input, not an output). Not for splitting the frontend itself into independently-deployable micro-frontends — that is also `microservices-decision` (its "Frontend decomposition" section), a distinct decision about frontend team/repo boundaries, not about what backend layer a client talks to. Not for the mechanics of rate limiting, circuit breaking, or load shedding at whatever layer this skill places them — that is `resilience-strategy`, which this skill hands the "centralize here" decision to. Not for managed-gateway-vs-self-hosted dollar cost — that is `technical-cost-decision`. Not for the authentication/authorization scheme itself (OAuth2 flow, JWT validation, RBAC/ABAC model) — that is `access-control-modeling` for application permissions and `cloud-iam-boundary` for infrastructure identity; this skill only decides *where in the request path* a check is terminated, not how the check works. Not for an unscoped, not-yet-designed system — that is `design-scoping` first, which sequences a system with named client types back here. A bare conceptual question with no named system ("what's the difference between an API gateway and a BFF", "what is a BFF") is answered directly, no gate — the gate exists for a pending decision on a named client/backend topology, not for explaining the vocabulary.
---

# BFF / API Gateway Placement

Take a backend made of one or more services and more than one kind of client calling into it, and decide what — if anything — sits between them: nothing (each client calls services directly), a single shared gateway, a Backend-for-Frontend per client type, or a shared gateway with BFFs behind it. The skill makes the user name the actual client types and whether their needs actually diverge before any topology is on the table, because "every serious system has an API gateway" and "let's give the new mobile app its own BFF" are both defaults that solve a problem that may not exist yet, or that quietly duplicate the same aggregation logic three times over.

## When to use

- Someone is **introducing a new client type** to an existing backend — "we're building a mobile app, should it hit the same API as the web app or get its own".
- Someone is **deciding whether to add an intermediary layer** — "do we need an API gateway", "should we add a BFF", "should the frontend talk to services directly".
- Someone reports a symptom that is really a topology question — "the mobile app makes eight calls to render one screen", "our gateway has become a second monolith nobody wants to touch", "auth logic is duplicated across twelve services", "every client re-implements the same response-stitching".
- Someone is **deciding where a cross-cutting concern lives** — auth termination, rate limiting, request logging, TLS termination — centralized at an edge layer vs duplicated per-service.
- Someone proposes a topology already-decided and wants it checked — "let's put a BFF in front of everything", "one shared gateway will handle all our clients", "skip the gateway, it's just overhead".

## Out of scope — hand these off

- **The wire protocol or interaction style of any one surface** — REST vs GraphQL vs gRPC vs WebSocket vs SSE for the gateway/BFF's own client-facing surface, or for a backend service behind it → `api-interface-style`. This skill decides whether a layer exists and what it owns; that skill decides how any one surface (including the new layer's own) talks.
- **Backend service boundaries** — how many services exist, where the lines are, team ownership of each → `microservices-decision`. This skill takes the service count and boundaries as given input; it does not decide whether to split the backend further.
- **Frontend decomposition into micro-frontends** — splitting the client application itself into independently-deployable pieces owned by different frontend teams (module federation, server-side/edge composition) → `microservices-decision`'s "Frontend decomposition" section. That is a client-side team-boundary decision; this skill is about what backend-facing layer a client (however it's built) talks to.
- **Service-to-service (east-west) traffic** — whether a service mesh exists for how backend services call *each other*, as opposed to how external clients reach them → `service-mesh-adoption`. This skill is exclusively north-south (client-to-service); a system can have both a gateway/BFF and a mesh, solving different halves of the traffic picture.
- **Rate limiting, circuit breaking, load shedding mechanics** — the actual algorithm, thresholds, and failure behavior of a control placed at the gateway or in-process → `resilience-strategy`. This skill only decides whether centralizing such a control at a shared layer makes sense given the topology; that skill designs the control itself.
- **Dollar cost** — managed API gateway (AWS API Gateway, Apigee, Kong-hosted) vs self-hosted, per-request pricing at volume → `technical-cost-decision`, once this skill's topology narrows the options being priced.
- **The authentication/authorization scheme itself** — OAuth2/OIDC flow design, JWT validation logic, session handling, the RBAC/ABAC model → `access-control-modeling` (application permissions) or `cloud-iam-boundary` (infrastructure identity). This skill only decides *where* a check is terminated (edge vs per-service vs both) — a placement question, not a scheme design.
- **Implementation** — the actual gateway configuration, BFF handler code, service mesh manifests. This skill stops at a recommendation and an ADR.
- **An unscoped, not-yet-designed system** — "what should our API layer look like" with no named client types or backend surfaces yet → `design-scoping` first, which sequences a concretely-scoped system back here.
- **A bare conceptual question with no named system** — "what's the difference between an API gateway and a BFF", "what is a BFF" — is answered directly, no gate. The gate exists for a pending decision on a named client/backend topology, not for explaining the vocabulary.
- **"Reverse proxy vs API gateway vs load balancer, which do I need"** — these three get conflated because they can coexist, but they answer different questions and aren't this skill's decision alone: a **load balancer** distributes traffic across replicas of the *same* service (that need — running more than one instance — is `deployment-strategy`/`resilience-strategy` territory, or `capacity-estimation` for how many); a **reverse proxy** terminates TLS, hides origin servers, and often caches responses (`caching-strategy` if the question is about response caching, `cloud-iam-boundary` if it's about network placement/exposure); an **API gateway or BFF** is this skill's decision — routing and shaping traffic across *multiple, different* services for one or more client types. A real system commonly has all three, at different layers, doing different jobs — don't treat "which one" as a single mutually-exclusive choice; name which concern is actually being asked about and route accordingly.

---

## The gate

Before recommending a topology, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **What already exists** — an existing API gateway, ingress, reverse proxy, or BFF already in the stack that a new decision would replace, extend, or sit beside; how many backend services currently exist (from `microservices-decision`'s output if it ran).

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

2. **Client/consumer types** — the distinct kinds of thing calling in: a browser SPA, an iOS app, an Android app, named external partners, an internal admin tool. "The frontend" is not precise once there's more than one.
3. **Backend surface count per client operation** — for a typical screen or operation, how many distinct backend services would a client otherwise need to call directly? One or two is not yet a problem; five or more, or a number that grows with every new service, is the signal this decision exists to catch.
4. **Divergence between client types** — do the different client types actually need different data shapes, payload sizes, or response granularity (a mobile client needing a trimmed payload vs a web client wanting the full record), or would one uniform response serve all of them equally well? Don't assume divergence — ask what's actually different.
5. **Aggregation need** — does any client operation require combining or joining data from multiple backend services into one response before the client can render, or is each call already a clean one-to-one mapping to a single service?
6. **Cross-cutting concerns and their current home** — auth checks, rate limiting, request logging/tracing, TLS termination: are these duplicated per-service today, and is that duplication causing real drift (different services enforcing auth differently) or just aesthetic distaste?
7. **Ownership** — who would own a shared gateway if one is built (a platform/infra team, or "everyone," which in practice means no one)? Who would own a BFF (the frontend team that consumes it, per `microservices-decision`'s per-service ownership norm)? A layer with no named owner is the same failure mode `microservices-decision` gates on for services.
8. **Team and consumer growth trajectory** — is a second or third client type genuinely planned, or is this being built for one client today "in case" more arrive? A layer built for hypothetical future clients pays its cost now for a benefit that may never materialize.

"We need a gateway" or "let's add a BFF" with items 2–5 unanswered is not valid input — a decision to centralize auth (item 6) without naming what's actually duplicated today is optimizing an assumption, not a measured problem.

**Pressure does not open the gate.** "The new mobile app ships next sprint, just give it its own BFF" is exactly the shape that produces a BFF nobody remembers the purpose of a year later. Naming items 2–5 costs one paragraph and is usually cheaper than building and later un-building the wrong layer.

---

## Challenge a proposed approach

If the user opens with the topology already chosen, put their reasoning under the gate, then test the specific claim against `topology-and-tradeoffs.md`:

- **"every serious system has an API gateway, let's add one"** — how many backend surfaces does a single client operation actually call today (item 3)? A backend with one or two services behind one client type gains an operational hop and a new single point of failure for a problem — duplicated cross-cutting logic, unmanageable fan-out — that doesn't exist yet at that scale.
- **"let's give the new mobile app its own BFF"** — does its data need actually diverge from the existing client's (item 4), or is this "BFF because it's the pattern"? A BFF that returns the same shape as the existing client's could instead be a shared gateway serving both, or the existing surface as-is. Name the specific divergence.
- **"one shared gateway will handle every client, mobile, web, and partners"** — do those three actually want the same response shape and the same latency/payload tradeoffs (item 4)? A gateway trying to be all things to all consumers accretes conditional logic per-consumer and becomes the exact "second monolith nobody wants to touch" this skill exists to prevent. If needs genuinely diverge, that argues for BFFs behind a thin shared layer, not one endpoint serving three shapes.
- **"skip the intermediary, clients can call services directly, it's simpler"** — how many services does one screen need (item 3), and does that number grow every time a service is added? Beyond a couple of calls per operation, every client (web, iOS, Android) ends up re-implementing the same fan-out and stitching logic, and every client now has to know the backend's internal topology — a change to service boundaries becomes a multi-client-release event.
- **"the BFF will just be a thin proxy, no real logic"** — is that true today, or will it be true in six months? A BFF is signing up for its own ownership, deploys, and on-call the moment it exists (item 7) — that cost is paid whether or not logic stays thin, and thin proxies have a well-documented habit of accumulating business rules once they're the easiest place to add one.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `topology-and-tradeoffs.md` once the gate is satisfied. In short: name the client types and what each actually needs (items 2, 4) → count backend surfaces per typical operation (item 3) → name whether aggregation is genuinely required or a clean pass-through would do (item 5) → check what's duplicated today among cross-cutting concerns and whether that duplication is actually hurting (item 6) → name an owner for any layer proposed (item 7) → weigh planned growth against building for a hypothetical (item 8) → recommend one of: direct-to-service, shared gateway, BFF-per-client-type, or a shared gateway fronting BFFs → record.

Reference file:

- `topology-and-tradeoffs.md` — the four topology shapes (direct, shared gateway, BFF-per-client, hybrid), what each earns and what it costs, the "second monolith" failure mode of an overloaded shared gateway, the "BFF sprawl" failure mode of duplicated logic across BFFs with no shared owner, and where each cross-cutting concern (auth, rate limiting, logging, TLS) typically centralizes and why.

---

## Output

**1. In chat, a recommendation block:**

```
Client types:         <each distinct consumer, and what's actually different about its needs>
Backend surfaces:      <how many services a typical client operation touches today>
Divergence:            <do client types need different shapes/payloads, or would one response serve all — name the specific difference or "none observed">
Aggregation need:      <does any operation require joining data across services before a client can use it, or is each call a clean 1:1>
Topology:              <direct-to-service | shared API gateway | BFF-per-client-type | shared gateway + BFF(s)>
What it owns:          <aggregation, auth termination, rate limiting, logging — named per layer if hybrid>
What stays elsewhere:  <rate-limit mechanics → resilience-strategy; cost → technical-cost-decision; auth scheme → access-control-modeling/cloud-iam-boundary; new layer's own wire protocol → api-interface-style>
Owner:                 <named team for each layer introduced, or UNASSIGNED>
Tradeoffs accepted:    <2-4 concrete costs: an extra hop's latency, an operational surface with its own on-call, duplicated logic across BFFs, a shared gateway's blast radius>
Not chosen because:    <one line per rejected topology>
Follow-ups:            <resilience-strategy for centralized rate limiting/circuit breaking; technical-cost-decision for managed-vs-self-hosted; api-interface-style for the new layer's surface style; access-control-modeling/cloud-iam-boundary for the auth scheme itself>
```

Any field you cannot fill from the user's own words is `UNANSWERED`. A block with `UNANSWERED` fields on items 2–5 ends the response.

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering). Fill "Revisit when" with a concrete trigger — "a third client type arrives with a data need the current layer can't serve without new conditional logic", "the shared gateway's codebase grows past what any one team can review", "two BFFs converge on near-identical logic (consider merging)", "auth divergence across services becomes a measured incident, not a hypothetical."

Then stop. Implementation — the gateway config, the BFF service, the routing rules — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked the decision — client types named, divergence checked against real needs rather than assumed, ownership accounted for — and wants a review or a tie-break rather than a Socratic pass, they can say so and get a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "We have a web app today, calling our five services directly through no intermediary — that's worked fine. Now we're building a mobile app. Mobile needs much smaller payloads (bandwidth-constrained) and typically needs data from three of the five services combined into one screen. iOS and Android will share the same needs. No other client types planned. Auth today is checked independently in each of the five services using the same JWT validation code copy-pasted into each — that's already caused one bug where a token-expiry check drifted out of sync in one service."

Gate satisfied. Client types: web (existing, direct-to-service, no complaints) and mobile (iOS+Android, identical needs to each other). Backend surfaces: mobile needs 3 of 5 services combined per screen (item 3) — real aggregation need (item 5). Divergence: mobile genuinely needs a trimmed, combined payload the web client doesn't (item 4) — not assumed, stated. Cross-cutting: JWT validation duplicated across all 5 services with a demonstrated drift bug (item 6) — a real, not hypothetical, problem. Recommendation: **BFF for mobile** (iOS+Android share one, since their needs are identical — don't build two), owned by the mobile team, aggregating the 3 services and shaping the trimmed payload; leave the web client on direct-to-service since it has no complaint and no divergence to justify a second BFF. Separately, given the JWT drift bug is real and pre-dates this decision: recommend centralizing auth validation as a shared library or a thin shared edge check in front of both paths — named as a `resilience-strategy`/`access-control-modeling`-adjacent follow-up, not solved by the BFF itself (the BFF should call already-authenticated services, not become the only place auth is checked). Tradeoffs: mobile BFF adds one hop and one on-call surface for the mobile team; web stays as-is, so two topologies coexist (name this explicitly, don't pretend it's uniform). Not chosen: a shared gateway for both (web has no divergence need, would be pure overhead); a BFF for web too (no stated need). Follow-ups: auth-duplication fix → `access-control-modeling`; mobile BFF's own client-facing protocol → `api-interface-style`. ADR; revisit when a third client type arrives or the JWT-drift fix is designed.

> "Should we put an API gateway in front of everything?"

Gate not satisfied — item 2 (how many client types, and what's different about them), item 3 (how many services does one client operation touch today), item 4 (do those client types' needs actually diverge). Response: ask what's calling in today, how many services a typical request touches, and whether there's a real, named problem (duplicated logic, an unmanageable fan-out, a security drift) versus "it's the pattern." Do not recommend a topology.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Vocabulary (gateway, BFF, edge) is provider-neutral and transfers across cloud/on-prem. Copy the `bff-gateway-placement/` directory into another repo's `.claude/skills/` to use it there.
