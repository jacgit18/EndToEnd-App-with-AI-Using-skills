# ADR Template

Copy the block below to `docs/architecture/decisions/NNN-<slug>.md`. `NNN` = next integer after the highest existing ADR (zero-padded to 3), `<slug>` = short kebab-case topic (e.g. `billing-source-of-truth`). Fill every field. No `TBD` in Context or Decision.

---

```markdown
# NNN. <Short title of the decision>

- **Status:** Accepted
- **Date:** <YYYY-MM-DD>
- **Deciders:** <who approved this>

## Context

<What data / feature this is about. The gate answers, stated plainly:
consumers and which are boundaries; database ownership; internal vs. exposed;
stage / expected rate of change; the user's stated leaning and reasoning.
2–5 short paragraphs or a tight bullet list. Enough that someone with no
memory of the conversation understands the situation.>

## Decision

- **Approach:** <database-first | code-first | contract-first>
- **Source of truth:** <the authoritative artifact>
- **Persistence:** <database technology>
- **Database modeling:** <SQL migrations | ORM schema | ...>
- **Application access:** <ORM | query builder | generated client | raw SQL>
- **Validation:** <where runtime validation is defined / generated from>
- **Mapping boundary:** <e.g. "DB row → domain model → API DTO at the HTTP layer" / "none — single internal consumer">
- **Generated (do not hand-write):** <list of derived artifacts>

## Consequences

**Accepted costs**
- <concrete cost 1>
- <concrete cost 2>

**Rejected alternatives**
- <approach>: <one line on why not>
- <approach>: <one line on why not>

**Revisit when**
- <the condition that would reopen this decision — e.g. "a second service needs this data" or "the API becomes public">
- <a migration-cost trigger — e.g. "single-node write throughput becomes the ceiling" or "this store's licensing/hosting cost crosses $X/mo" — the point where the chosen technology, not just the source of truth, is back on the table>
```

---

## Notes

- One ADR per decision. If billing and notifications need different source-of-truth calls, that's two ADRs.
- If persistence wasn't already fixed (see "When persistence isn't decided yet" in `SKILL.md`), the paradigm/technology choice is its own earlier ADR (`NNN-<slug>-persistence.md`). This ADR's **Persistence** field then just references it.
- ADRs are append-only. To change a past decision, write a new ADR that references and supersedes it, and set the old one's Status to `Superseded by NNN`.
- The "Revisit when" line is the point of the whole document — it's what lets a future reader (or Claude) know whether the decision still holds.
