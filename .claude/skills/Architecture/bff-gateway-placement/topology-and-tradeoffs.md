# Topology shapes and their failure modes

Reference for the process step in `SKILL.md`. Four shapes, in order of how much is placed between a client and the backend services it ultimately needs.

## Direct-to-service (no intermediary)

Each client calls each backend service it needs directly, over whatever protocol `api-interface-style` chose for that surface.

**Earns its keep when:** one client type, or client types whose needs don't diverge; a small number of services per client operation (one or two); no measured cross-cutting drift.

**Cost:** every client (web, iOS, Android, partner integrations) independently implements any fan-out or stitching a screen needs, and independently encodes which service owns what. Adding a service, splitting one, or renaming an endpoint becomes a multi-client-release event instead of a change behind one boundary.

**Failure mode:** the client-side call count per screen grows quietly as the backend grows, until a screen makes eight calls to five services and every client team is maintaining its own ad hoc aggregation logic — the exact problem a gateway or BFF exists to centralize, just paid for in duplicated client code instead of one owned layer.

## Shared API gateway

One layer, in front of all consumers, fronting the same responses to every client type — typically owning auth termination, rate limiting, TLS termination, and routing; sometimes a thin aggregation layer too.

**Earns its keep when:** cross-cutting concerns (auth, rate limits, logging) are genuinely duplicated and drifting across services; client types don't need meaningfully different response shapes — a gateway serving one shape well beats a gateway with per-consumer conditional branches.

**Cost:** one more operational hop and a single point of failure for every client; someone has to own it, and "the platform team" or "everyone" both tend toward "no one" without an explicit `Owner` field, same as an unowned service in `microservices-decision`.

**Failure mode — the second monolith.** A gateway that tries to serve every client's diverging needs accretes per-consumer conditional logic (`if (client === 'mobile') { trim the payload }`) until it is itself a tangled, high-blast-radius component nobody wants to touch — the same failure `microservices-decision` warns about for an unbounded monolith, just relocated to the edge. The fix when this happens is usually to split diverging consumers out into their own BFFs behind the gateway (the hybrid shape below), not to keep adding conditionals.

## BFF per client type

A dedicated aggregation/shaping layer for one client type (or one frontend team), owned by the team that consumes it, calling the backend services on the client's behalf and returning exactly the shape that client needs.

**Earns its keep when:** client types have genuinely different data/payload/latency needs (mobile wants a trimmed payload; web wants the full record; a partner API wants a stable versioned contract); real aggregation is needed (a screen needs data from several services joined into one response) and that logic shouldn't be re-implemented per client.

**Cost:** each BFF is its own deployable, with its own on-call, its own deploy pipeline, its own set of things that can break — the same headcount-and-ownership arithmetic `microservices-decision` applies to backend services applies here. A BFF with no named owner is exactly as orphaned as an unowned service.

**Failure mode — BFF sprawl.** Building a BFF per client "because that's the pattern," without a divergence that justifies it, produces two or three near-identical BFFs that duplicate the same aggregation logic with no shared owner watching for drift between them. If two BFFs converge on doing the same thing, that's a signal to merge them or extract the shared logic into a library or a shared gateway layer, not to keep them separate for symmetry. A BFF that starts as "just a thin proxy" and accumulates business rules over time has quietly become an undocumented extra service outside whatever boundaries `microservices-decision` settled on — name that when it happens rather than letting it drift.

## Hybrid — shared gateway fronting BFFs

A shared edge layer owns the cross-cutting concerns common to every consumer (auth termination, rate limiting, TLS, logging/tracing), and routes to per-client-type BFFs behind it that handle aggregation and shaping specific to each client.

**Earns its keep when:** both problems are real at once — genuine cross-cutting duplication *and* genuine per-client divergence. This is usually the right shape once a system has grown past two client types with different needs, since it avoids both the second-monolith failure (shared concerns don't leak into each BFF) and BFF sprawl (each BFF doesn't re-implement auth/rate-limiting).

**Cost:** the most moving parts of the four shapes — two layers to own, deploy, and reason about instead of one. Don't reach for this as a starting point for a system with one client type; it's the shape you grow into, not the shape you start with.

## "Reverse proxy vs API gateway vs load balancer" isn't one choice

These three terms get conflated because a real system commonly runs all three at once, at different layers, solving different problems — not because they're competing answers to the same question.

| Term | What it actually solves | Who decides it |
|---|---|---|
| Load balancer | Distributing traffic across replicas of the *same* service so no one instance is overloaded | `deployment-strategy` / `resilience-strategy` (the need arises from running more than one instance); `capacity-estimation` for how many replicas |
| Reverse proxy | TLS termination, hiding origin servers, often response caching | `caching-strategy` if the question is response caching; `cloud-iam-boundary` if it's network placement/exposure |
| API gateway / BFF | Routing and shaping traffic across *multiple, different* services for one or more client types | This skill |

Ask which concern is actually in question before reaching for this skill's gate — "we're adding a second instance of the checkout service" is a load-balancer question this skill doesn't own; "our mobile and web clients need different data from our 6 services" is this skill's gate.

## Where cross-cutting concerns typically centralize

| Concern | Typical home | Why |
|---|---|---|
| Auth termination (validate a token, check a coarse permission) | Shared gateway, if one exists | One place to fix a drift like an out-of-sync expiry check, instead of N copies in N services |
| Fine-grained authorization (can *this* user do *this* action on *this* resource) | Per-service, or a policy engine each service calls | The gateway usually doesn't have the domain context to make a resource-level call — see `access-control-modeling` |
| Rate limiting — coarse, per-client-key | Shared gateway or edge | Attributable at the point clients first hit the system |
| Rate limiting / concurrency limiting — saturation-aware, per-dependency | In-process, per-service | The gateway can't see a service's own event-loop lag or connection-pool saturation — see `resilience-strategy` |
| Request logging / tracing correlation ID | Shared gateway (assign it) + every service (propagate it) | Needs to exist before the first hop and survive every hop after |
| TLS termination | Edge / shared gateway | Avoids re-terminating per-service |
| Response aggregation / shaping for one client | The client's own BFF, not the shared gateway | Keeps client-specific logic out of the shared layer, avoiding the second-monolith failure |
