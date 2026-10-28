# CLAUDE.md

Two things live in this repo:

1. **A skill catalog** (`.claude/skills/`, `plugins/`, `scripts/`) — gated Claude Code skills.
2. **`finance-dashboard/`** — a personal finance app: FastAPI + Postgres backend, React/Vite/TypeScript frontend, deployed via Docker Compose + Caddy.

Standing rules are in `.claude/rules/` and load automatically — read them, don't duplicate them here:
`.claude/rules/INDEX.md` lists every rule file with what it decides and what enforces it. Start there; read `repo-map.md`, `conventions.md`, `commands.md` and `definition-of-done.md` first.

## Hard rules (details in `conventions.md`)

- **Docs are not in this repo.** finance-dashboard's docs are `/home/jac/Videos/DevHiveMind/Projects/EndToEnd-App-with-AI-Using-skills/finance-dashboard/` and the write-ups are `…/Artifact/` (no `docs/` subfolder). The repo copies were deleted 2026-10-13. Quote paths (spaces).
- **Git:** branch per change, PRs to `main`, never push to `main`. Stage explicit pathspecs only (never `git add -A` / `.`). Use `scripts/git/commit.sh`, `push.sh`, `land.sh`.
- **PR descriptions:** never hand-written. `node scripts/pr-body.mjs --what "..." > body.md`, then `gh pr create --body-file body.md`; it ticks the Audience box from the diff (enforcers: `.github/workflows/pr-audience.yml`, `pr-changelog.yml`). Kit: `.claude/skills/commit-and-push/pr-kit/`.
- **CI budget:** every GitHub Actions job has `timeout-minutes` (about 2x its worst run, 10 or less unless `# timeout-ok: why`); a change to workflows or e2e specs reports CI minutes before and after in the PR; tests are never deleted or merged unasked. Rule `.claude/rules/ci-budget.md`; enforcer `scripts/ci-timeouts.mjs` run by `.github/workflows/ci-timeouts.yml`.
- **Prod deploys** need a fresh, explicit "deploy to prod" in the current session.
- **Never commit** `*.csv` (personal financial exports) or `.claude/_Prompts/logs/`.
- Free-first: prefer free tiers; document anything that could cost money in `ops/paid-options.md` (vault docs root).
- Never post anything externally (e.g. LinkedIn drafts) — save as files only.

## finance-dashboard

```bash
# Backend (from finance-dashboard/backend)
PYTHONPATH=. uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest -q

# Frontend (from finance-dashboard/frontend)
npm run dev        # dev server
npm run build      # tsc --noEmit + vite build
npm test           # vitest
npm run e2e        # playwright (+ axe)
```

- **Read first (vault, `/home/jac/Videos/DevHiveMind/Projects/EndToEnd-App-with-AI-Using-skills/finance-dashboard/`):** `PriorityRead.md` ranks everything. Guardrails: `ROADMAP.md` (build only what it and the backlog list), `ARCHITECTURE.md`, `DECISIONS.md` (do not re-litigate), `CHANGELOG.md` (add an entry with each change).
- **UI work:** read all five in `ux/` first: `UX-DESIGN-BRIEF.md`, `USERFLOW.md`, `DESIGN-SYSTEM.md`, `COMPONENTS.md`, `SCREEN-SPECS.md`. They were written from the code (2026-10-13); the code wins if they differ. Update them with each UI change.
- **Database work** (schema, migration, access rules, fixtures): read all five in `data/` first: `DATA-MODEL.md`, `SCHEMA.md`, `MIGRATIONS.md`, `RLS-POLICIES.md`, `SEED-DATA.md`. Written from the code (2026-10-13); the code wins if they differ. Update them in the same PR.
- Postgres runs in Docker (`finance-dashboard-db`); full stack via `compose.yaml`. See `finance-dashboard/README.md`.
- CI is `.github/workflows/ci.yml`.
- Dependency scan = npm audit + dependency review + dep-vet + pip-audit; enforcer `.github/workflows/dependency-scan.yml`. No package is added without the owner's yes in chat (`dependency-security.md`); put `Dependency approval: <name>` in the PR.
- Web UI targets WCAG 2.2 AAA and Lighthouse 100; measure the **production build**, not the dev server (`web-accessibility-and-lighthouse.md`).
- A Lighthouse/axe score is regression evidence, not a conformance claim.

## Skills

- Skills are flat: `.claude/skills/<name>/SKILL.md`. Descriptions carry the sibling carve-outs; keep them ≤ ~430 chars. No `$<digit>` in SKILL.md.
- Lint: `scripts/skills/lint.sh --strict`. Script smoke tests: `scripts/tests/run.sh`.
- New skill: `/new-skill <name> [Group]`. Catalog check: `/sync-catalog`.
- Slash-only skills (suggest `/name`, never invoke): tech-decision-walkthrough, system-design-communication, bug-hunt-drill, decision-journal, problem-journal, repo-reality-audit, context-promotion.
- PR review: `.github/workflows/claude-review.yml` reviews each PR when it is opened or marked ready and picks the model from the diff with `scripts/review-model.mjs` (Opus for risky paths: the finance backend, hooks and settings, workflows, dependency files, or over 600 lines / 25 files; Sonnet otherwise; never Haiku; labels `review:deep` / `review:standard` override). The kit copy is in `.claude/skills/commit-and-push/pr-kit/`; the repository secret is `CLAUDE_CODE_OAUTH_TOKEN` (subscription, from `claude setup-token`). Never a required check. Rule: `.claude/rules/pr-review-bot.md`.
