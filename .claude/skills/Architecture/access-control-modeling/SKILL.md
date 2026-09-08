---
name: access-control-modeling
description: A gated decision for how an application decides who may do what to which resource — the authorization model (flat RBAC, hierarchical RBAC, ABAC, ACL, or relationship-based/ReBAC), the actors/resources/actions being protected, permission granularity (resource-type vs per-instance vs per-field), multi-tenancy isolation (shared schema + tenant_id, schema-per-tenant, database-per-tenant), and where the check is enforced (application-layer middleware/policy engine, database row-level security, or both). Use when someone says "what roles should we have", "design the permissions system", "how do users relate to roles", "can a user have multiple roles", "admin vs member vs viewer", "row-level security or app-level checks", "multi-tenant permission model", "RBAC or ABAC", "a user should only see their own org's data", "who can approve/edit/delete X", or proposes a role/permission shape and wants it checked. It forces the user to name the actors, the protected resources and actions, the granularity, and the tenancy model before any role table or policy check is recommended, then records the outcome as an ADR. This is authorization (what a principal may do) — authentication (proving who they are: login, sessions, JWT/OAuth2 flows, password/credential handling) is a distinct, unowned concern; name it and defer. Not for cloud/infrastructure identity — which AWS/GCP/Azure resource may call which resource, a service's execution role, or network placement — that is `cloud-iam-boundary`, whose principal is a service, pipeline, or cross-account caller, not an application end user; the two compose when one action needs both (an admin role that also triggers an infra-level grant). Not for the actual table DDL, indexes, and constraints once the roles/permissions/user relationships are named as entities — that is `relational-modeling`, which this skill hands the entity list to. Not for which microservice owns a permission check as data, or cross-service auth-token propagation — that is `microservices-decision`. Not for whether a cached permission decision's TTL and invalidation are correct — that is `caching-strategy`, which this skill hands the staleness requirement to. Not for the broader blast radius of a specific change that happens to touch permissions ("we're adding a feature, does it need new roles" alongside API/data/state/other risk) — that is `change-surface-audit`, which audits the whole change first and hands the permissions question here once it's confirmed touched.
---

# Access Control Modeling

Take a system where more than one kind of user exists, or where a resource shouldn't be equally visible to everyone, and decide exactly which actors can do what to which resources, how that's structured (roles, attributes, relationships), how tenants stay isolated from each other, and where the check actually runs. The skill makes the user name the concrete actors, resources, and actions before any role table or `if user.isAdmin` check gets written, because "we'll add roles later" and "just check it in the frontend" are the two ways this decision goes wrong — the first gets expensive to retrofit once real data and endpoints assume a single trusted owner, and the second isn't authorization at all, it's a UI convenience sitting in front of an unprotected API.

## When to use

- Someone is **designing the permission system for a new feature or app** — "what roles do we need", "design access control for the admin panel", "how should permissions work for this".
- Someone is deciding **how roles/permissions relate to users and resources** — one role per user vs many, role hierarchy vs flat, a role that only applies within one organization/tenant.
- Someone is asking **RBAC vs ABAC vs ACL**, or "can a user see only their own data / their org's data" (ownership- or tenant-scoped access).
- Someone is deciding **where a permission check lives** — in application code, in the database (row-level security), in a policy engine (Casbin/OPA/CASL), or some combination.
- Someone is adding **multi-tenancy** to a system that didn't have it, or building it in from the start.
- Someone proposes a shape already-decided and wants it checked — "we'll just add an `isAdmin` boolean", "check the role in the frontend and hide the button", "filter by `tenant_id` in the app, that's enough".
- An **audit or incident** surfaced an access problem at the application level — a user saw another tenant's data, a non-admin reached an admin-only action, a role granted more than intended. (A `disclosure-gap-audit` security-pass finding of a missing authz check / IDOR / weak tenant isolation lands here for the model.)

## Out of scope — hand these off

