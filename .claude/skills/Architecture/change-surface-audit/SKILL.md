---
name: change-surface-audit
description: A pre-flight procedure run against one proposed add / modify / remove change — or a "silent" change like a dependency upgrade, config change, or infra update — before it ships. Walks the six blast-radius surfaces a change can silently touch (API, data, state, performance, security, observability), and for a removal specifically audits the hidden dependents (API consumers, DB/ETL/analytics consumers, feature-flag debt, cached data/CDN, UI dead paths) before anything is deleted. Classifies the change as backward-compatible or breaking, and a breaking change or a removal must carry a compatibility/deprecation phase (add → dual-write/deprecate → backfill/audit consumers → switch/remove) before it's called safe to ship. Use when someone says "what could this change break", "am I missing anything before I ship this", "is this a breaking change", "we're removing this endpoint/column/feature — what do we need to check first", "before adding this feature, what should I think about", "PR review for blast radius", or names a dependency bump / config change / infra update and asks what it touches. Not for the diff's own correctness or cleanup — that's `code-review` / `security-review`, which read the code itself; this skill reasons about what the change breaks *elsewhere* in the system that reading the diff won't reveal. Not for what a change *obligates you to publicly disclose* — a new tracking pixel, analytics SDK, AI/LLM call, or third-party data-sharing flow that has to be reflected in the privacy policy, cookie banner, or subprocessor list — that's `disclosure-gap-audit`; it takes the disclosure half while this skill takes the blast radius, and the two compose on one change. Not for proactively enumerating every way a whole, not-yet-decided design could fail across nine categories with nothing specific proposed yet — that's `failure-mode-analysis`, exhaustive and design-wide; this skill is reactive to one already-proposed, concrete change. Not for picking the rollout mechanism (canary / blue-green / feature-flag-gated) once a change is confirmed safe to ship — that's `deployment-strategy`, which this skill hands the compatibility phase to for staging. Not for a live system-to-system migration (replatforming, datastore replacement, hosting move) — that's `migration-cutover`, a whole system moving to a new implementation, not one feature's own lifecycle inside a system that isn't changing. Not for picking the protection mechanism for an overload or dependency risk this surfaces — that's `resilience-strategy`. Not for the schema/table design itself once a data change is confirmed, or for sizing a scaling change — that's `relational-modeling` / `database-architecture` / `data-tier-operations`. Not for the API's versioning scheme or DTO/error shape — that's `api-interface-style`. Not for where a config value or secret should live — that's `config-and-secrets-management`. Not for writing the changed file's own standing orientation/companion doc (role, public surface, edges, gotchas) — that's `codebase-file-orientation`; it documents the file, this traces what the change breaks elsewhere, and the two compose on one change. A bare conceptual question with no specific change in hand ("what's expand-contract", "what counts as a breaking change") is answered directly, no audit.
---

# Change Surface Audit

Most production incidents don't come from a stage of the SDLC failing — they come from an
*unsafe transition*: a change that looked additive, or looked like "just removing dead code,"
that turned out to invalidate an assumption somewhere else in the system. This skill takes
one concrete, already-proposed change and asks the question that actually matters —
**"what assumptions does this change invalidate?"** — not "what code do I need to write?"

It is a mechanical pre-flight walk, not a Socratic gate: it doesn't withhold judgment
pending a user rep, but it does need the change itself, in concrete terms, before it can
say anything useful.

## When to use

- A specific, already-decided change is about to ship and someone wants its **blast
  radius checked** — "what could this break", "am I missing anything before I ship this".
- Someone asks whether a change is **backward-compatible or breaking**, or proposes a
  migration order to check ("can I just change the schema and deploy?").
- A **removal** is proposed — an endpoint, a column, a feature flag, a UI route — and the
  question is what depends on it before it's deleted.
- A **dependency upgrade, config change, or infra update** is being made and treated as
  "not really a feature change" — these are the changes most likely to skip review, and
  they touch the same surfaces a feature change does.
- A PR or design is up for review and the ask is specifically about **risk/blast radius**,
  not code quality.

## Out of scope — hand these off

- **The diff's correctness, style, or cleanup opportunities** — that's `code-review` /
  `security-review`. Those read the code as written; this skill reads the *system* the code
  lands in and asks what else it touches.
- **What the change obligates you to publicly disclose** — a new pixel / SDK / AI call /
  data-sharing flow that must land in the privacy policy, cookie banner, or subprocessor
  list → `disclosure-gap-audit`. This skill takes the blast radius (what breaks); that one
  takes the disclosure gap. They compose on the same change.
