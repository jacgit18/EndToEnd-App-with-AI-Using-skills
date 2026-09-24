# Orientation doc — format, rubric, and reconcile checklist

## The template

The sidecar doc is short and fixed-shape. Fill every section; a section with genuinely nothing to say
is dropped, not padded (except **Role**, which is always present).

```markdown
# <relative/path/to/file>

**Role.** <One to three sentences. The single job this file owns and why it exists as its own file.
Not a paraphrase of the top function, not a list of everything in it. If you can't name one job,
that's a finding — say the file has more than one responsibility.>

**Entry points.** <The public surface other code reaches for: exported functions / classes / types,
the CLI subcommand it registers, the HTTP route or handler, the event / queue subscription, the
config key it owns. For each, one clause on what a caller uses it for. If nothing is exported, say
so — it's a script or a side-effect module.>

**Depends on.** <The edges that matter, both directions:
  - outward — modules it imports whose behaviour it relies on, plus services / DB tables / queues /
    env vars / files / external APIs it touches;
  - inward — the callers that would break if this file's surface changed (grep for them; if the
    tree isn't available, write "inbound callers not traced — <reason>").
Skip framework/stdlib noise. Name the non-obvious ones.>

**Gotchas.** <What a careful reader still gets wrong. Ordering constraints ("must run after X"),
a global or singleton it mutates, an error path it swallows, a constant that must equal one in
another file, a workaround for a known upstream bug (link the issue), a performance cliff. Omit the
whole section if there are none — do not invent them.>

**Keep in sync.** <Other files or contracts that must change together with this one: the schema this
DTO mirrors, the client that speaks this protocol, the fixture that encodes this shape. Omit if the
file stands alone.>

<!-- Orientation doc: file-level "where". Local "why" belongs in comments at the relevant line. -->
```

## Belongs in the doc / in a comment / nowhere

| Fact | Where |
|---|---|
| "This module owns rate-limit accounting for the public API." | **Doc** — Role |
| "Exported `reserve()` / `release()`; callers: `middleware/limit.ts`, `admin/quota.ts`." | **Doc** — Entry points / Depends on |
| "Bucket refill must happen before the check or the first request of a window is rejected." | **Doc** — Gotchas (system-level constraint) *and* a short comment at the line if the ordering looks swappable |
| "We use a token bucket, not a sliding window, because Redis round-trips dominated the sliding-window version." | **Comment** at the algorithm — a rejected alternative and its reason, tied to a specific line |
| "`WINDOW_MS` here must equal `WINDOW_MS` in `client/backoff.ts`." | **Doc** — Keep in sync *and* a comment on the constant |
| "Increment `i` each loop." | **Nowhere** — the code says it |
| "TODO: extract the Redis calls behind an interface." | **Nowhere** — that's an issue / backlog item, not orientation |

Rule of thumb: if the fact is about **how this file relates to the rest of the system**, it's the doc.
If it's about **why one line is the way it is**, it's a comment. If the code already states it plainly,
it's neither.

## What the doc must not become

- **A line-by-line narration** of the file. If the doc would go stale on any refactor that keeps
  behaviour, it's describing implementation, not orientation.
- **A changelog.** History lives in git and the commit message (`commit-and-push`).
- **A design rationale essay.** One clause of "why it exists as its own file" in Role is the limit;
  deeper rationale is a comment or an ADR.
- **A duplicate of a good module docstring.** If the language has a docstring convention the repo uses,
  and it already carries Role + Entry points, the sidecar adds only Depends on / Gotchas / Keep in
  sync — or isn't needed. Detect this before writing (SKILL.md step 2, "header banners").

## Reconcile checklist

Walk each row against the current file. A "no" is a drift finding for the report.

| Section | Check |
|---|---|
| **Role** | Still one job, and still *this* job? Has the file quietly absorbed a second responsibility since the doc was written? |
| **Entry points** | Every listed export still exists, with the same signature / arity / sync-vs-async? Every *new* exported symbol listed? Removed exports struck from the doc? |
| **Depends on — outward** | Every listed import still present and still load-bearing? New imports of other first-party modules / services / tables / env vars added? Dead ones removed? |
| **Depends on — inward** | The named callers still call it? New callers appeared (grep)? A caller the doc said would break has since been decoupled? |
| **Gotchas** | Each one still true? (A constraint that a later fix removed is the most common stale entry.) Any new footgun introduced by recent changes? |
| **Keep in sync** | The counterpart file still exists at that path, and the coupling still real? |

If every row passes, the verdict is "doc is current" — say so and write nothing.
