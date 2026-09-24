# Style Tradeoffs

One entry per style: what it is, what it fits, what it costs, which consumers it rules out, and how it fails when misapplied. Use this in step 4 of `selection-framework.md` and in "Challenge the framing" in `SKILL.md`.

---

## REST / HTTP-JSON

**What it is.** Resources addressed by URL, standard HTTP verbs (GET/POST/PUT/PATCH/DELETE), JSON bodies, stateless requests. Optionally described by OpenAPI.

**Fits when.** Fixed, predictable resources with CRUD-shaped access. Broad, heterogeneous, or unknown clients. Public APIs where ubiquitous tooling, HTTP caching, and "integrators already know it" matter. The team wants the lowest-friction option.

**Costs.**
- Over-fetch (fields you don't need) and under-fetch (N round trips for related data) on rich screens.
- No schema unless you bolt on OpenAPI and keep it honest.
- Streaming and server push are awkward — they're a different transport (SSE/WebSocket) bolted alongside.

**Rules out.** Nothing. Anything that speaks HTTP can call it.

**Failure mode.** A mobile home screen that fans out to six endpoints and discards half of each payload. An "event feed" implemented as a 5-second poll loop. A bidirectional flow faked with long-polling.

---

## GraphQL

**What it is.** A single endpoint; the client sends a typed query naming exactly the fields it wants across a graph of types; the schema is the contract. Mutations for writes, subscriptions for push.

**Fits when.** Many *distinct* client query shapes — several frontends, or one frontend with many screens each needing a different slice. Rapidly-evolving UI where you don't want a new endpoint per view. Aggregating several backends behind one graph. Over/under-fetching is a *measured* pain, not a worry.

**Costs.**
- Server complexity moves up: N+1 resolution, query-cost limiting, depth limiting, persisted queries.
- HTTP-layer and CDN caching are mostly lost (everything is a POST to one URL); caching moves into the app.
- Performance is harder to reason about — one endpoint, unbounded query variety.
- Overkill for a single client with stable screens.

**Rules out.** Nothing hard — but a plain client without a GraphQL library is unpleasant. Fine in browsers.

**Managed implementations.** A hosted GraphQL layer (AWS AppSync, Hasura) trades the resolver/query-cost-limiter build-out above for a managed service, and typically throws in subscriptions (real-time push on data change) and offline client sync for free — genuinely useful when the fit is already GraphQL and those two features are wanted, not a reason to pick GraphQL on their own. It doesn't remove the fundamental costs above (caching still moves into the app, query variety is still unbounded) — it just moves who operates the resolver layer.

**Failure mode.** Adopted for one client with fixed screens: you now operate a query planner and cost-limiter for no measurable benefit over REST.

---

## gRPC

**What it is.** RPC over HTTP/2, Protocol Buffers binary serialization, generated client/server stubs from a `.proto`, first-class unary / server-stream / client-stream / bidirectional-stream methods.

**Fits when.** Internal service-to-service calls on a hot path — high call volume, latency- and bandwidth-sensitive. Polyglot backend that benefits from generated typed stubs. Streaming between services.

**Costs.**
- Not natively callable from browsers — needs grpc-web plus a translating proxy.
- Binary payloads aren't human-readable: no `curl`, harder debugging, needs tooling to inspect.
- External partners generally expect REST; a `.proto` is a barrier to integration.
- Extra build step (protoc / buf) and generated-code management.

**Rules out.** Browser clients (without grpc-web + proxy). External/public consumers in practice.

**Failure mode.** Exposed as the public or partner API — integrators bounce off the binary framing and `.proto`, and you end up maintaining a REST translation layer anyway.

---

## WebSocket

**What it is.** A persistent, bidirectional TCP connection upgraded from an HTTP request; either side sends frames at any time.

**Fits when.** Genuinely two-way, low-latency, stateful sessions — chat, collaborative editing, multiplayer games, live trading, an interactive dashboard that both streams and accepts commands.

**Costs.**
- Stateful connections to manage: horizontal scaling with sticky routing or a shared pub/sub backplane, reconnection logic, heartbeats, backpressure.
- Not cacheable; sits outside normal HTTP request/response observability.
- More operational burden than any request/response style.
- Overkill when traffic is only server→client.

**Rules out.** Little — broad browser support. Some corporate proxies and load balancers need explicit configuration for the upgrade and long-lived connections.

**Failure mode.** Chosen for one-directional notifications where SSE would do the job with a fraction of the moving parts.

---

## Server-Sent Events (SSE)

**What it is.** A one-way server→client stream over a single long-lived HTTP response; the browser's `EventSource` handles auto-reconnect and last-event-id resume.

**Fits when.** Server→client live updates only — notifications, activity feeds, job progress, dashboards, streaming tokens from an LLM. The client still uses ordinary HTTP requests to send anything back.

**Costs.**
- One-directional by design.
- Under HTTP/1.1, counts against the per-host connection limit (a non-issue over HTTP/2).
- Some proxies buffer the response and defeat the streaming unless configured.

**Rules out.** Nothing meaningful — native in browsers, trivial elsewhere.

**Failure mode.** Passed over in favour of WebSocket because "real-time" was assumed to require bidirectional, importing all of WebSocket's connection-management cost for a one-way feed.

---

## Webhooks

**What it is.** When an event occurs, you send an HTTP POST with the event payload to a URL the consumer registered in advance.

**Fits when.** Notifying external or third-party systems of events — integration platforms, low-to-moderate-frequency significant events, any consumer that wants push instead of polling your API.

**Costs.**
- You must build: delivery retries with backoff, ordering/dedup (or explicit "no ordering" contract), signature/HMAC verification so consumers can trust the payload, a replay/redelivery endpoint, and a dead-letter path for consumers that stay down.
- The consumer must expose a public HTTPS endpoint and stay reachable.
- One firehose webhook for every event type gets noisy — consumers want to subscribe to specific types.

**Rules out.** Consumers behind a firewall or NAT with no inbound endpoint. Browser clients.

**Failure mode.** Shipped without retries or signature verification → events are silently lost when the consumer blips, and deliveries can be spoofed. Consumers that can't host an endpoint are simply excluded.

---

## Async messaging (queue / broker)

**What it is.** The producer writes a message to a queue or topic (SQS, Kafka, RabbitMQ, NATS, ...); consumers read at their own pace; the broker holds the messages and the delivery state.

**Fits when.** Decoupling producers from consumers, buffering load spikes, fanning one event out to many consumers, work that can complete out of band, at-least-once processing with replay.

**Costs.**
- Eventual consistency — the caller does not get a synchronous answer.
- A broker to run, scale, secure, and pay for.
- End-to-end tracing and debugging span a hop through infrastructure.
- Not a request/response fit without correlation-id plumbing and a reply queue — at which point you've rebuilt RPC with extra latency.

**Rules out.** Public-API consumers — this is an internal integration shape; consumers need broker credentials and a client library.

**Failure mode.** Used where the caller needs the result now: you've added latency, a broker, and correlation plumbing to reimplement a synchronous call.

---

## Combining styles is normal

Most real systems run more than one. A single surface picks a **primary** and, where one sub-case doesn't fit, a **secondary** for exactly that sub-case:

- REST for CRUD **+** SSE for a live status feed.
- REST at the public edge **+** gRPC between internal services.
- A synchronous request/response API **+** webhooks so consumers learn about events without polling.
- GraphQL for the app's reads **+** async messaging for background processing behind the mutations.

Naming a primary and a secondary is a complete answer. Stretching one style to cover a shape it's bad at — polling for real-time, long-polling for bidirectional, a reply queue for RPC — is the thing to avoid.

---

## Decision-shape cheat table

| If the dominant need is… | Start from |
|---|---|
| CRUD over stable resources, broad or public clients | **REST** |
| Many client-driven query shapes across several frontends, measured over-fetching | **GraphQL** |
| Internal service-to-service, hot path, high volume, or inter-service streaming | **gRPC** |
| Bidirectional low-latency stateful session | **WebSocket** |
| Server→client live updates only | **SSE** |
| Push events to external systems | **Webhooks** |
| Decouple producers/consumers, buffer spikes, fan-out, process out of band | **Async messaging** |

The table is a starting point, not the decision. Run it through steps 2–4 of `selection-framework.md` against the actual consumers and constraints.
