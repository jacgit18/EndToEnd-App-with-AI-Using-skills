# change-surface-audit skill

A **pre-flight procedure** for one already-proposed, concrete change — add, modify, remove,
or a "silent" change (dependency upgrade, config change, infra update). It walks the **six
blast-radius surfaces** a change can silently touch (API, data, state, performance,
security, observability), classifies the change as backward-compatible or breaking, and for
a breaking modify requires the **expand-contract sequence**; for a removal it runs a
**hidden-dependents audit** (API consumers, DB/ETL/analytics consumers, feature-flag debt,
cached data/CDN, UI dead paths) before anything is deleted.

Built from `Architecture/Extra AI and decision points.md`'s "Feature changes" section — the
source note explains the risk categories and gives worked examples (the NOT NULL column,
the status-enum growth, the hidden removal dependencies) but no repeatable procedure and no
output format. The skill adds both (`SKILL.md` the 7-step walk, `surface-checklist.md` the
six-surface probes, `removal-and-silent-changes.md` the expand-contract sequence, the
removal audit, and the silent-changes walk).

## Where it sits

This is a **procedure skill, not a decision-gate** — the same shape as
`Documents/document-page-check` and `Architecture/failure-mode-analysis`. It does not
withhold judgment pending a user rep; it needs the concrete change in hand, then runs a
walk and produces a report.

```
change-surface-audit   →  walk ONE proposed change across 6 surfaces, classify compatible/breaking   (this skill)
      │
      ├─ rollout staging (canary/blue-green/flag-gated) →  deployment-strategy
      ├─ overload/dependency risk this surfaces         →  resilience-strategy
      ├─ schema/table design once confirmed             →  relational-modeling / database-architecture
      ├─ scaling change sizing                           →  data-tier-operations
      ├─ API versioning scheme / DTO shape               →  api-interface-style
      ├─ config value's storage/rotation                 →  config-and-secrets-management
      ├─ permissions/roles/tenancy touched               →  access-control-modeling
      └─ new pixel/SDK/AI call/data-sharing flow → must disclose  →  disclosure-gap-audit
```

`change-surface-audit` runs against **one concrete, already-decided change**. Its
whole-design counterpart `failure-mode-analysis` runs proactively across an entire design
with nothing yet decided. Its code-quality counterpart is the built-in `code-review` /
`security-review` — those read the diff itself; this skill reads what the diff touches
*elsewhere*.

## The shape

Not a rep gate, but it needs the change to audit: the type (add/modify/remove/silent), the
concrete surface (not "a feature" — the actual endpoint/column/config key/dependency),
known consumers if any, and whether backward compatibility is even the goal. Missing input
gets asked for, not invented.

The walk:

1. Classify and restate the change.
2. Walk the six surfaces (API, Data, State, Performance, Security, Observability),
   `n/a — <reason>` where one doesn't apply.
3. For Modify — classify compatible vs. breaking; a breaking one needs the
   expand-contract sequence.
4. For Remove — audit hidden dependents (never assume "nobody uses this").
5. For Silent changes — the same six-surface walk aimed at the dependency/config/infra
   diff instead of your own code.
6. Name the assumptions this change invalidates.
7. Emit the report and recommend a lane: ship / needs compatibility phase / needs
   deprecation window.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Inputs needed, the 7-step walk, the output block, the deprecation-record trigger, worked invocations. |
| `surface-checklist.md` | The six surfaces, each with probe questions, an example risk, and a per-change-type "heaviest surfaces" table. |
| `removal-and-silent-changes.md` | The expand-contract sequence with a worked NOT-NULL-column example, the five hidden-removal-dependency categories, the silent-changes walk (dependency/config/infra), and the deprecation-record format. |

## Output

1. A summary block in chat: change, surfaces touched, compatibility verdict, hidden
   dependents found, assumptions invalidated, point of no return, recommendation, handoffs.
2. **Only for a Remove needing a live deprecation window**: a small living document at
   `docs/engineering/deprecations/<slug>.md` — the consumer audit, the window, the point of
   no return, and a status field updated as consumers migrate off. An Add or a compatible
   Modify gets no persistent file, same as `document-page-check`.

Stops before writing the actual compatibility code, the deprecation notices, or the staged
rollout — those are separate, explicitly started steps that consume this report.

## Interaction with sibling skills

- **Distinct from `failure-mode-analysis`** — that skill is proactive and exhaustive across
  a whole design with nothing yet decided; this skill is reactive to one already-proposed
  change. If someone wants the whole-design version, route there instead.
- **Hands rollout mechanics to `deployment-strategy`** — this skill decides *whether* a
  compatibility phase is needed and what it must contain (the expand-contract steps); that
  skill decides how the rollout is staged, what environments gate it, and what aborts it.
  `deployment-strategy` already owns the *expand/contract discipline for schema and
  contract changes* at the rollout-mechanics level — this skill is the pre-flight check
  that decides a change needs that discipline in the first place, and feeds it the specific
  steps.
- **Distinct from `migration-cutover`** — that is a whole system moving to a new
  implementation (a datastore replacement, a replatform); this is one feature's lifecycle
  inside a system that isn't itself changing. A removal's "point of no return" borrows the
  same naming as that skill's rollback window, at a much smaller scale.
- **Feeds `resilience-strategy`** — a new call path with no timeout, or a hot new query
  with no cap, surfaced by the Performance/Dependency probes, is that skill's input.
- **Feeds `access-control-modeling`** — any change touching who can do what routes there
  for the actual model; this skill only flags that it's touched.
- **Not `code-review` / `security-review`** — those assess the diff's own correctness and
  quality; this skill assesses what the change breaks elsewhere in the system.

Run `skill-interaction-testing` after any trigger-description change here — the overlap
risk is with `failure-mode-analysis` (one-change vs. whole-design), `deployment-strategy`
(pre-flight vs. rollout-mechanics, both mention expand-contract), and `migration-cutover`
(feature removal vs. system migration, both use "point of no return").

## Using it in another repo

Repo-agnostic. Writes a deprecation record only for removals with a live deprecation
window, to `docs/engineering/deprecations/`.

```
cp -r ".claude/skills/Architecture/change-surface-audit" /path/to/other-repo/.claude/skills/
```
