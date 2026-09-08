# Adding or changing a skill

1. Copy `template/skill-template/` to `.claude/skills/<Group>/<name>/` and fill in
   `SKILL.md` + reference files + `README.md`. Budget real effort on the `description`
   frontmatter — it alone decides when the skill fires and carries the carve-outs against
   siblings.
2. **Isolation screen** — confirm a baseline (no skill) fails the way the skill exists to
   fix, and that the skill fixes it.
3. **Interaction test** — run `Prompts/skill-interaction-testing` against the sibling set.
   Record what you find: hand-off, absorption, chaining, or a fix for stacking /
   contradiction / silent override.
4. **Reciprocal edits** — apply the sibling `description` changes and cross-pointers the
   interaction test surfaced, both directions.
5. **Bookkeeping** — add/refresh the skill's row in `README.md`; mark the `SKILL-BACKLOG.md`
   entry `[x] Built` with the test result inline; leave the auto-memory marker
   (`memory/MEMORY.md` index line + a file).

For a whole-catalog pass rather than one skill, use `catalog-drift-audit` and append to
`.claude/_Prompts/catalog-audit-log.md`.
