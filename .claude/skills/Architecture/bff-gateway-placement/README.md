# bff-gateway-placement skill

A gated decision for **what sits between client applications and backend services** —
nothing (direct-to-service calls), a shared API gateway, a Backend-for-Frontend per client
type, or a shared gateway fronting BFFs. Given a backend with one or more services and more
than one kind of client calling into it, the skill makes the user name the actual client
types, how many backend surfaces a typical operation touches, and whether those clients'
needs genuinely diverge before any topology is on the table, then recommends one and writes
an ADR.

Built from an audit of `Architecture/Architecture Styles/` (the `Backend For Frontend (BFF)
Pattern.md` and `Micro-Frontend.md` notes) that found `api-interface-style` already promised
this hand-off — its "gateway / BFF placement" deferred item pointed at
`microservices-decision` — but `microservices-decision` never actually addressed it. This
skill closes that gap; the micro-frontend half of the source material (splitting the
*frontend* into independently-deployable pieces, a client-side team-boundary question) is a
distinct decision and was folded into `microservices-decision` instead, since it reuses that
skill's headcount/ownership arithmetic directly rather than needing its own gate.

## Where it sits

```
microservices-decision     →  how many backend services exist, and their boundaries
                               (also: frontend decomposition into micro-frontends)
bff-gateway-placement       →  what layer, if any, sits between clients and those services
                               (this skill)                                          → ADR
api-interface-style         →  the wire protocol for one surface, including this layer's
                               own client-facing surface once its topology is picked
resilience-strategy         →  the actual rate-limiting/circuit-breaking mechanism, once
                               this skill says where it centralizes
technical-cost-decision     →  managed-gateway-vs-self-hosted dollar cost
access-control-modeling /
cloud-iam-boundary          →  the auth scheme itself, once this skill says where it
                               terminates
```

## The shape

A gate skill, same family as `microservices-decision` and `api-interface-style`. It refuses
to recommend a topology until the user supplies:

- **client/consumer types** — not "the frontend," but which distinct kinds exist
- **backend surface count per client operation** — how many services a screen touches today
- **divergence** — do the client types' data/payload needs actually differ, checked, not
  assumed
- **aggregation need** — does anything require joining data across services before a client
  can use it
- **what's duplicated today** among cross-cutting concerns (auth, rate limiting, logging),
  and whether that duplication is a measured problem
- **ownership** for any layer proposed — an unowned gateway or BFF is the same failure mode
  `microservices-decision` gates on for an unowned service

Then it recommends one of four shapes (direct / shared gateway / BFF-per-client / hybrid),
names what the new layer owns vs defers elsewhere, and writes an ADR.

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/`.

```
cp -r .claude/skills/Architecture/bff-gateway-placement /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `microservices-decision`** — that skill decides how many backend services exist and,
  separately, whether the frontend splits into micro-frontends. This skill takes the service
  count as a given input and decides what a client talks to in order to reach them.
- **vs `api-interface-style`** — that skill decides the protocol for one surface. This skill
  decides whether an intermediary layer exists between clients and multiple surfaces; once
  it does, that layer's own client-facing surface goes back through `api-interface-style`.
- **vs `resilience-strategy`** — this skill says *where* a control like rate limiting
  centralizes (edge/gateway vs in-process); that skill designs the control itself.
- **vs `technical-cost-decision`** — anything bill-driven (managed gateway pricing) hands
  off once a topology narrows the options being priced.
