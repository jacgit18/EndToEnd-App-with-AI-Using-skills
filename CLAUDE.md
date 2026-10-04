# CLAUDE.md

Two things live in this repo:

1. **A skill catalog** (`.claude/skills/`, `plugins/`, `scripts/`) — gated Claude Code skills.
2. **`finance-dashboard/`** — a personal finance app: FastAPI + Postgres backend, React/Vite/TypeScript frontend, deployed via Docker Compose + Caddy.

Standing rules are in `.claude/rules/` and load automatically — read them, don't duplicate them here:
`repo-map.md` (what's tracked vs. absent in this working subset), `conventions.md` (branches, commits, staging, docs location, prod deploys), `commands.md` (git scripts, lint, tests), `skill-architecture.md`, `adding-a-skill.md`, `agents.md`, `web-accessibility-and-lighthouse.md`.

## Hard rules (details in `conventions.md`)

- **Docs are not edited here.** `finance-dashboard/docs/` and `Artifact/` are frozen copies; edit them only under `/home/jac/Videos/DevHiveMind/EndToEnd-App-with-AI-Using-skills/`. Quote paths (spaces).
- **Git:** branch per change, PRs to `main`, never push to `main`. Stage explicit pathspecs only (never `git add -A` / `.`). Use `scripts/git/commit.sh`, `push.sh`, `land.sh`.
- **Prod deploys** need a fresh, explicit "deploy to prod" in the current session.
- **Never commit** `*.csv` (personal financial exports) or `.claude/_Prompts/logs/`.
- Free-first: prefer free tiers; document anything that could cost money in `docs/paid-options.md`.
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

- Postgres runs in Docker (`finance-dashboard-db`); full stack via `compose.yaml`. See `finance-dashboard/README.md`.
- CI is `.github/workflows/ci.yml`.
- Web UI targets WCAG 2.2 AAA and Lighthouse 100; measure the **production build**, not the dev server (`web-accessibility-and-lighthouse.md`).
- A Lighthouse/axe score is regression evidence, not a conformance claim.

## Skills

- Skills are flat: `.claude/skills/<name>/SKILL.md`. Descriptions carry the sibling carve-outs; keep them ≤ ~430 chars. No `$<digit>` in SKILL.md.
- Lint: `scripts/skills/lint.sh --strict`. Script smoke tests: `scripts/tests/run.sh`.
- New skill: `/new-skill <name> [Group]`. Catalog check: `/sync-catalog`.
- Slash-only skills (suggest `/name`, never invoke): tech-decision-walkthrough, system-design-communication, bug-hunt-drill, decision-journal, problem-journal, repo-reality-audit, context-promotion.
