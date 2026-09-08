# Skill architecture

Every skill is a directory with a fixed shape:

- **`SKILL.md`** — YAML frontmatter (`name`, `description`) then the procedure. The
  `description` is large and does real work: it packs literal trigger phrases **and**
  explicit "this is NOT for X — that's `sibling-skill`" carve-outs. Disambiguation between
  overlapping skills lives in these descriptions, not in a router. When you change a
  skill's scope, you almost always must edit sibling descriptions reciprocally.
- **Companion `*.md`** — the deep reference material (methods, worked examples, rubrics),
  kept out of `SKILL.md` so the entry point stays short.
- **`README.md`** — where this skill sits relative to its siblings (hand-off, absorption,
  chaining boundaries).

Most skills are **gates**: they withhold the answer until a precondition is met — a stated
hypothesis, a listed set of unknowns, a settled prior decision, a learning rep the user
must do themselves. A few (`index-tuning`, `failure-mode-analysis`, `reliability-math`,
`change-surface-audit`, `document-page-check`, `disclosure-gap-audit`) are procedures, not gates.
The README's per-group tables say which is which.

## Cross-cutting meta-skills

These four are referenced by many others and are the usual integration points for a new skill:

- `Skill Development/learning-gate` — classifies intent (learning / execution / reference),
  sets how much thinking Claude may do. New skills add a Step 3 row here.
- `Skill Development/problem-solving-gates` — prior-effort gates (Rubber Duck / Options
  Generator / Knowledge Checker / Optimization).
- `Skill Development/spec-drift-gate` — spec-before-build + drift checkpoints.
- `Prompts/ambiguity-gate` — ask before acting on a request with more than one reading.
