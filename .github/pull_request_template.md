## What and why


## Audience (user-facing changes)

<!-- Tick exactly one. `node scripts/pr-body.mjs --what "..."` writes this whole description with the right box ticked. -->

- [ ] n/a: no user-facing change
- [ ] **Admin only**: finance-dashboard UI or API only an admin sees
- [ ] **Everyone**: a finance-dashboard change any user sees

## Changelog

<!-- One or two sentences for CHANGELOG.md in the project docs vault (the "PR changelog" check needs real text here; write "n/a: <why>" for a change that needs none). `node scripts/pr-body.mjs --changelog "..."` fills it. -->

## Checks

- [ ] `scripts/skills/lint.sh --strict` (skills, rules or commands changed; n/a otherwise)
- [ ] `scripts/tests/run.sh` (scripts or hooks changed; n/a otherwise)
- [ ] finance-dashboard: backend `uv run pytest -q`; frontend `npm run build && npm test`
- [ ] UI, style, font, image or bundle change: `node scripts/lighthouse.mjs --check` run, before and after in the description (n/a otherwise)