- **Proactive, whole-design failure enumeration with nothing specific decided yet** —
  "what could go wrong with this architecture" across all nine categories → `failure-mode-analysis`.
  That skill is exhaustive over a design; this skill is scoped to one proposed change.
- **The rollout mechanism** once a change is confirmed safe or the compatibility phase is
  planned — canary, blue-green, feature-flag-gated release, environment progression →
  `deployment-strategy`. This skill decides *whether* a compatibility phase is needed and
  what it must contain; that skill decides *how* the rollout is staged and what aborts it.
- **A live system-to-system migration** — replacing a datastore, replatforming, moving
  hosting providers → `migration-cutover`. That is a whole system moving to a new
  implementation with its own cutover pattern and rollback window; this skill is one
  feature's add/modify/remove lifecycle inside a system that is *not* itself changing.
- **Picking the protection mechanism** for an overload or dependency risk this audit
  surfaces (a new call path with no timeout, a hot new query with no cap) →
  `resilience-strategy`.
- **The schema/table design itself**, once a data-model change is confirmed, or sizing a
  scaling change → `relational-modeling` / `database-architecture` / `data-tier-operations`.
- **The API's versioning scheme, DTO shape, or error format** → `api-interface-style`.
- **Where a config value or secret should live**, once a config change is confirmed →
  `config-and-secrets-management`.
- **Who is allowed to do what**, if the change touches permissions/roles/tenancy →
  `access-control-modeling`.
- **A bare conceptual question** — "what's expand-contract", "what counts as a breaking
  change" — answered directly, no audit.

---

## Inputs the procedure needs

Don't invent a change to audit. If any of these are missing, ask and stop.

1. **The change type** — Add / Modify / Remove / Silent (a dependency upgrade, config
   change, or infra update that isn't being treated as a "feature" at all).
2. **The concrete change** — not "we added a feature," but the actual surface: the
   endpoint/route, the column/table/enum value, the config key, the dependency name and
   version delta. Restate it in concrete terms before walking anything.
3. **Current consumers/usage, if known.** If unknown — "we don't actually know who calls
   this" — that becomes the first audit action (go find out: logs, access grants, contract
   registries), not an assumed "probably nobody."
4. **Whether backward compatibility is even the goal here.** Occasionally a hard break is
   intentional (a security fix that must break old clients). Name that up front — it
   changes what "done" looks like, but it doesn't skip the audit of who gets broken and how
   they're told.

---

## The procedure

Work `surface-checklist.md` and `removal-and-silent-changes.md` alongside these steps.

### 1. Classify and restate the change

State the type (Add/Modify/Remove/Silent) and the concrete surface from input 2. This is
the thing every later step is checked against — get it wrong and the whole walk is void.

### 2. Walk the six surfaces

From `surface-checklist.md`: **API, Data, State, Performance, Security, Observability.**
For each — does this change touch it, what's the specific risk here, what question
resolves it. Applies to Add and Modify directly; for Remove and Silent changes, walk the
same six surfaces against the *thing being removed or changed*, not just the code diff.
Mark a surface `n/a — <reason>` rather than silently skipping it.

### 3. For Modify — classify compatible vs. breaking

If an existing consumer would notice the contract, behavior, or the *meaning* of a state
value changing, it's breaking, regardless of how small the diff looks (a status enum
gaining a new value is breaking for every branch that assumed the old exhaustive set). A
breaking modify requires the **expand-contract sequence** — add the new shape, write to
both / support both, backfill, switch reads, remove the old shape — read in full from
`removal-and-silent-changes.md`. This skill confirms the sequence is *planned*, not
skipped; the actual environment-by-environment staging of that rollout is
`deployment-strategy`'s.

### 4. For Remove — audit hidden dependents

From `removal-and-silent-changes.md`: API consumers (audited from logs/registries, never
assumed), DB/ETL/analytics/export consumers, feature flags and config referencing the
removed path, cached data and CDN entries, UI routes/deep-links/bookmarks. Every dependent
found gets a **deprecate-before-remove** step, not delete-then-discover. A removal with no
known consumers still gets a deprecation window unless the audit that ruled consumers out
is named and dated.

### 5. For Silent changes — the same six-surface walk, applied to the change itself

Dependency upgrades, config changes, and infra updates are the changes most likely to skip
review because they don't look like "a feature." Walk them through the same six surfaces:
the version's changelog (or the config diff, or the infra change) is the thing under
review, and what it touches downstream is the interaction. See
`removal-and-silent-changes.md` for the specific probes (semver lies, transitive
dependency bumps, a config default that changes silently, an infra change that alters
latency or defaults nobody coded against).

### 6. Name the assumptions this change invalidates