- **Authentication** — proving who the caller is: login flows, session vs token, JWT/OAuth2 mechanics, password hashing and credential storage, MFA. No skill owns this yet in this catalog; name the requirement ("this still needs a login/session mechanism") and defer rather than designing it here. Authorization assumes a trusted, already-authenticated principal is available to check against.
- **Cloud/infrastructure identity and network placement** — which AWS/GCP/Azure resource may call which other resource, a Lambda's execution role, cross-account trust, VPC/subnet placement → `cloud-iam-boundary`. That skill's principal is a service, pipeline, or cross-account caller; this skill's principal is an application end user (or an API-key-holding integration acting on a user's behalf). The two compose when a single action needs both — e.g., an "admin" application role that also triggers an AWS console grant — name both skills' outputs as related but separate ADRs.
- **The actual schema** — table DDL, keys, indexes, constraints for `users`, `roles`, `permissions`, and their junction tables → `relational-modeling`, once this skill has named the entities and relationships. Don't design columns and indexes here.
- **Service boundaries and cross-service auth propagation** — which microservice is the source of truth for a permission check, or how an auth token/claim is verified across service calls → `microservices-decision`.
- **Caching a permission decision** — the TTL and invalidation trigger for a cached authorization result → `caching-strategy`, once this skill names that a check is cacheable and how stale it may get.
- **Code-level vulnerability scanning** — injection, broken access control found on a diff, insecure deserialization → `security-review`. This skill designs the intended model; that skill checks whether code actually implements it correctly.
- **An unscoped, not-yet-designed system** — "what should the permission system for our new product look like" with no named actors or resources yet → `design-scoping` first, which sequences a concrete feature back here.
- **A bare conceptual question with no named system** — "how does RBAC actually work", "what's the difference between RBAC and ABAC" — is answered directly, no gate. The gate exists for a pending decision on a named system, not for explaining the vocabulary.

---

## The gate

Before recommending a model, a schema shape, or an enforcement layer, these must be answered.

**Facts you may surface from the repo** (state them for confirmation):

