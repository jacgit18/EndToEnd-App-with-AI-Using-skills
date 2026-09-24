# Authorization Models

The vocabulary and selection logic behind the gate's item 6. Built from `Architecture/Security/
Authentication vs Authorization.md` — the split it draws (identity vs "confirming if the
requester is allowed to perform the intended action") is the boundary this whole skill sits on.

## The models, in order of how much a static role can express

| Model | A grant looks like | Answers "who can do X" by | Cost it adds |
|---|---|---|---|
| **Flat RBAC** | user → role → permissions | Reading the role's fixed permission list | None beyond the role table itself |
| **Hierarchical RBAC** | user → role → (inherited roles) → permissions | Walking a role graph | Resolving inheritance; a role's effective permissions are no longer a flat read |
| **ABAC** (attribute-based) | a rule over attributes of user, resource, and context | Evaluating the rule against a specific instance | The grant is no longer enumerable — "list everyone who can do X" means evaluating the rule against every candidate, not reading a table |
| **ACL** (access control list) | a per-(subject, resource, action) entry | Looking up that specific pair | Doesn't summarize into roles; scales by number of grants, not number of roles |
| **ReBAC** (relationship-based) | access derived from a relationship graph (owner-of, member-of, parent-of) | Traversing the graph (is there a path from user to resource via an allowed relationship?) | Needs a graph-shaped store or query, not a permissions table |

**Default to flat RBAC.** It is the cheapest model to build, explain, and audit, and it correctly
expresses the common case: a small number of named roles, each with a fixed, resource-type-level
permission set (admin/member/viewer, each able to do a fixed list of things to any instance of a
resource type). Reach for something richer only when flat RBAC genuinely cannot express the
stated granularity (gate item 5) — don't adopt ABAC or ReBAC because they sound more correct.

**Add hierarchy** only once roles demonstrably nest — an `org_admin` who should have everything a
`member` has, plus more. Don't build a hierarchy for two roles that don't overlap; a flat list of
two is simpler than a graph of two.

**Reach for ABAC** when the rule that decides access references something that varies per
instance or per request and can't be captured as "you have this role": `resource.owner_id ==
user.id`, `resource.department == user.department`, "only during business hours," "only if the
invoice is still in draft status." The tell: if answering "can Alice edit this?" requires looking
at *this specific resource*, not just Alice's role, RBAC alone is the wrong tool.

**Reach for ACL** when grants are genuinely ad hoc and per-resource, not describable by any small
set of roles or attribute rules — document-sharing ("share this file with these three people"),
where the set of people who can access one instance has no pattern predictable from a role.

**Reach for ReBAC** when access follows a relationship or org graph rather than a role or a
single attribute check — "the owner, or anyone they've shared it with, or any member of a team
they've shared it with" is a graph traversal (owner-of ∪ shared-with ∪ member-of ∘ shared-with),
not a role and not a single attribute comparison. This is the Google-Docs/Zanzibar shape; it is
the most expressive and the most expensive to build and reason about — don't reach for it until
ACL and ABAC both fall short of the actual sharing pattern described.

These are not mutually exclusive in one system: a common real shape is flat RBAC for
coarse-grained actions (who can access the admin panel at all) layered with ABAC or ownership
checks for per-instance actions (can this specific user edit this specific invoice). Name both
layers rather than forcing one model to cover everything.

## Permission naming

Name permissions as `resource:action` (`invoice:approve`, `report:export`, `user:invite`), not
vague capability flags (`canEdit`, `isPowerUser`). A verb-scoped name is auditable on sight — a
reviewer can tell what it grants without reading the code that checks it — and composes cleanly
into a role's permission list without ambiguity about *which* resource "edit" applies to.

## Static vs dynamic role→permission mapping

**Static** — roles and their permissions are fixed in code (an enum, a config file checked into
the repo). Change requires a deploy. Correct default: fewer moving parts, the mapping is
reviewable in a pull request like any other code change.

**Dynamic** — an admin UI lets someone edit which permissions a role has, at runtime, stored as
data. Only justified once a non-engineer genuinely needs to change the mapping without a deploy
(a customer-facing "manage your team's permissions" feature, or an internal support tool). The
moment the mapping becomes editable data, it needs its own protection (gate item 9 — who can
edit the editor) and its own audit trail (item 10), because it is no longer reviewed the way code
is.
