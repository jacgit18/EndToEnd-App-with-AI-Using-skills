# ADR Template

Copy the block below to `docs/architecture/decisions/NNN-<slug>.md`. `NNN` = next integer after the highest existing ADR (zero-padded to 3), `<slug>` = short kebab-case topic (e.g. `public-api-style`, `frontend-backend-transport`, `orders-inventory-rpc`). Fill every field. No `TBD` in Context or Decision.

---

```markdown
# NNN. <Short title of the decision>

- **Status:** Accepted
- **Date:** <YYYY-MM-DD>
- **Deciders:** <who approved this>

## Context

<Which surface this is and its two ends. The gate answers, stated plainly:
consumers and which are boundaries you don't control; the interaction shape
(request/response, server-push, streaming, bidirectional, events); the
data/query shape and whether over/under-fetching is measured; latency and
throughput; the real-time need and its direction; consumer reachability and
platform limits; public vs internal and how stable it must be.
2–5 short paragraphs or a tight bullet list — enough that a reader with no
memory of the conversation understands the situation.>

## Decision

- **Primary style:** <REST | GraphQL | gRPC | WebSocket | SSE | webhooks | async-messaging>
- **Serialization:** <JSON | Protocol Buffers | ...>
- **Secondary style:** <style for a named sub-case, e.g. "SSE for the live order feed" — or "none">
- **Interaction shape:** <request-response | server-push | client-stream | bidirectional | events>
- **Consumers covered:** <each client type and how it reaches the surface>

## Consequences

**Accepted costs**
- <concrete cost 1 — from style-tradeoffs.md, specific to this surface>
- <concrete cost 2>

**Rejected alternatives**
- <style>: <one line on why not, tied to a gate answer>
- <style>: <one line on why not>

**Deferred (not decided here)**
- Contract source-of-truth (contract-first vs code-first) → `database-architecture`
- Versioning strategy → <needed; owner / when>
- Auth scheme → <needed; owner / when>
- Gateway / BFF → <`bff-gateway-placement`, or "not needed">

**Revisit when**
- <the condition that would reopen this — e.g. "a second frontend appears with a different query shape", "this internal call becomes a public API", "the event rate crosses the point where a broker is cheaper than webhook fan-out", "browser support becomes a requirement">
```

---

## Notes

- One ADR per surface. If the public API and the internal service-to-service calls are different surfaces, that's two ADRs.
- This ADR does **not** record where the contract's source of truth lives — that's a `database-architecture` ADR, and it may point back to this one.
- ADRs are append-only. To change a past decision, write a new ADR that references and supersedes it, and set the old one's Status to `Superseded by NNN`.
- The "Revisit when" line is the point of the document — it tells a future reader whether the choice still holds.
