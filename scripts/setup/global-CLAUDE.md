# Global preferences

Journal root: @DEVHIVEMIND_ROOT@/AI Generated Content
(Used by the `decision-journal` and `problem-journal` skills: `decisions-log.md`, `problems-log.md`, `errors/`. Quote the path — it contains spaces.)

Project docs root: @DEVHIVEMIND_ROOT@/Projects/<project-name>/
(Every project's docs — ADRs, specs, backlog, write-ups — are written and edited here, not inside the project folder. The project folder holds the docs directly; there is no `docs/` subfolder, since the vault path already says docs. When a new project folder is added or copied, create `<project-name>/` here (copy existing docs in, or leave empty if it has none). The project's own `docs/` copy in its repo, if any, is frozen. `EndToEnd-App-with-AI-Using-skills` holds `finance-dashboard/` (its docs) and `Artifact/`. Quote the path.)

Git actions — model choice (applies to every project):
- Routine git (stage, commit, message from a diff, branch, push, open PR, status/log) is fine on a small model (Haiku).
- Judgment-heavy git (merge conflicts, rebase/history rewrite, squash/split decisions, recovering from a bad state like detached HEAD or a force-push mistake, reviewing a diff for real problems) needs Sonnet or Opus. If the session is on a smaller model, say so before starting and wait — you can't switch models yourself.
- Destructive commands (`reset --hard`, force-push, deleting branches) are where a smaller model's wrong call is costly: confirm first on any model.
- Report PR/merge state exactly (open ≠ merged). Version-controlled copy: `.claude/rules/git-actions.md` in EndToEnd-App-with-AI-Using-skills.

Slash-only skills (never auto-fire; you cannot invoke them): when one fits, suggest the user type `/name` instead of calling it — tech-decision-walkthrough, system-design-communication, bug-hunt-drill, decision-journal, problem-journal, repo-reality-audit, context-promotion.

Design mind map (applies to every project): each project keeps an Obsidian design mind map at `@DEVHIVEMIND_ROOT@/Projects/<project>/architecture/<Project> Design Mind Map.canvas` (reference: iron-log's). Create it when onboarding a project; update the matching branch whenever an ADR, data model, runbook or audit changes. The `mind-map` skill has the method. Quote the path.

Agent guardrail docs (applies to every project): each project has `README.md` (in the repo) plus `ROADMAP.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `DECISIONS.md` in `@DEVHIVEMIND_ROOT@/Projects/<project>/`. Create any that are missing when onboarding a project, keep them short and linked to the detailed docs, and update CHANGELOG/DECISIONS/ROADMAP with each change. For any project with a UI also create `ux/` with `UX-DESIGN-BRIEF.md`, `USERFLOW.md`, `DESIGN-SYSTEM.md`, `COMPONENTS.md`, `SCREEN-SPECS.md`, filled from the real code, and list them in the project's CLAUDE.md. For any project with a database also create `data/` with `DATA-MODEL.md`, `SCHEMA.md`, `MIGRATIONS.md`, `RLS-POLICIES.md`, `SEED-DATA.md` (before the first migration on a new project; from the real code on an existing one), read them before schema, migration, access or fixture work, and update them in the same PR. The `priority-read` skill has the method and what each file holds. Quote the path.

Priority read (applies to every project): each project keeps `@DEVHIVEMIND_ROOT@/Projects/<project>/PriorityRead.md`, a short ranked list of which docs to read first, which to read when touching an area, and which generated bulk to skip. Create it when onboarding a project; update it whenever a doc is added, superseded or closed. The `priority-read` skill has the method. Quote the path.
