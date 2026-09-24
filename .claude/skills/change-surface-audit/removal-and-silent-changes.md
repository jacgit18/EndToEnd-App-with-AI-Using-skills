# Removal Dependencies, the Expand-Contract Sequence, and Silent Changes

Reference for `SKILL.md` steps 3, 4, and 5.

---

## The expand-contract sequence (for a breaking Modify)

A breaking change to a contract, a schema, or the meaning of a state value is safe only if
it moves through distinct steps — skipping one is what turns "we changed a field" into an
incident.

1. **Expand** — add the new shape alongside the old (a new nullable column, a new
   optional field, a new enum value accepted-but-not-yet-emitted). Nothing that reads the
   old shape breaks yet.
2. **Dual-write / dual-support** — code writes both shapes (or handles both), so the
   system can run with a mix of old and new consumers during a rolling deploy.
3. **Backfill** — bring existing data/state up to the new shape. Name what a read looks
   like if it lands *mid-backfill* — that's a real state the system will be in, not an
   edge case to wave away.
4. **Switch reads** — consumers move to reading/emitting the new shape. This is the step
   that actually changes observed behavior; everything before it was inert.
5. **Contract** — remove the old shape (the old column, the old field, the old enum
   branch). This is also the first fully irreversible step in most cases — name it as the
   **point of no return** in the audit's output.

Skipping straight from step 1 to step 5 — "change the schema, deploy the code" — is the
unsafe process. The safe process is boring on purpose: each step is independently
reversible except the last.

Worked example — adding a NOT NULL column:
- Unsafe: alter table to add the column NOT NULL, deploy code that writes it. Existing
  rows either fail the migration outright or every pre-deploy insert path breaks until the
  new code ships everywhere.
- Safe: (1) add the column nullable; (2) deploy code that writes it going forward, alongside
  the old behavior if anything still needs it; (3) backfill existing rows; (4) switch any
  reads that need the guarantee to assume it's populated; (5) add the NOT NULL constraint
  (and this is the point of no return — reverting means dropping the constraint again, not
  simply rolling back code).

---

## Hidden removal dependencies

Removal is deceptively hard because systems accumulate dependents nobody tracked. Audit
each category explicitly — "probably nobody uses this" is not an audit, it's a guess.

### 1. API consumers
Check access logs for real traffic over a stated window, not just the current sprint's
knowledge. Check API-key/partner registries. Check internal callers too — a cron, an
internal script, a dashboard's data source. **Process:** audit → if traffic exists,
deprecate (a response header, a log warning, a dated end-of-life) before removing → if
zero traffic over the stated window, record the audit (source + date + window) and the
removal can skip a live deprecation window but not the mechanical cleanup pass below.

### 2. Database dependencies
A column or table can be read by things outside the application entirely: background
jobs, analytics pipelines, ETL jobs, scheduled exports, a BI tool's saved query. These
don't show up in an application-code grep. Check the data warehouse's lineage/source list
and any scheduled export configuration, not just the app's own repo.

### 3. Feature flags
A flag guarding the removed path needs its own cleanup: delete the flag, remove the
branching logic on both sides (not just the disabled branch — the *other* branch becomes
the only code path and should be un-conditional), clean the flag from configuration/rollout
tooling. Otherwise the codebase accumulates flag debt — flags nobody remembers the purpose
of, still evaluated on every request.

### 4. Cached data
Stale cache entries, orphaned Redis keys under the old key pattern, and CDN-cached
responses for the removed route can outlive the removal by their TTL, serving a "the
feature still works" experience to some users after it's gone. Purge or let expire
deliberately, don't assume TTL alone handles it silently and correctly.

### 5. UI dead paths
Navigation routes, deep links, and browser-stored state (bookmarks, saved URLs, a
service-worker cache of the old route) can point at something that no longer exists.
Decide what a stale link should do — redirect, a clear "this was removed" page, or a
silent 404 — rather than letting it be whatever the framework defaults to.

---

## Silent changes — the category most likely to skip this audit entirely

Dependency upgrades, configuration changes, and infrastructure updates rarely get treated
as "a feature change," which is exactly why they cause a large share of production
incidents — nobody ran a blast-radius check because nobody thought there was a feature to
check. Walk the same six surfaces from `surface-checklist.md` against these:

### Dependency upgrades
- Does the changelog show a **default behavior change** — timeout, retry count, TLS/cert
  validation strictness, a serialization format, a logging verbosity default?
- Is this a **major version** with documented breaking changes, or a minor/patch that
  *claims* to be safe (semver is a promise, not a guarantee — read the actual diff for
  anything security- or timing-sensitive)?
- Does the upgrade pull in **transitive dependency changes** you didn't ask for and haven't
  read the changelog of?
- Does anything in your code rely on the old library's specific error types, exception
  hierarchy, or exact error messages (a common integration-surface break)?

### Configuration changes
- Does a changed default value affect behavior for every deployment that doesn't
  explicitly override it, or only the one environment being changed right now?
- Is the change environment-scoped correctly, or does a shared config value silently
  affect an environment nobody meant to touch?
- Does this configuration value's own storage/rotation/sensitivity need a pass through
  `config-and-secrets-management` rather than being edited ad hoc?

### Infrastructure updates
- Does a platform/runtime upgrade (container base image, language runtime, managed
  service version) change timing, memory limits, or default network behavior (a new
  default timeout, a changed connection-pool default) that nothing in application code
  changed to cause?
- Does the update change what's reachable — a security-group/firewall default, a new
  private-by-default setting on a managed resource?
- Is there a rollback path for the infra change itself, distinct from rolling back
  application code?

Treat a silent change's changelog/diff as the "component" and what it touches downstream as
the "interaction" — the same six-surface walk applies, it's just aimed at someone else's
release notes instead of your own diff.

---

## Deprecation record format

For a Remove that carries a live deprecation window, write
`docs/engineering/deprecations/<slug>.md`:

```
Removing:            <the concrete endpoint/column/flag/route>
Consumer audit:       <source(s) checked, date, window, findings>
Deprecation window:   <start date> → <end date>
Notice mechanism:     <response header / log warning / changelog entry / direct outreach>
Point of no return:   <the specific irreversible step — route deleted, column dropped, cache purged>
Status:               <open — N consumers remaining | ready to remove | removed on <date>>
```

Update `Status` as consumers migrate off; this is a living document until the removal
actually happens, then it's a record of what was checked.
