## What and why


## Audience (user-facing changes)

<!-- Tick exactly one. `node scripts/pr-body.mjs --what "..."` writes this whole description with the right box ticked. -->

- [ ] n/a: no user-facing change
- [ ] **Admin only**: finance-dashboard UI or API only an admin sees
- [ ] **Everyone**: a finance-dashboard change any user sees

## Changelog

<!-- One or two sentences for CHANGELOG.md in the project docs vault (the "PR changelog" check needs real text here; write "n/a: <why>" for a change that needs none). `node scripts/pr-body.mjs --changelog "..."` fills it. -->

## Delivery

<!-- One feature, one brief, one PR (feature-delivery.md). `node scripts/pr-body.mjs --brief "<path>" --split "<reason>"` fills these. A split needs one of: migration first, file overlap with an open PR (name it), over about 600 lines or 25 files, pure-move refactor first, device or owner-only part. -->

Brief: none given (pass --brief)
Split because: n/a: this PR is the whole feature

## Done

<!-- Paste the card's "Done when" list (definition-of-done.md). Mark each line with its evidence label: verified, read-only, agent-reported or not run (say why). A line that is not verified means this is ready for review with a gap, not done. -->

- [ ] Every "Done when" line is listed above with its evidence label
- [ ] The project's Definition of done (its CLAUDE.md) walked through; gaps named here

## Checks

- [ ] `scripts/skills/lint.sh --strict` (skills, rules or commands changed; n/a otherwise)
- [ ] `scripts/tests/run.sh` (scripts or hooks changed; n/a otherwise)
- [ ] finance-dashboard: backend `uv run pytest -q`; frontend `npm run build && npm test`
- [ ] CI minutes: n/a (no workflow or test-suite change), or PR wall-clock and runner minutes before and after, with any new job, leg, spec or timeout named and what a new e2e spec catches that a unit test cannot (`ci-budget.md`)
- [ ] UI, style, font, image or bundle change: `node scripts/lighthouse.mjs --check` run, before and after in the description (n/a otherwise)
