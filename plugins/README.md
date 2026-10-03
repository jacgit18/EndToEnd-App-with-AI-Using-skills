# plugins/

Packaged subsets of the skill catalog for use in other projects. Each plugin's `skills/`
entries are relative symlinks to the canonical `.claude/skills/<name>/` directories, so a
plugin never drifts from the catalog — edit the skill in `.claude/skills/`, not here.

## architecture-skills

30 skills: the Architecture, Architecture (Data) and AI Engineering groups (see
`.claude/skills/INDEX.md`), minus `tech-decision-walkthrough`, plus `technical-cost-decision`. They hand off to each other constantly, so they ship as one
plugin. Skills load namespaced: `architecture-skills:index-tuning`. Hand-offs outside the
plugin (the `testing-skills` plugin below, `tech-decision-walkthrough`, `spec-drift-gate`, …) fall back to
an inline one-line answer when not installed; each skill's Portability section says how.

Install for every project (a "skills-dir" plugin, auto-loads next session):

```bash
ln -s "$PWD/plugins/architecture-skills" ~/.claude/skills/architecture-skills
```

Upgrading from the earlier `data-skills` pilot: `rm ~/.claude/skills/data-skills` first (it
was a symlink to the directory this plugin replaced).

Try it for one session without installing: `claude --plugin-dir plugins/architecture-skills`.

This repo's `.claude/settings.json` disables `architecture-skills@skills-dir`, so the plugin
copies don't appear next to the project copies here.

## testing-skills

9 skills from the Testing group: `test-strategy`, `coverage-policy`, `test-case-discovery`,
`test-practice-gate`, `database-test-tooling`, `browser-test-tooling`,
`debugging-layer-selection`, `diagnostic-injection`, `web-vitals-audit`. `bug-hunt-drill` and
`repo-reality-audit` stay project-only. A separate plugin so it can be installed only where
tests are written; hand-offs into `architecture-skills` (`failure-mode-analysis`,
`deployment-strategy`, `data-access-layer`, …) fall back inline when that plugin is absent.

```bash
ln -s "$PWD/plugins/testing-skills" ~/.claude/skills/testing-skills
```

Try it without installing: `claude --plugin-dir plugins/testing-skills`. This repo's
`.claude/settings.json` disables `testing-skills@skills-dir` for the same reason as above.

## planning-skills

2 skills from the Business group: `user-story-decomposition` (feature or epic → stories or a
use case, acceptance criteria, Definition of Ready) and `ticket-evaluation` (a written ticket →
proceed / defer / needs more info / reconsider). They hand off to each other, so they ship
together. The rest of Business is split by job: `technical-cost-decision` ships in
`architecture-skills`, the writing trio is in the personal core below, and
`system-design-communication` stays project-only. Hand-offs to `design-scoping` and the
Architecture decision skills fall back inline when `architecture-skills` is absent.

```bash
ln -s "$PWD/plugins/planning-skills" ~/.claude/skills/planning-skills
```

Try it without installing: `claude --plugin-dir plugins/planning-skills`. This repo's
`.claude/settings.json` disables `planning-skills@skills-dir` for the same reason as above.

## Personal core (not a plugin)

Skills about how you work rather than about a project load as plain user skills via symlinks:
the four request-shape gates, the writing trio (`explaining-my-work`, `delete-ai-words`,
`software-carpentier-brand`), the two Documents skills (`codebase-file-orientation`,
`document-page-check`), three Prompts skills (`prompt-authoring`, `prompt-tester`,
`idea-to-first-test`), `incremental-build-pacing`, the git pair (`commit-and-push`,
`history-integration-strategy`) and seven slash-only skills (`disable-model-invocation: true`, so
they never auto-fire; type `/name` to use one): `tech-decision-walkthrough`,
`system-design-communication`, `bug-hunt-drill`, `decision-journal`, `problem-journal`,
`repo-reality-audit`, `context-promotion`. The two journals write under a configurable root
(`$JOURNAL_DIR`, else `Journal root:` in `~/.claude/CLAUDE.md`, else `.claude/_Prompts/`).
Already installed ones are skipped:

```bash
for s in ambiguity-gate learning-gate problem-solving-gates entry-point-first \
         explaining-my-work delete-ai-words software-carpentier-brand \
         codebase-file-orientation document-page-check \
         prompt-authoring prompt-tester idea-to-first-test incremental-build-pacing \
         commit-and-push history-integration-strategy \
         tech-decision-walkthrough system-design-communication bug-hunt-drill \
         decision-journal problem-journal repo-reality-audit context-promotion; do
  [ -e ~/.claude/skills/$s ] || ln -s "$PWD/.claude/skills/$s" ~/.claude/skills/$s
done
```

Verified 2026-10-03 (Claude Code 2.1.282): symlinked skill and plugin-skill directories are
followed; plugin skills are namespaced; a missing sibling triggers the inline fallback.
