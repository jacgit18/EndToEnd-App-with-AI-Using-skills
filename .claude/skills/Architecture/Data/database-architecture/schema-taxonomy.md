# Schema Taxonomy

Rule: never use "schema" unqualified. State which of these you mean every time. They overlap and are often generated from one another, but they are distinct artifacts and must not be assumed to have the same shape.

| Term | What it is | Enforces | Lives in |
|---|---|---|---|
| **Database schema** | The store's structure — tables/columns/constraints (relational), collection + document shape + indexes (document), node/edge labels + properties (graph) | Relational: `NOT NULL`, `UNIQUE`, foreign keys, checks, referential integrity. Stores without these enforce **nothing** — the invariant must move to application code | SQL migrations / declarative schema / index definitions |
| **Domain model** | Business concepts and their rules | Invariants expressed in code | Application code |
| **API schema** | The shapes crossing a boundary — request/response, or event/message payloads | What callers may send and will receive; what subscribers will be sent | OpenAPI / GraphQL / protobuf (sync); AsyncAPI (events, webhooks) |
| **Validation schema** | Runtime input checking | Rejects malformed input at the edge | Zod / Yup / io-ts / JSON Schema |
| **Type definitions** | Compile-time representation | Nothing at runtime — a `TS interface` is a hint, not a constraint | `.ts` / type stubs |

## The trap

```ts
interface User {
  id: string;
  email: string;
  createdAt: Date;
}
```

This is a **type definition**. It describes what the code *expects*. It does not tell you whether `email` is `UNIQUE` in the database, whether `id` is a foreign key target, or whether `createdAt` can be null. A type can be accurate and the database can still have different rules. Do not treat an interface as evidence of the database schema, or vice versa.

## Interface vs. contract

An interface describes data **for your code**. A contract describes an **agreement between systems** — it additionally pins formats (`format: uuid`, `format: email`), required-ness across the wire, versioning, and compatibility guarantees. From a contract you can generate types, validators, docs, and client SDKs. From an interface you can generate... the interface.

## Boundaries that aren't HTTP request/response

A contract boundary can be an event stream, a message queue, or an outbound webhook. The payload a webhook sender commits to, or the event shape on a topic, is an **API schema** in the table above — pin it with **AsyncAPI** the way you'd pin a REST surface with OpenAPI, and run it through the mapping boundary (step 5 of `decision-framework.md`) exactly like a response DTO: the database row does not get to be the webhook body by default.

When several consumers depend on a payload you emit and you can't coordinate their release cycles, **consumer-driven contract testing** (Pact) is the mechanism that keeps you from breaking them — their expectations become executable checks against your side.

## What this means for a recommendation

- When someone says "let's make the schema the source of truth", ask *which* schema.
- The database schema becoming the API schema by default is the specific failure the mapping boundary (step 5 of `decision-framework.md`) exists to prevent.
- Generating type definitions from a database schema is fine and common. Generating your *public API* from it is a decision, not a default.
- A webhook you send or an event you publish is a boundary. If the gate surfaced consumers of a payload you emit, that payload needs its own contract and mapping step — not just the inbound handler.
