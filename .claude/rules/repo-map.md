# Repo map

> **README drift:** `README.md` "Layout" references top-level directories — `Architecture/`,
> `Finance/`, `Goals/`, `Business Venture/`, `Communication/` — that are **not in this repo**.
> They belong to the surrounding PersonalBrain vault and were the source notes the skills
> were distilled from. Do not expect to find them here; do not try to "restore" them.

**This checkout is a working subset.** Tracked here: `.claude/`, `Artifact/`, `finance-dashboard/`,
`scripts/`, `.mcp.json`, and a few root files (`README.md` stub, two LinkedIn drafts). Rows below
marked *(absent here)* describe the fuller repo — `Books/`, `curriculum/`, `.superpowers/`,
`template/`, `SKILL-BACKLOG.md`, the README catalog table, and the `Finance` / `Health` / `Research`
skill groups are **not in this checkout**. Do not try to restore them; skills and commands that
depend on them (`catalog-drift-audit` Steps 1–2, `/new-skill` bookkeeping) skip that step and say so.

| Path | What's in it |
|---|---|
| `.claude/skills/<Group>/<name>/` | The skill library. Groups: `AI Engineering`, `Architecture` (+ `Architecture/Data`), `Business`, `Documents`, `Finance`, `Git`, `Health`, `Prompts`, `Research`, `Skill Development`, `Testing`. *(Finance, Health and Research are absent here.)* |
| `.claude/rules/` | This guidance, split into topic files and imported by `CLAUDE.md`. Edit the rule files, not the `CLAUDE.md` list. |
| `.claude/commands/` | Slash commands. `/new-skill <Group>/<name>` drives the add-a-skill workflow end to end; `/sync-catalog` is a read-only catalog consistency check. (Directory is `commands`, plural — Claude Code ignores a singular `command/`.) |
| `.claude/agents/` | **Not present in this checkout.** `spec-executor.md` (the one auto-discovered subagent) and the `decision-making-prioritization/` scaffolding are described in `agents.md` but are not tracked here; `spec-drift-gate` has an inline fallback. |
| `.claude/settings.json` | Wires two hooks: `UserPromptSubmit` → prompt logging, `SessionStart` → mechanical catalog-drift glance. |
| `.claude/_Prompts/logs/YYYY-MM-DD.md` | Auto-appended log of every submitted prompt. **Gitignored** — local only, never committed. |
| `.claude/_Prompts/catalog-audit-log.md` | Durable trail of `catalog-drift-audit` runs; each run reads it first to avoid re-flagging resolved items. |
| `README.md` | Human-facing catalog index with one table row per skill. Kept in sync by hand. *(Here it is a stub with no per-skill table.)* |
| `SKILL-BACKLOG.md` *(absent here)* | Skill candidates; each entry is marked `[x] Built …` with its isolation + interaction-test result recorded inline. |
| `template/skill-template/` *(absent here)* | Scaffold for a new skill — `SKILL.md` + `reference-file.md` + `README.md` skeletons. Copy to `.claude/skills/<Group>/<name>/`. |
| `template/spec-system/agent-spec-template.md` *(absent here)* | Template + worthiness test for authoring a new agent. |
| `scripts/` | `hooks/log-prompt.sh`, `hooks/catalog-drift-check.sh`; `git/state.sh` (snapshot), `git/commit.sh` (staged-pathspec commit + trailer), `git/push.sh` (timeout/fallback/retry), `git/land.sh` (merge a PR via `gh` + resync local), `git/batch-git-push.sh` (bulk). See `commands.md` / `conventions.md`. |
| `Artifact/` | Talking points / catalog write-ups for external posts. |
| `curriculum/`, `.superpowers/sdd/` *(absent here)* | A separate spec-driven learning-portfolio project (specs, plans, task briefs/reports). Unrelated to the skill catalog. |
