# Enforcement and Tenancy

Where the check in `authorization-models.md` actually runs, and how tenants stay isolated from
each other. Backs gate items 7–9.

## Where the check lives

| Layer | What it is | Strength | Weakness |
|---|---|---|---|
| **Frontend / UI hiding** | Hide a button or route the user can't use | None as a security control | Never enforcement — a direct API call bypasses it entirely. Fine as a UX convenience *on top of* a real check, never a substitute for one. |
| **Application-layer guard** | A middleware/decorator/policy function run before the handler executes | Centralizes the check in one place; easy to unit-test in isolation | Only as strong as every code path remembering to call it — a new route that forgets the guard is unprotected |
| **Policy engine** (Casbin, OPA, CASL, a framework's built-in authorization module) | Externalizes the rule set from business logic into a declarative policy, evaluated by a shared library | Single source of truth for the rules; rules are reviewable and testable independent of the routes that use them; scales past a handful of ad hoc `if` checks | A dependency and a learning curve; overkill for two roles and three resources |
| **Database row-level security** (Postgres RLS) or a scoped view | The database itself refuses to return or modify rows outside the current session's allowed scope | Enforced even if application code forgets — the strongest backstop for "wrong tenant sees your data" specifically | Policies are SQL predicates, not workflow logic — awkward or impossible for anything shaped like "only if the invoice is still in draft and it's before the approval deadline" |

**Default recommendation:** an application-layer guard (or a policy engine once the rule count
justifies it) for anything resource-type or business-logic-shaped, plus row-level security as a
backstop specifically for tenant isolation (gate item 7) — not as a replacement for the app-layer
check, because RLS can't express most real authorization rules, only "which rows belong to this
session's tenant." Using RLS as the *only* layer means every permission rule has to be shoehorned
into a row-visibility predicate; using it as a backstop means a forgotten `WHERE tenant_id = ?`
fails safe instead of leaking.

## Multi-tenancy isolation

| Shape | What it is | Backstop against a forgotten filter | Ops cost | Fits |
|---|---|---|---|---|
| **Shared schema + `tenant_id`** | One set of tables, every tenant-scoped row carries a `tenant_id` column, the app filters by it | None by default — add row-level security keyed on `tenant_id` to make this safe | Lowest — one schema to migrate and operate | The common default; most tenant counts, unless a compliance requirement forces stronger isolation |
| **Schema-per-tenant** | Each tenant gets its own Postgres schema (or equivalent) with identical table structure | Structural — a query connected to the wrong schema simply can't see another tenant's tables | Migration fan-out (every schema change runs N times); connection/pool management gets more complex | Dozens to low hundreds of tenants, when isolation needs to be stronger than a column but a full separate database per tenant is too costly |
| **Database-per-tenant** | Each tenant gets an entirely separate database (or cluster) | Structural and strongest — no shared connection can reach another tenant's data at all | Highest — per-tenant backup, restore, scaling, and monitoring | Enterprise/compliance-driven isolation requirements (a named regulatory or contractual constraint from `design-scoping`), or tenant counts low enough that per-tenant ops cost is acceptable |

Pick shared-schema-plus-RLS by default; move to schema- or database-per-tenant only when a
*named* constraint (a customer contract, a compliance regime, a specific isolation guarantee
already promised) requires it — not because it sounds more secure in the abstract. The migration
from shared-schema to schema-per-tenant later is a real, costly project; naming the constraint
now (or confirming there isn't one) is what gate item 7 is for.

## Caching a permission decision

If a check's result is cached for performance (common under load — re-evaluating a role or
policy on every request has a real cost), the cached decision can outlive a permission change:
a user demoted or removed can keep the old decision until the cache entry expires or is
invalidated. State two things explicitly: the staleness bound (how long a revoked permission may
still be honored — often driven by how sensitive the action is; a cached "can view" decision
tolerates more staleness than a cached "can delete") and the invalidation trigger (does a role
change actively bust the cache, or does it only expire on TTL?). Hand the concrete staleness
requirement to `caching-strategy` for the TTL/invalidation mechanism itself — this skill only
states that the requirement exists and how strict it is.

## The entity list to hand to `relational-modeling`

Once the model (flat/hierarchical RBAC, ABAC, ACL, ReBAC) and tenancy shape are chosen, name the
entities and relationships — don't design the DDL here:

- **`users`** — the principal.
- **`roles`** — for RBAC; omit entirely for pure ABAC/ACL/ReBAC.
- **`permissions`** — the `resource:action` list from `authorization-models.md`.
- **`role_permissions`** — junction, role ↔ permission (RBAC only).
- **`user_roles`** — junction, user ↔ role; add a `tenant_id`/`org_id` column here directly if a
  role applies only within one tenant rather than globally (a user can be `admin` of org A and
  `member` of org B — the role assignment, not the role definition, is tenant-scoped).
- **Per-instance ownership** — for granularity beyond resource-type (gate item 5), either an
  `owner_id` column directly on the protected resource's own table (simplest — most per-instance
  ownership is exactly this), or a separate `resource_grants(user_id, resource_id, permission)`
  table when a single resource can be shared with multiple, specific principals (the ACL case).
- **The permission-editing surface itself**, if permissions are dynamic (`authorization-models.md`)
  — it is a protected resource too (`permission:edit`), not an unguarded admin page.

Hand this list, with the tenancy column/table decided, to `relational-modeling` for normal form,
keys, indexes (an index on `user_roles(user_id)` and `user_roles(tenant_id, role)` are the
near-universal ones this schema needs), and constraints.