Answer directly: what did other parts of the system assume that stops being true after
this ships? (An exhaustive enum. A field that was never null. A response time nobody
timed out on. A cache key format nobody thought would collide.) This is the output that
actually predicts the incident — more than the surface checklist alone.

### 7. Emit the report and recommend a lane

- **Backward-compatible, no removal involved** → safe to ship as a normal change; hand the
  rollout mechanics to `deployment-strategy` if the unit's own release process is itself in
  question.
- **Breaking, or a removal is involved** → needs a compatibility phase / deprecation
  window before it ships. Name the phase's steps and the point of no return (the first
  step that can't be undone — the old-schema drop, the old-consumer's last known caller
  going quiet, the cache/CDN purge). Hand the staged rollout to `deployment-strategy`; for
  a removal, write the deprecation record (below).

---

## Output

**1. In chat**, a summary block:

```
Change:              <type — Add/Modify/Remove/Silent>  ·  <concrete surface>
Surfaces touched:     API <y/n+risk> · Data <..> · State <..> · Performance <..> · Security <..> · Observability <..>
Compatibility:        <backward-compatible | breaking> — <why>
Hidden dependents:    <count found, source of each — logs/registry/config scan — or "audited, none found">
Assumptions invalidated: <the 2-4 that matter>
Point of no return:    <n/a for a compatible add, else the specific irreversible step>
Recommendation:        <ship | needs compatibility phase | needs deprecation window>
Handoffs:              deployment-strategy <rollout staging> · resilience-strategy <n> · relational-modeling/database-architecture <n> · access-control-modeling <n>
```

**2. For a Remove that needs a deprecation window**, write a deprecation record to
`docs/engineering/deprecations/<slug>.md`: the concrete thing being removed, the consumer
audit (source, date, findings), the deprecation window and end date, the point of no
return, and a status field updated as consumers migrate off. This is a small living
document in the same spirit as `migration-cutover`'s rollback window — it exists because a
removal is a one-way door that plays out over time, not a point-in-time decision. Add and
Modify (once compatible) get no persistent file — the chat report is the artifact, same as
`document-page-check`.

Then stop. Designing the actual compatibility code, the deprecation notices, and the
rollout staging are separate, explicitly started steps that consume this report.

---

## Example invocations

> "We're adding a `suspended` value to `order.status`. What do I need to think about
> before shipping this?"

Type: Modify. Surface: State (the enum), plus every consumer that branches on status —
Data (any check constraint or index assuming the old set), API (any response schema
enumerating valid statuses), Observability (any dashboard/alert filtering by status).
Compatible? No — every `switch`/`if` over the old three-value enum is now missing a case,
which is silent-failure-shaped, not a loud one. Breaking. Sequence: ship the new value
accepted-but-unused first, audit every consumer for exhaustive-match handling, add the
`suspended` branch everywhere it's missing, *then* start emitting it. Assumptions
invalidated: "status is one of {active, inactive}" is now false everywhere. Recommend:
needs a compatibility phase before the value is ever emitted; not a removal, no
deprecation record needed.

> "We want to delete the `/v1/legacy-search` endpoint, nobody uses it anymore."

Type: Remove. "Nobody uses it" is the assumption to audit, not accept — check access logs
for real traffic in a real window, check partner/API-key registries, check if anything
internal (a cron, a script, a dashboard) still calls it. If the audit genuinely turns up
zero callers over a stated window, record that and the removal can skip a live deprecation
window but still needs the mechanical cleanup pass (route, handler, any feature flag
gating it, any cached responses, any doc/link referencing it). If it turns up even one
low-traffic caller, standard path: deprecate (return a deprecation header / log a warning),
set an end date, remove after the window closes with no more traffic. Point of no return:
the day the route handler is deleted. Write the deprecation record.

> "We're bumping our HTTP client library from 2.x to 3.x."

Type: Silent. This is exactly the change most likely to skip review. Walk the six
surfaces against the version delta: does the changelog show a default timeout/retry
behavior change (Performance/Resilience), a TLS/cert-validation default change (Security),
a breaking change to how errors surface (API/Observability — does your error-mapping code
still catch what this version throws), a new required config (Data/Operational). Even with
zero code changes on your side, the behavior of every call through this client just moved.

> "Is this endpoint doing anything wrong?" (a diff is pasted, no mention of what it
> connects to or breaks)

Not this skill primarily — that's a code-quality read → `code-review`. If the user
actually wants the blast-radius question, ask which one they mean; don't run both by
default.

---

## Portability

Repo-agnostic. Writes a deprecation record only for removals with a live deprecation
window, to `docs/engineering/deprecations/`. Copy the `change-surface-audit/` directory
into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits
among the sibling skills.
