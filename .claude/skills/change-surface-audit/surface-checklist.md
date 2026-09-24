# The Six Change Surfaces

Reference for `SKILL.md` step 2. For an Add or a Modify, walk all six against the concrete
change from step 1. For a Remove or a Silent change, walk the same six against the thing
being removed or changed — see `removal-and-silent-changes.md` for what to add on top.

Record `n/a — <reason>` when a surface genuinely isn't touched, so a skipped surface is a
decision on the record, not an omission.

---

## 1. API surface

**Does this change what a caller sends or gets back, or add/remove a way to call in?**

Probe:
- Is a new endpoint/route/RPC/topic introduced?
- Is an existing one extended (new optional field, new query param) or changed (a field's
  type, meaning, or presence)?
- Does the response shape change in a way a strict parser would reject (removed field,
  retyped field, a list that can now be empty/null when it couldn't before)?
- Is the change backward compatible for every *known* client version, including ones that
  can't be forced to upgrade (mobile apps pinned to a store release, a partner integration)?

Example risk: *a field's type changes from int to string in a minor release — every client
that parses it strictly either crashes or silently mis-parses.*

Checklist before shipping an API change:
- Is the response/request schema changing, and does every field addition have a sensible
  default for old clients that don't send/expect it?
- Are old client versions still compatible, and is there a way to know if any are still
  out there (version header, user-agent, a usage dashboard)?

## 2. Data surface

**Does this change what's stored, how it's shaped, or how it's read?**

Probe:
- New table, column, index, or relationship? Renamed or retyped existing one?
- Does the migration lock a table other writers depend on, and for how long?
- Does an index change help this query at the cost of every other writer's insert path?
- Does existing data need a backfill, and is a partial backfill (crash mid-way) a state the
  system can be in without corrupting reads?
- Does this change what a downstream consumer (ETL, analytics, an export job) reads,
  without that consumer being in this audit's inventory at all?

Example risk: *a new NOT NULL column with no default locks the table for the migration's
duration, or breaks every existing insert path that doesn't set it.*

Checklist:
- Is the schema change backward compatible with code that hasn't deployed yet (rolling
  deploy running old and new code against the same schema simultaneously)?
- Does the data need backfilling, and what happens to a read that lands mid-backfill?

## 3. State surface (client / in-memory / cache)

**Does this change what a piece of state means, or how much of it there is?**

Probe:
- Does a client-side derived value or cache need re-normalization?
- Does an existing "exhaustive" switch/enum match now have a case missing (the single most
  common silent-failure shape in a Modify)?
- Does a new field/component trigger re-renders, re-fetches, or cache invalidation across
  more of the app than intended?
- Is server state and UI state being conflated in a way that makes the new value's source
  of truth ambiguous?

Example risk: *`status` grows from a 2-value to a 4-value enum — every place that matched
exhaustively (`if active then X else Y`) now silently treats the 2 new values as the wrong
branch instead of erroring.*

## 4. Performance surface

**Does this change add load, latency, memory, or network calls that weren't there before?**

Probe:
- New DB queries per request — and do they run in a loop (N+1)?
- New network calls per page/request, and what's their timeout/retry behavior?
- Payload size increase — response bodies, cache entries, message sizes?
- Memory or CPU cost that only shows up at production scale, not in dev/staging data
  volumes?

Example risk: *a feature modification adds one more query per item in a list render — fine
in dev with 5 items, an N+1 storm in prod with 5,000.*

Checklist — estimate before shipping:
- New requests per page/action, new DB queries per request, payload size delta.

## 5. Security surface

**Does this change expose new data, change who can do what, or open an injection surface?**

Probe:
- Does the change expose data that wasn't previously reachable (a new field, a new
  endpoint, a more permissive filter)?
- Does authorization logic change — does this need a pass through
  `access-control-modeling`'s vocabulary (role/attribute grant, resource ownership,
  tenancy) rather than an ad hoc check?
- Does a new endpoint or parameter allow enumeration (sequential IDs, a search that leaks
  existence) it didn't before?
- Is user input reaching a query, template, or shell in a new place without the existing
  validation path?

Example risk: *a new "export my data" feature reuses an internal query builder that
doesn't scope by tenant — now any authenticated user can export any tenant's data by
adjusting a parameter.*

## 6. Observability surface

**Will you find out this broke, or will a customer tell you first?**

Probe:
- Does the new/changed path emit logs and metrics at the same standard as the rest of the
  system, or does it ship silent?
- Is there an existing alert or dashboard that implicitly assumed the old shape (a status
  filter, a field it groups by) that now silently undercounts or miscounts?
- Are client errors on this path distinguishable from backend errors after the change?

Example risk: *a feature ships with no monitoring wired up at all — the first sign of
trouble is a support ticket, not an alert.*

---

## Which surfaces usually carry the most risk, by change type

| Change type | Heaviest surfaces |
|---|---|
| New endpoint | API, Security, Observability |
| Extended/changed endpoint | API, State (client-side parsing), Observability |
| New column/table | Data, Performance (migration lock) |
| Changed column meaning / enum growth | State, Data, Functional logic everywhere it's matched |
| New UI component/flow | State (re-renders), Performance, Security (new input surface) |
| Config/infra change | Operational, Performance, Security (see `removal-and-silent-changes.md`) |

Still record the others as `n/a — <reason>` so the walk is complete on paper.
