# plugins/

Packaged subsets of the skill catalog for use in other projects. Each plugin's `skills/`
entries are relative symlinks to the canonical `.claude/skills/<name>/` directories, so a
plugin never drifts from the catalog — edit the skill in `.claude/skills/`, not here.

## data-skills

The six Data-cluster gates (`database-architecture`, `relational-modeling`,
`dimensional-modeling`, `data-access-layer`, `index-tuning`, `data-tier-operations`) plus
the three load-bearing siblings they hand off to (`change-surface-audit`,
`technical-cost-decision`, `access-control-modeling`). Skills load namespaced:
`data-skills:index-tuning`. Other hand-offs (`caching-strategy`, `problem-solving-gates`, …)
fall back to an inline one-line answer when not installed — each skill's Portability
section says how.

Install for every project (a "skills-dir" plugin, auto-loads next session):

```bash
ln -s "$PWD/plugins/data-skills" ~/.claude/skills/data-skills
```

Try it for one session without installing: `claude --plugin-dir plugins/data-skills`.

This repo's `.claude/settings.json` disables `data-skills@skills-dir`, so the plugin copies
don't appear next to the project copies here.

## Personal core (not a plugin)

The four request-shape gates load as plain user skills via symlinks:

```bash
for s in ambiguity-gate learning-gate problem-solving-gates entry-point-first; do
  ln -s "$PWD/.claude/skills/$s" ~/.claude/skills/$s
done
```

Verified 2026-10-03 (Claude Code 2.1.282): symlinked skill and plugin-skill directories are
followed; plugin skills are namespaced; a missing sibling triggers the inline fallback.
