---
description: Continue from the most recent session handoff in this project. Reads the newest .claude/handoffs/handoff-*.md, checks the repo against it, restates the next steps, then carries on.
argument-hint: [handoff-file-or-keyword]
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Skill
---

# /last-handoff

Pick up where the last session stopped. Handoffs are written by the `session-handoff` skill into
`.claude/handoffs/` of the project. `$ARGUMENTS` is optional: a path to a handoff file, or a keyword
matched against handoff filenames (`/last-handoff pr239`).

## 1. Find the handoff

Newest handoffs in this project (by modified time):
!`d="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/.claude/handoffs"; ls -t "$d"/handoff-*.md 2>/dev/null | head -5 || true; echo "  --- dir: $d ---"`

- No argument: handoffs pile up and several can belong to different tasks the same day. If the newest two or three name different branches or goals, read only each file's title and Goal line, show them, and ask which to resume before reading further or editing anything (one session opened the wrong handoff and began editing the wrong feature). If only one plausible handoff exists, take it.
- `$ARGUMENTS` is an existing file: use it.
- `$ARGUMENTS` is a keyword: take the newest file whose name contains it.
- Nothing listed, or no match: say so in one line and stop. Do not guess a handoff from another
  project, and do not write one (that is `session-handoff`).

Read the whole file. Tell the user which file you picked (name and date) in one line.

## 2. Check it against reality

A handoff is a snapshot, not ground truth. Before acting on it:

- `git status -sb`, `git log --oneline -5`, and `git diff --stat`: is the branch the one it names, and is the
  working tree what it says? A step marked "not started" may already be in the tree.
- If it names a PR, run `gh pr view <n> --json state,mergedAt,headRefName` (open is not merged). If it names
  other open work, `gh pr list` for the same area.
- If a file or path it names no longer exists, say so rather than assuming it moved.

Anything that disagrees with the handoff: list the differences, trust the repo, and ask only if the
difference changes what to do next.

## 3. Restate, then continue

Reply with:

1. **Goal** in one sentence.
2. **What the repo shows now** (branch, PR state, uncommitted changes), noting any drift from the handoff.
3. **Next steps**, in the handoff's order (for a planning handoff: its Relevant Files & Proposed Changes, in order), with the first one marked as the one you are starting. Re-check any item the handoff labels `read-only` or `agent-reported` before building on it (`evidence-labels.md`).

Then start on step 1 of Next Steps. Do not wait for a "go" unless the next step is hard to reverse or
outward-facing (push, merge, deploy, delete, post): those follow the project's own rules (CLAUDE.md)
and need the user's go-ahead as usual. Keep the handoff's "Decisions & Constraints" as binding; do not
re-litigate them.

If the handoff is a planning handoff (sections Problem, Expected Behavior & Acceptance Criteria, Relevant Files &
Proposed Changes, Required Tests, Unresolved Questions), treat the acceptance criteria and required tests as the
definition of done, re-run the reproduction steps first to confirm the problem still shows, and ask the user about
any Unresolved Question before the step it blocks.

If the handoff has an increment map (`- [x]` / `- [ ]` checklist from `incremental-build-pacing`), keep
using that format and tick items as you finish them.

Read-only until step 3: steps 1 and 2 change nothing.
