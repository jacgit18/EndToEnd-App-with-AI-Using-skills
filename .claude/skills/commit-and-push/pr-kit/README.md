# PR kit: a pull request description that always passes its checks

Copied from iron-log (where it runs). Install it in any project that opens PRs:

| Copy | To |
|---|---|
| `pull_request_template.md` | `.github/pull_request_template.md` |
| `pr-audience.yml` | `.github/workflows/pr-audience.yml` (the check: exactly one Audience box ticked) |
| `pr-changelog.yml` | `.github/workflows/pr-changelog.yml` (the check: a real entry under `## Changelog`; for a project whose CHANGELOG.md is outside the repo) |
| `pr-body.mjs` | `scripts/pr-body.mjs` (fills the template and ticks the Audience box from the diff) |
| `prBody.test.js` | `scripts/prBody.test.js` (vitest; drop it if the project has no test runner) |

Then add the rule to the project's CLAUDE.md: "open every PR with `node scripts/pr-body.mjs --what "..." > body.md` and `gh pr create --body-file body.md`; never write the description by hand."

Adapt per project (all in `pr-body.mjs` and the template):
- `NOT_USER_FACING`: the path patterns that can never change what a user sees (docs, tests, scripts, CI, config). Anything else counts as user-facing.
- The admin detection (an added `key: 'admin'` line in `src/features.ts`, `server/admin.ts`) is iron-log's feature-flag convention. Change it to the project's own, or delete the branch so only n/a and everyone are inferred.
- Audience labels in the template (`n/a`, `**Admin only**`, `**Everyone**`) must keep the strings in `LABELS`.
- Add the project's own "Checks" lines to the template. Only the Audience section is machine-checked.

The check fails with "no heading" or "found N" when a description was written by hand, which is the failure this kit removes: the author (human or agent) never has to remember who sees the change.
