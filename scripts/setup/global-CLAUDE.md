# Global preferences

Journal root: @DEVHIVEMIND_ROOT@/AI Generated Content
(Used by the `decision-journal` and `problem-journal` skills: `decisions-log.md`, `problems-log.md`, `errors/`. Quote the path — it contains spaces.)

Project docs root: @DEVHIVEMIND_ROOT@/<project-name>/docs/
(Every project's docs — ADRs, specs, backlog, write-ups — are written and edited here, not inside the project folder. When a new project folder is added or copied, create its `<project-name>/docs/` here (copy existing docs in, or leave empty if it has none). The project's own `docs/` copy, if any, is frozen. `EndToEnd-App-with-AI-Using-skills` holds `finance-dashboard/docs/` and `Artifact/`. Quote the path.)

Slash-only skills (never auto-fire; you cannot invoke them): when one fits, suggest the user type `/name` instead of calling it — tech-decision-walkthrough, system-design-communication, bug-hunt-drill, decision-journal, problem-journal, repo-reality-audit, context-promotion.
