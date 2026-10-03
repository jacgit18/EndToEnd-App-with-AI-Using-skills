# Adding or changing a skill

1. Copy `template/skill-template/` to `.claude/skills/<name>/` (flat — Claude Code discovers one level only; record the group label in `.claude/skills/INDEX.md`) and fill in
   `SKILL.md` + reference files + `README.md`. Budget real effort on the `description`
   frontmatter — it alone decides when the skill fires and carries the carve-outs against
   siblings. (In a checkout without `template/`, copy a sibling skill of the same group as
   the scaffold instead — see `repo-map.md`.)
2. **Static audit** — run `skill-static-audit` on the draft (read-only,
   cheap) and fix the blockers and should-fixes before spending agent runs on the next two
   steps. It catches missing carve-outs, unreachable steps and one-way sibling pointers by
   reading; it does not replace steps 3–4, which run the skill.
3. **Isolation screen** — confirm a baseline (no skill) fails the way the skill exists to
   fix, and that the skill fixes it. When the skill's claim is about outcomes (estimates,
   verdicts, calls that later proved right or wrong), make the screen **outcome-grounded**:
   first check there are real cases with recorded outcomes (about 3 minimum; none = park the
   skill, don't test on invented ones); withhold the outcome from every arm; run a third arm
   that gets the skill's rules as a plain prompt (otherwise the skill arm passes rules the
   baseline was never told); score with a separate agent, and score range width, not just
   containment. Parked candidates live in `.claude/skills/CANDIDATES.md`.
4. **Interaction test** — run `skill-interaction-testing` against the sibling set.
   Record what you find: hand-off, absorption, chaining, or a fix for stacking /
   contradiction / silent override.
5. **Reciprocal edits** — apply the sibling `description` changes and cross-pointers the
   interaction test surfaced, both directions.
6. **Portability + packaging** — add a `## Portability` section just above `## Routing
   boundaries (full)`, in the shape every packaged skill uses (copy one, e.g. `test-strategy`):
   what setup it needs and what it writes; `Depends on:` the siblings it hands off to (leave out
   catalog tooling; list a core gate only when its hand-off carries weight); the standard
   missing-sibling sentence; then 2–3 load-bearing fallbacks, each checked against the skill
   body (overreaches get caught this way). No `cp -r` block. Then ask the user where it ships —
   an existing plugin (relative symlink in `plugins/<plugin>/skills/`, bump its `plugin.json`
   version), the personal-core loop in `plugins/README.md`, or project-only — and say which in
   the skill's `README.md` if it has one. Update the counts in `plugins/README.md` and
   `repo-map.md`. Claude can't write `~/.claude/skills/`, so a new personal-core skill needs the
   user to run its `ln -s`; say so.
7. **Bookkeeping** — add/refresh the skill's row in `README.md`; mark the `SKILL-BACKLOG.md`
   entry `[x] Built` with the test result inline; leave the auto-memory marker
   (`memory/MEMORY.md` index line + a file). Where `README.md` has no catalog table or
   `SKILL-BACKLOG.md` is absent (this working subset), skip those two and say so.

For a whole-catalog pass rather than one skill, use `catalog-drift-audit` and append to
`.claude/_Prompts/catalog-audit-log.md`.
