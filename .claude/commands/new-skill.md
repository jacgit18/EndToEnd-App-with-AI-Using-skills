---
description: Build a new skill end-to-end per .claude/rules/adding-a-skill.md — scaffold, isolation screen, interaction test, reciprocal edits, bookkeeping, commit.
argument-hint: "<Group>/<name>  (e.g. Prompts/foo, Architecture/Data/bar)"
---

Build a new skill at `.claude/skills/$ARGUMENTS/`.

Follow @.claude/rules/adding-a-skill.md as the canonical checklist and
@.claude/rules/skill-architecture.md for the shape. Do every step; don't report it done until
each has actually happened. Work on a branch `skill/<name>`; commit at the end per
@.claude/rules/conventions.md — explicit pathspecs (never `git add -A`), `git diff --cached`
first, the `Co-Authored-By` footer.

Execution notes for running this well:

- **Placement.** Confirm `<Group>` exists under `.claude/skills/`. Match the group's file
  convention: single-file `SKILL.md` for Business / Finance / Health / AI Engineering / most
  Prompts skills; `SKILL.md` + companion `*.md` + `README.md` (copy `template/skill-template/`)
  for Architecture and Testing. A brand-new group also needs its own `### Group` section in
  `README.md`. Ask if unsure.
- **`description` frontmatter first, and slowly.** It alone decides when the skill fires and
  carries every carve-out against siblings — literal trigger phrases plus explicit
  "NOT for X — that's `sibling`". A weak description is the usual reason a skill misfires or
  never fires.
- **Isolation screen (step 2).** One realistic prompt, baseline vs. skill, ideally a
  worktree-isolated agent. Record PASS / MIXED / FAIL with the reasoning — record MIXED/FAIL
  honestly, don't inflate a weak result.
- **Interaction test (step 3).** Invoke the `skill-interaction-testing` skill; scope the pool
  per its Step 1 (own group + the four cross-cutting gates + any outsider sharing a concrete
  concept). Run scenarios via a worktree agent. Fixes are one-line description edits.
- **Reciprocal edits (step 4).** Apply sibling pointer edits **both directions** — a
  one-directional pointer is the single most common finding.
- **Bookkeeping (step 5).** `README.md` row; `SKILL-BACKLOG.md` `[x] Built <date>` with the
  isolation + interaction results inline; `memory/skill-added-<name>.md` + its `MEMORY.md`
  index line.
- **Then** open a PR to `main` if the user wants one — this command does not push to `main`
  directly.
