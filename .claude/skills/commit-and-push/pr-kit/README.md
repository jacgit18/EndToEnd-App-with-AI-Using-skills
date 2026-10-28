# PR kit: a pull request description that always passes its checks

Copied from iron-log (where it runs; iron-log is the source, refresh these files from it when it changes), except `prBody.test.js`: iron-log's copy tests its own audience rules, the kit's is generic (inline audiences) so it passes in a fresh project. Add new test cases to both; never copy iron-log's file over the kit's. Install it in any project that opens PRs with one command:

```bash
.claude/skills/commit-and-push/pr-kit/install.sh <project-dir>   # keeps files that exist; --force replaces
```

It copies the files below, appends the rule to the project's CLAUDE.md, and prints what to adapt. By hand, the same mapping:

| Copy | To |
|---|---|
| `pull_request_template.md` | `.github/pull_request_template.md` |
| `pr-audience.yml` | `.github/workflows/pr-audience.yml` (the check: exactly one Audience box ticked) |
| `pr-changelog.yml` | `.github/workflows/pr-changelog.yml` (the check: a real entry under `## Changelog`; for a project whose CHANGELOG.md is outside the repo) |
| `pr-kit.json` | `.github/pr-kit.json` (the per-project settings) |
| `pr-body.mjs` | `scripts/pr-body.mjs` (fills the template and ticks the Audience box from the diff) |
| `prBody.test.js` | `scripts/prBody.test.js` (vitest; drop it if the project has no test runner) |
| `dependency-scan.yml` | `.github/workflows/dependency-scan.yml` (npm audit for production dependencies, GitHub dependency review, and `dep-vet` on packages a PR adds; rule `dependency-security.md`) |
| `dependabot.yml` | `.github/dependabot.yml` (weekly grouped updates; add an ecosystem block per manifest) |
| `dep-vet.mjs`, `depVet.test.js` | `scripts/dep-vet.mjs` and its test (registry facts and typosquat flags for new npm packages; `node scripts/dep-vet.mjs <name>` by hand before approving one) |
| `ci-timeouts.yml`, `ci-timeouts.mjs`, `ciTimeouts.test.js` | `.github/workflows/ci-timeouts.yml`, `scripts/ci-timeouts.mjs` and its test (fails a GitHub Actions job with no `timeout-minutes`, or one over 10 without `# timeout-ok: why`; rule `ci-budget.md`; also wire `node scripts/ci-timeouts.mjs` into the project's local check) |
| `claude-review.yml`, `review-model.mjs`, `reviewModel.test.js` | `.github/workflows/claude-review.yml`, `scripts/review-model.mjs` and its test (the automatic PR review; `review-model.mjs` picks Opus for risky paths or a big diff and Sonnet otherwise, never Haiku; needs the `CLAUDE_CODE_OAUTH_TOKEN` repository secret (subscription, from `claude setup-token`); settings under `review` in `.github/pr-kit.json`; rule `pr-review-bot.md`) |

Then add the rule to the project's CLAUDE.md: "open every PR with `node scripts/pr-body.mjs --what "..." > body.md` and `gh pr create --body-file body.md`; never write the description by hand."

Adapt per project (the script and both CI checks are identical everywhere and are never edited):
- `.github/pr-kit.json` (installed with `audiences: []`): extra audiences such as admin only or paid, each `{ key, label, files?, diffFile?, diffPattern?, reason }` (a changed file, or a line added to `diffFile`). Optional keys `notUserFacing`, `ui`, `autoTickWhenNoUi` override the defaults at the top of `pr-body.mjs`. iron-log's file is the worked example.
- `.github/pull_request_template.md`: one Audience box per audience label (the test fails if one is missing) and the project's own "Checks" lines. Only the Audience section is machine-checked.

The check fails with "no heading" or "found N" when a description was written by hand, which is the failure this kit removes: the author (human or agent) never has to remember who sees the change.

Prerequisites outside the repo (`dependency-security.md`, "Prerequisites outside the repo"): turn on the dependency graph, Dependabot alerts and the required checks in the repository settings, and confirm each check skips bot PRs by PR author. `install.sh` runs the kit's tests after copying when the project has vitest; after the first PR, read `gh pr checks`.
