# CI budget: agents do not grow the pipeline unasked (applies to every project)

An AI agent treats "more tests, longer timeouts, one more job" as free safety. It is not: every PR pays for it in runner minutes and in waiting, and agents open PRs constantly. A suite that took 5 minutes quietly becomes 30 (reported by a developer on the same pattern, 2026-10; the numbers are an anecdote, the mechanism is real). Nothing stops it unless the limits are written down and a check enforces them.

## The rules

1. **Every job has a timeout.** Each job in `.github/workflows/*.yml` sets `timeout-minutes`: about 2x its normal runtime, 10 minutes or less unless a comment on that line says why (`# timeout-ok: why`). A job without one runs for GitHub's 6-hour default when it hangs. A job that calls a reusable workflow (`uses:`) is exempt; the called workflow's jobs carry theirs.
2. **Each project records a budget** in its `CLAUDE.md` and `CI-BUDGET.md` (project docs folder): PR wall-clock target (time to green), total runner minutes per PR, the slowest allowed job, and the baseline measured on a date. Measure from real runs (`gh run list`, `gh run view --json jobs`), three runs, and report the spread (`test-run-protocol.md`).
3. **Unit first.** Logic is tested by a unit test. An e2e or integration test is added only when the PR body names what it catches that a unit test cannot (wiring, layout, a real browser, a real database). A new feature gets one spec, not one per state.
4. **No silent growth.** An agent never raises a timeout, adds a job, a matrix leg, a browser or a shard, or widens a `paths:` filter without saying so in the PR body with the minutes before and after. A change that adds more than 10% to the PR wall-clock or total minutes needs the owner's yes in chat.
5. **Trim, deduplicate, remove: proposed, never silent.** Cut timeouts that are far above the runtime; keep one test per flow; delete a test that has never failed and covers what a cheaper test already covers. The agent lists candidates with evidence (run history, what else covers it); the owner approves each deletion. Tests that guard a critical path named in the project's `CLAUDE.md` are never candidates.
6. **Cheap runs first, cancel the stale.** Lint, typecheck and unit tests run before e2e; PR workflows use `concurrency` with `cancel-in-progress: true`; docs-only changes skip heavy jobs; caches are keyed on the lockfile.
7. **Review it on a schedule.** At each milestone (or monthly) the audit reports the slowest jobs and specs, jobs near their timeout, and flaky retries (retries hide cost). `/audit-codebase` has the check.

## Enforcers

- `scripts/ci-timeouts.mjs` (PR kit, run by `.github/workflows/ci-timeouts.yml` and the project's `npm run lint` or check): fails a job without `timeout-minutes` and a value over 10 without `# timeout-ok:`. Exits 1; the false-positive cases (reusable-workflow jobs, comments, quoted values) are in its test.
- PR template line `CI minutes: before/after, or n/a`; `definition-of-done.md` baseline line.
- Rules 2 to 7 are advisory until one is missed twice (`rule-enforcers.md`).

## Where it lives

- Per project: `CI-BUDGET.md` beside `ARCHITECTURE.md` in `/home/jac/Videos/DevHiveMind/Projects/<project>/`; created when onboarding; listed in `PriorityRead.md`.
- Related: `test-run-protocol.md` (reading a slow or failing run), `definition-of-done.md`, `feature-delivery.md` (fewer PRs means fewer pipeline runs), `dependency-security.md` (the scan workflows also have timeouts), skills `test-strategy` and `coverage-policy`.
