# Test-run protocol under load (applies to every project)

Machine load causes false failures (load 18 to 56 gave dozens of timeouts, a failed pre-push hook and a Lighthouse score of 61 with no baseline).

1. Before a full check, read the load (`uptime`). If it is above the core count, expect timeouts.
2. Run unit tests with fewer workers (`--maxWorkers=4`); a project records its own command in its `CLAUDE.md`.
3. A failing test is not a regression until it also fails alone and on `main` under the same conditions. Name the test and say how you compared.
4. Lighthouse and other timing scores: measure `main` first on the same machine; repeat 3 times; retry on an idle machine before blaming the change. Run `main` 3 times as well and report its spread; a change inside that spread is not a score win or loss, so cite requests or bytes instead.
5. Skip a hook (`SKIP_CHECK=1`, `--no-verify`) only after the full check passes cleanly, and only when the user has allowed skipping hooks.
6. Report what was `not run` (e2e, sync e2e, db checks) so it is not mistaken for passed.
7. Running only the tests a change can affect (`vitest related`, `jest --findRelatedTests`) follows imports, so it saves little for a widely imported file (iron-log: a shared validator still ran 79% of the tests) and cannot see files a test reads by path (shell scripts, templates) or a deleted module. Fall back to the full suite for tooling or dependency files, files read by path and deletions, always include the tests that guard the critical paths, and keep the full suite on main before a deploy. Measure the saving on a leaf file and on a widely imported one before promising it (`iron-log` ADR 072).
8. Before renaming a CI job or splitting it into a matrix, read the branch rules: a ruleset can require checks by name while `gh api repos/<r>/branches/<b>/protection` answers 404. Keep a gate job with the old name that `needs:` the matrix (`if: always()`); a job skipped by `if:` still passes a required check.
9. CI duration is a measurement like a Lighthouse score: compare a run against recent `main` runs of the same job (`gh run list --workflow <f> --json databaseId`, then `gh run view <id> --json jobs`), take three, and state the spread before saying a change made CI slower or faster. Compare per job, not only the total: matrix shards can hide an imbalance (iron-log 2026-10-26: shards 1 and 4 took 8 to 9 minutes, shards 2 and 3 about 3). A retry that passes hides cost, so count retries. Budget and timeouts: `ci-budget.md`.

Enforcer: advisory; the project's pre-push hook runs the check, this rule says how to read its failures.
