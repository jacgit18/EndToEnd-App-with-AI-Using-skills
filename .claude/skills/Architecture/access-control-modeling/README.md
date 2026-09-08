# access-control-modeling skill

A gated decision for **who may do what to which resource inside the application** — the
authorization model (flat RBAC, hierarchical RBAC, ABAC, ACL, or ReBAC), the actors/resources/
actions being protected, permission granularity (resource-type vs per-instance vs per-field),
multi-tenancy isolation, and where the check is enforced (app-layer, database row-level
security, or both). Not authentication (unowned — name and defer), not cloud/infra identity
(that's `cloud-iam-boundary`), not the actual table DDL (that's `relational-modeling`).

Built from `Architecture/Security/Authentication vs Authorization.md` — the AuthN/AuthZ split
this skill's scope boundary sits on ("confirming if the requester is allowed to perform the
intended action," and the note that hiding a frontend feature is a UX layer, not the control
itself).

## Where it sits

```
design-scoping              →  states the compliance/isolation constraint this system lives under
access-control-modeling      →  who may act, on what, at what granularity, enforced where   (this skill)  → ADR
relational-modeling           →  designs the users/roles/permissions tables this skill names as entities
cloud-iam-boundary             →  the infra-identity counterpart — same question, different principal (a service, not a user)
caching-strategy                →  the TTL/invalidation for a cached permission decision this skill flags as cacheable
microservices-decision           →  which service owns a permission check, cross-service auth propagation
```

## The shape

A gate skill. It refuses to recommend a role/permission model or an enforcement layer until the
user supplies:

- **a concrete need** — a feature to restrict, an audit finding, multi-tenancy being added
- **the actors** — the distinct kinds of principal, not "users"
- **the protected resources and actions** — specific verbs per resource type, not "everything"
- **granularity** — resource-type, per-instance, or per-field (the biggest cost driver)
- **the model shape** — flat RBAC by default; hierarchy, ABAC, ACL, or ReBAC only when flat RBAC
  can't express the stated granularity
- **the tenancy shape** — single-tenant, shared-schema + `tenant_id` (+ RLS backstop),
  schema-per-tenant, or database-per-tenant
- **the enforcement layer(s)** — app-layer guard / policy engine / DB row-level security, and
  whether a decision is cached
- **delegation and audit** — who administers roles, and what's logged

Then it picks the smallest model that expresses the stated granularity, the tenancy isolation
that fits the actual constraint (not the most paranoid option by default), names the enforcement
layers, hands the entity list to `relational-modeling`, and writes an ADR.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 2–10 from the user), challenge-the-proposal, output contract. |
| `authorization-models.md` | Flat/hierarchical RBAC, ABAC, ACL, ReBAC — what each is, when to reach for it, permission naming, static vs dynamic role→permission mapping. |
| `enforcement-and-tenancy.md` | App-layer guard vs policy engine vs DB row-level security; the three tenancy isolation shapes and their backstops; caching a permission decision; the standard entity list handed to `relational-modeling`. |

## Output

1. A recommendation block in chat (need, actors, protected resources, granularity, model,
   tenancy, isolation backstop, enforcement, caching, delegation/admin, audit requirement,
   entities to model, tradeoffs, follow-ups).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (a role needs to vary
   per-instance — retrofit to ABAC/ReBAC; a compliance requirement forces database-per-tenant;
   the permission count per role stops being readable as a flat list).

Stops before implementation (the actual middleware/policy-engine code, RLS policies, migrations).

## Interaction with sibling skills

- **Distinct from `cloud-iam-boundary`** — same shape of question (who may act, on what, how is
  it bounded) at a different altitude: that skill's principal is a service, pipeline, or
  cross-account caller reaching a cloud resource; this skill's principal is an application end
  user (or an integration acting on one's behalf) reaching an application resource. They compose
  when one action needs both (an "admin" app role that also triggers an AWS console grant) —
  name both ADRs rather than folding one into the other.
- **Feeds `relational-modeling`** — the entity list (`users`, `roles`, `permissions`,
  `role_permissions`, `user_roles` + tenancy column) is named here; the actual DDL, keys,
  indexes, and constraints are designed there.
- **Hands off to `caching-strategy`** — a cached permission decision's staleness bound is stated
  here; the TTL/invalidation mechanism is designed there.
- **Hands off to `microservices-decision`** — which service is the source of truth for a
  permission check, and cross-service token/claim propagation, is that skill's territory once
  more than one service is involved.
- **Authentication is unowned** — login, sessions, JWT/OAuth2, password/credential handling. This
  skill assumes a trusted, already-authenticated principal exists to check against; name the
  authentication gap explicitly rather than designing it here.
- **Consumes `design-scoping`** — a named compliance/isolation constraint from that skill's
  output shapes the tenancy decision (gate item 7); also defers there outright for an unscoped
  system with no named actors or resources yet.

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk is
with `cloud-iam-boundary` (app-user vs infra-identity principal, both phrased as "who can access
X") and `relational-modeling` (naming entities vs designing their schema).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`
and reuses its `adr-template.md`. Framework-neutral vocabulary; if the repo already uses a policy
engine (Casbin, OPA, CASL) or an IdP with role/group claims (Auth0, Cognito, Okta), map the
recommendation onto its actual primitives during the gate rather than inventing a parallel system.

```
cp -r ".claude/skills/Architecture/access-control-modeling" /path/to/other-repo/.claude/skills/
```
