# api-interface-style skill

A gated decision for **how one API surface talks** — the protocol and interaction model, not
where its schema lives and not how many surfaces there are. Given a surface that needs to
exist, the skill makes the user state its consumers, the interaction shape, and the query /
latency / real-time needs before any style is named, then recommends a primary style (plus a
secondary for a sub-case where needed) and writes an ADR.

Covers REST, GraphQL, gRPC, WebSockets, SSE, webhooks and async messaging; data vs. RPC-style
APIs; frontend vs. backend callers; and managed GraphQL (AppSync) in `style-tradeoffs.md`.

## Where it sits

```
microservices-decision   →  whether to split, and where the service boundaries go
api-interface-style       →  how one surface talks: REST / GraphQL / gRPC / WS / SSE /
                             webhooks / async messaging   (this skill)
database-architecture     →  where the authoritative definition lives: contract-first vs
                             code-first; OpenAPI / GraphQL schema / protobuf as source of truth
technical-cost-decision   →  managed gateway vs self-hosted, cost at request/event volume
bff-gateway-placement     →  whether a shared gateway / BFF sits in front of multiple
                             services or client types at all (this skill's protocol choice
                             applies to that layer's own surface, once its topology is picked)
```

`api-interface-style` and `database-architecture` are the two halves of "design the API" and
are **orthogonal**: you can be contract-first with gRPC or code-first with REST. This skill
picks the wire protocol and interaction model; `database-architecture` decides which artifact
is authoritative. Each skill's ADR may reference the other's.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The 8-item gate, challenge-the-framing, output contract. |
| `selection-framework.md` | The 7-step process, worked once the gate is satisfied. |
| `style-tradeoffs.md` | Each style — fit, cost, ruled-out consumers, failure mode — plus the "combining styles is normal" note and a decision-shape cheat table. |
| `adr-template.md` | The ADR block for this decision, with a Deferred section pointing at sibling skills. |

## What it produces

1. A recommendation block in chat (surface, primary + secondary style, serialization,
   interaction shape, consumers covered, accepted tradeoffs, rejected alternatives, deferred
   decisions).
2. An ADR written to `docs/architecture/decisions/NNN-<slug>.md`.

Stops before the contract, handlers, resolvers, and SDKs.

## Deliberately out of scope

- Contract source-of-truth (contract-first vs code-first) → `database-architecture`.
- Whether to split into services / where boundaries go → `microservices-decision`.
- Cost-sizing against volume, managed-vs-self-hosted gateway → `technical-cost-decision`.
- Schema / table design behind the API → `relational-modeling` / `dimensional-modeling`.
- Replication, sharding, pooling, transaction patterns → `data-tier-operations`.
- Versioning mechanics, auth-scheme selection — the skill *names* that each is needed and
  defers it.
- Whether a shared gateway or BFF sits in front of multiple services/clients at all →
  `bff-gateway-placement`.
- Implementation of any kind.

## Dependencies

Needs no repo setup; output paths are defaults the repo's own convention overrides. The
siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Installed in other projects via the plugin described in
`plugins/README.md`.

## Interaction with sibling skills

Re-check overlap when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `database-architecture`** — that skill's description also mentions "API shape" and
  "should we use GraphQL". The split is protocol/interaction-model (here) vs
  source-of-truth (there). Both descriptions carry a disclaimer pointing at the other.
- **vs `microservices-decision`** — this skill assumes the surface already exists as a
  concept. If the real question is "should these be separate services", that runs first.
- **vs `technical-cost-decision`** — anything volume- or bill-driven (gateway cost, egress,
  per-request pricing) hands off; this skill only notes the trigger.
- **vs `bff-gateway-placement`** — that skill decides *whether* a gateway/BFF exists at all
  in front of multiple services or client types; this skill decides the protocol for one
  surface, including that layer's own client-facing surface once its topology is settled.
