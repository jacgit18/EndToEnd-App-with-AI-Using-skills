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

## Slash-only skills

Skills with `disable-model-invocation: true` (the seven in the user's global CLAUDE.md) are invisible to routing: Claude cannot invoke them and never sees their descriptions. When a request matches one, or a sibling's "NOT for X" carve-out names one, suggest the user type `/name`; do not recreate its workflow. A gate that waits on one must say what to do when the user does not run it.

What each is for (match on the request, not the name): `/bug-hunt-drill` quiz or practice debugging; `/decision-journal` log a judgment call; `/problem-journal` log a fixed bug or error; `/context-promotion` context the user keeps retyping; `/repo-reality-audit` docs or ADRs versus the real repo, or a build that won't run; `/tech-decision-walkthrough` walk through a build's tech choices; `/system-design-communication` mock system-design interview.

## Cross-cutting meta-skills

These four are referenced by many others and are the usual integration points for a new skill:

- `learning-gate` — classifies intent (learning / execution / reference),
  sets how much thinking Claude may do. New skills add a Step 3 row here.
- `problem-solving-gates` — prior-effort gates (Rubber Duck / Options
  Generator / Knowledge Checker / Optimization).
- `spec-drift-gate` — spec-before-build + drift checkpoints.
- `ambiguity-gate` — ask before acting on a request with more than one reading.
