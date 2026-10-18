# Test-run protocol under load (applies to every project)

Machine load causes false failures (load 18 to 56 gave dozens of timeouts, a failed pre-push hook and a Lighthouse score of 61 with no baseline).

1. Before a full check, read the load (`uptime`). If it is above the core count, expect timeouts.
2. Run unit tests with fewer workers (`--maxWorkers=4`); a project records its own command in its `CLAUDE.md`.
3. A failing test is not a regression until it also fails alone and on `main` under the same conditions. Name the test and say how you compared.
4. Lighthouse and other timing scores: measure `main` first on the same machine; repeat 3 times; retry on an idle machine before blaming the change. Run `main` 3 times as well and report its spread; a change inside that spread is not a score win or loss, so cite requests or bytes instead.
5. Skip a hook (`SKIP_CHECK=1`, `--no-verify`) only after the full check passes cleanly, and only when the user has allowed skipping hooks.
6. Report what was `not run` (e2e, sync e2e, db checks) so it is not mistaken for passed.

Enforcer: advisory; the project's pre-push hook runs the check, this rule says how to read its failures.
