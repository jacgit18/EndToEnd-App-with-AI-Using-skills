# plugins/

Packaged subsets of the skill catalog for use in other projects. Each plugin's `skills/`
entries are relative symlinks to the canonical `.claude/skills/<name>/` directories, so a
plugin never drifts from the catalog — edit the skill in `.claude/skills/`, not here.

## architecture-skills

28 skills: the Architecture and Architecture (Data) groups (see `.claude/skills/INDEX.md`),
minus `tech-decision-walkthrough`, plus `technical-cost-decision`. They hand off to each other constantly, so they ship as one
plugin. Skills load namespaced: `architecture-skills:index-tuning`. Hand-offs outside the
plugin (the `testing-skills` plugin below, `tech-decision-walkthrough`, `model-routing-decision`, …) fall back to
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

## Personal core (not a plugin)

The four request-shape gates load as plain user skills via symlinks:

```bash
for s in ambiguity-gate learning-gate problem-solving-gates entry-point-first; do
  ln -s "$PWD/.claude/skills/$s" ~/.claude/skills/$s
done
```

Verified 2026-10-03 (Claude Code 2.1.282): symlinked skill and plugin-skill directories are
followed; plugin skills are namespaced; a missing sibling triggers the inline fallback.
