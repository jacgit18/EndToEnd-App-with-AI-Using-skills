# Selection Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR's Context and Decision.

## 1. Name the surface and its two ends

One sentence: what interface this is, who is on each end, and who owns the release cycle of each end.

- "The browser SPA (we ship it) ↔ our backend (we ship it)."
- "External developers (we don't control them) → our public API."
- "The orders service → the inventory service (both ours, deployed independently)."
- "Our system → partner systems, on shipment events (they register a URL)."

If this turns out to be several surfaces with different consumers, stop and split — each surface gets its own pass and its own ADR. If it turns out the real question is whether these should be separate services at all, that is `microservices-decision` first.

## 2. Classify the interaction shape

Pin the dominant shape. Most surfaces have one; some have a primary plus one sub-case.

| Shape | What flows | Natural styles |
|---|---|---|
| **request → response** | client asks, server answers, done | REST, GraphQL, gRPC unary |
| **server → client push** | server sends updates on its own schedule; client doesn't ask each time | SSE, WebSocket, webhooks |
| **client → server stream** | client sends a sequence (upload, telemetry) | gRPC client-streaming, WebSocket |
| **bidirectional session** | both ends send at will over a live connection | WebSocket, gRPC bidi-streaming |
| **fire-and-forget events** | producer emits, doesn't wait, consumers process later | webhooks (external), async messaging (internal) |

Write the shape, and name any secondary shape ("request/response for the CRUD, plus server→client push for a live status feed").

## 3. Map consumers to protocol constraints

For each consumer type from the gate, write what its platform allows. This eliminates candidates before you score them.

- **Browser** — REST, GraphQL, SSE, WebSocket: yes. Raw gRPC: no (needs grpc-web + a proxy). Consuming webhooks: no (can't host an endpoint).
- **Mobile app** — all of the above; long-lived WebSocket connections cost battery and fight flaky networks.
- **Your own backend services** — anything, including gRPC and a message broker. This is where gRPC and async messaging are on the table.
- **External partners / third-party developers** — expect REST + JSON + OpenAPI. May accept GraphQL. Rarely accept gRPC. Can consume webhooks *only if* internet-reachable with an HTTPS endpoint.
- **Unknown public** — REST is the safe default; every other choice narrows your addressable integrators.

If a consumer can't be reached the way a style needs (webhook consumer behind a firewall, browser needing gRPC), that style is out for that surface — or the surface needs splitting by consumer.

## 4. Score the survivors

Take the styles that cleared steps 2 and 3 and weigh them against the rest of the gate, using `style-tradeoffs.md`:

- **Data / query shape** — fixed resources → REST. Many client-driven query shapes across several frontends, with *measured* over/under-fetching → GraphQL. RPC-style operations → gRPC (internal) or REST action endpoints.
- **Latency & throughput** — hot internal path, high call rate, tight budget → gRPC (HTTP/2, binary, small frames). Ordinary user-facing CRUD → the binary win doesn't matter; optimize for tooling and clarity.
- **Real-time need** — server→client only → SSE. Bidirectional → WebSocket. "Within a minute is fine" → don't build a streaming transport; a poll or a webhook is simpler.
- **Team & ecosystem** — what the team already runs, debugs, and monitors comfortably. A style nobody can operate under load is the wrong style regardless of its fit on paper. An existing style in the same service needs a positive reason to diverge from.
- **Public / stability** — a published boundary rewards boring and universal (REST) and punishes anything that makes integrators install tooling or read a `.proto`.

## 5. Pick the primary, name the secondary

State the **primary style** for the surface and why, in one or two sentences tied to the gate answers — not to general reputation.

If one sub-case genuinely doesn't fit the primary (CRUD API that also needs a live feed; sync API that also emits events), name the **secondary style** for exactly that sub-case and its boundary. Two styles for two shapes is a correct outcome. Do not stretch the primary to cover a shape it's bad at just to have one answer.

## 6. List what you're deferring

Name each downstream decision this surface still needs, and where it goes:

- **Contract source-of-truth** — is OpenAPI / the GraphQL schema / the `.proto` authoritative, or generated from code? → `database-architecture`.
- **Versioning strategy** — URI vs header vs query, deprecation policy. → its own decision; note it's needed.
- **Auth scheme** — API key, OAuth2, mTLS, session — by consumer class and data sensitivity. → its own decision.
- **Gateway / BFF** — does a gateway or backend-for-frontend sit in front, and does it own auth / rate limiting / aggregation? → `bff-gateway-placement`, which decides the topology; `technical-cost-decision` if it's purely about managed-vs-self-hosted cost once a topology is chosen.
- **Cost at volume** — if the call/event rate is large enough to drive infrastructure cost. → `technical-cost-decision`.

The implementer must not treat "style chosen" as "API designed" — this list is what's left.

## 7. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR from `adr-template.md` to `docs/architecture/decisions/NNN-<slug>.md`.