1. **What already exists** — a `role` or `isAdmin` column, an existing `roles`/`permissions` table, an auth library already in use (Casbin, CASL, OPA, a framework's built-in guard system), or an identity provider (Auth0, Cognito, Okta) that may already carry role/group claims.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

2. **The concrete need** — what triggered this: a new feature needs restricting, an audit or incident found a hole, multi-tenancy is being added, a customer is asking for admin sub-roles. "We should probably have permissions" is not a need — it's a reason to ask what, specifically, needs restricting from whom.
3. **The actors** — the distinct kinds of principal in the system, named plainly: customer, org admin, support agent, an API-key-holding third-party integration. "Users" is not precise enough once there's more than one kind.
4. **The protected resources and actions** — what is being guarded, and the specific verbs on each: `invoice: view/edit/approve/delete`, `report: view/export`, not "everything" or "the app."
5. **Granularity** — is the decision made at the resource-*type* level (any invoice), per-*instance* (only invoices you or your org own), or per-*field* (can see the invoice but not the amount)? This is the single biggest cost driver: per-instance and per-field checks cannot be answered by a static role name alone.
6. **Role/permission structure** — flat named roles (admin/member/viewer), a role hierarchy with inheritance, or rules evaluated against attributes (department == resource.department, resource.owner == user.id, time-of-day)? Do roles apply globally or only within one tenant/org?
7. **Multi-tenancy** — does more than one customer/org share this system? If so: shared schema with a `tenant_id` filtered by the app, schema-per-tenant, or database-per-tenant — and what specifically stops a query that forgets the tenant filter from leaking another tenant's rows?
8. **Enforcement layer** — application-layer check (middleware/guard/policy function), database-level (row-level security, a scoped view), or both? If a decision will be cached, how stale may it be before a revoked permission is still honored?
9. **Delegation and administration** — can a user grant or modify another user's permissions (self-service admin), and who administers the roles/permissions themselves? The permission-editing surface is itself a protected resource — don't let it go unmodeled.
10. **Auditability** — does a role/permission change need to be logged, reviewed, or trigger an alert, and who owns that review?

"We should add roles" or "just restrict it to admins" with items 2–7 unanswered is not valid input.

**Pressure does not open the gate.** "We need to ship the admin panel today, don't overthink it" is a reason to ask for the fast path, not to skip the question: naming the actors (item 3) and the 3–5 actual admin actions (item 4) takes one sentence and is usually the only two items genuinely blocking a first cut — tenancy (item 7), enforcement layer (item 8), and audit (item 10) can default to the simplest honest answer (single-tenant, an app-layer guard, "not logged yet — flag as a gap") and be revisited later without a rewrite. Once the specific items actually challenged are answered, the gate releases — don't keep escalating to demand the full item 2–10 list when the user has given a good-faith answer to what was asked.

---

## Challenge a proposed approach

If the user opens with the shape already decided, put their reasoning under the gate, then test the specific claim against `authorization-models.md` and `enforcement-and-tenancy.md`:

- **"add an `isAdmin` boolean, that's enough"** — is this genuinely two flat, permanent classes, or is a third role, per-org scoping, or per-instance ownership coming? A boolean can't express "admin of your org, not every org" — retrofitting that later means touching every check that assumed the boolean. Name the actors (item 3) before collapsing to a flag.
- **"check the role in the frontend and hide the button"** — that's UX, not authorization. Hiding a button doesn't stop a direct API call from a browser console or a script. Where is the server-side check (item 8)? The frontend hint is fine *in addition to*, never *instead of*.
- **"just check `req.user.role === 'admin'` wherever it's needed"** — scattering the check across every handler means the day it's wrong in one place it stays wrong there, with no single place to audit or change the rule. Centralize into a guard/middleware/policy function even for two roles — the cost is the same either way, the payoff compounds.
- **"filter by `tenant_id` in the app, that's enough"** — what happens the day someone writes a query and forgets the `WHERE tenant_id = ?`? Is there a database-level backstop (row-level security) or is every current and future query trusted to remember (item 7)? Shared-schema tenancy without an RLS backstop is a single missed `WHERE` clause away from a cross-tenant leak.
- **"we'll add real permissions later once we have real customers"** — a single-tenant, single-role app still benefits from naming actors/resources/actions now (item 3–4), even if the model today is one implicit role; it's the retrofitting onto data and endpoints that assumed one trusted owner that's expensive, not the initial naming.
- **"one shared admin role that can do everything, simpler to reason about"** — simpler until the day one over-broad admin action is mis-clicked or a compromised admin account has no blast-radius limit. What are the 3–5 actual admin actions (item 4)? A narrower set, even split into two roles, costs little more to define.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `authorization-models.md` then `enforcement-and-tenancy.md` in order once the gate is satisfied. In short: name actors, resources, and actions (items 3–4) → decide granularity (item 5) → choose the model shape — flat RBAC, hierarchical RBAC, ABAC, ACL, or ReBAC (item 6) — using the smallest model that expresses the granularity actually needed → decide tenancy isolation and its backstop (item 7) → decide the enforcement layer(s) and any caching staleness bound (item 8) → decide who administers permissions and whether delegation is allowed (item 9) → name the audit requirement (item 10) → hand the entity list to `relational-modeling` for the schema → recommend and record.

Reference files:

- `authorization-models.md` — RBAC (flat and hierarchical), ABAC, ACL, and ReBAC: what each is, the failure mode it fixes, the cost it adds, and how to pick the smallest one that fits the stated granularity; permission-naming convention; static (code-defined) vs dynamic (runtime-editable) role→permission mappings.
- `enforcement-and-tenancy.md` — where a check lives (app-layer guard, policy engine, database row-level security) and when to use more than one layer; the three multi-tenancy isolation shapes and what backstops each against a forgotten filter; the standard entity list (`users`, `roles`, `permissions`, `role_permissions`, `user_roles`, tenant scoping) to hand to `relational-modeling`; caching a permission decision safely.

---

## Output

**1. In chat, a recommendation block:**

```
Need:                 <the concrete trigger from gate item 2>
Actors:               <the distinct principal kinds>
Protected resources:  <resource types and the actions on each>
Granularity:          <resource-type | per-instance | per-field>
Model:                <flat RBAC | hierarchical RBAC | ABAC | ACL | ReBAC> — and why this and not a simpler/richer one
Tenancy:              <single-tenant | shared-schema + tenant_id | schema-per-tenant | database-per-tenant>
Isolation backstop:   <row-level security | scoped views | app-only (name the risk accepted)>
Enforcement:          <app-layer guard/middleware | policy engine (name it) | DB row-level security | combination — and where in the request path>
Caching:              <cached decision + staleness bound, or "not cached"> — handed to caching-strategy if cached
Delegation/admin:     <who can grant/modify roles; self-service or admin-only>
Audit requirement:    <what's logged, who reviews — handed to observability-strategy if it needs alerting>
Entities to model:    <handed to relational-modeling — e.g. users, roles, permissions, role_permissions, user_roles(+tenant_id)>
Tradeoffs accepted:   <2–4 concrete costs — role-per-tenant admin overhead, RLS query-plan cost, policy-engine learning curve, etc.>
Not chosen because:   <one line per rejected shape — a flatter model, a richer one, app-only tenancy, etc.>
Follow-ups:           <relational-modeling for the schema; cloud-iam-boundary if an action also needs an infra-level grant; caching-strategy for a cached decision's TTL; observability-strategy for audit alerting>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering). Fill "Revisit when" with a concrete trigger — "a second tenant tier needs a stricter isolation guarantee", "a role needs to vary per-instance instead of globally (retrofit to ABAC/ReBAC)", "the permission count per role exceeds what's readable as a flat list (add hierarchy)", "a compliance requirement forces database-per-tenant".

Then stop. Implementation — the actual middleware/policy-engine code, the RLS policies, the migration — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — actors and resources named, granularity and tenancy decided against a real system, enforcement layer chosen with a stated reason — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "We're adding an org concept to our SaaS app. Actors: org owner, org member, and our own internal support staff. Owners can invite/remove members and edit billing; members can view and edit shared documents but not billing; support staff can view (not edit) any org's data for troubleshooting, logged. Everything's per-org — a member of org A must never see org B's documents. We're on Postgres, shared schema today, maybe a few hundred orgs. No per-document sharing outside the org yet."

Gate satisfied. Actors: org owner, org member, support (cross-tenant, read-only, audited). Resources/actions: `document: view/edit`, `billing: view/edit`, scoped per-org except support. Granularity: resource-type within an org (not yet per-document — noted as a future ReBAC trigger if per-document sharing is added). Model: flat RBAC, roles scoped by `org_id` (owner/member), plus a separate global `support` role with its own audited path — not folded into the org-scoped roles. Tenancy: shared schema + `tenant_id`(`org_id`) with Postgres row-level security as the backstop, since a few hundred orgs doesn't justify schema-per-tenant yet. Enforcement: app-layer guard for the role check, RLS policy on `org_id` as the backstop against a forgotten filter, and the support-staff path explicitly bypasses RLS through a logged, separate code path rather than a wildcard policy. Entities handed to `relational-modeling`: `users`, `orgs`, `org_memberships(user_id, org_id, role)`, plus RLS policy definitions. Audit: every support-staff read logged with actor + org + timestamp → `observability-strategy` for alerting on volume. ADR; revisit when per-document sharing across orgs is requested.

> "Just add an `isAdmin` flag to the users table, we need to ship the admin panel today."

Gate not satisfied — item 3 (is "admin" the only other actor, or are there org-scoped admins coming), item 4 (what specifically does the admin panel let an admin do — enumerate the 3–5 actions). Response: naming those takes one sentence and still ships today; the flag becomes the cost once a second tenant or a narrower admin role is needed and every check assumed a global boolean. Ask, don't design on the flag yet.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Written in framework-neutral vocabulary (roles, permissions, tenants); if the repo already uses a policy engine (Casbin, OPA, CASL) or an IdP with group/role claims (Auth0, Cognito), name it during the gate and let the recommendation map onto its actual primitives rather than inventing a parallel system. Copy the `access-control-modeling/` directory into another repo's `.claude/skills/` to use it there.
