---
description: Read-only catalog consistency check — README rows, unreferenced skills, backlog markers, possible dead pointers. Changes nothing.
---

Read-only health check on the skill catalog. **Change nothing.** To apply fixes, that is the
`catalog-drift-audit` skill (heavier, periodic, writes `.claude/_Prompts/catalog-audit-log.md`).
This is the quick pre-commit glance — see @.claude/rules/adding-a-skill.md step 5 for what
each skill is supposed to have.

Skills on disk with no `README.md` row:
!`for s in $(find .claude/skills -name SKILL.md | sed 's#.claude/skills/##;s#/SKILL.md##'); do b=$(basename "$s"); grep -qF "$b" README.md || echo "  MISSING: $s"; done; echo "  --- end ---"`

Skills referenced by no other skill's `SKILL.md` (starvation candidates):
!`for s in $(find .claude/skills -name SKILL.md | sed 's#.*/\([^/]*\)/SKILL.md#\1#'); do n=$(grep -rlF "$s" .claude/skills --include=SKILL.md 2>/dev/null | grep -v "/$s/SKILL.md" | wc -l); [ "$n" -eq 0 ] && echo "  UNREFERENCED: $s"; done; echo "  --- end ---"`

`SKILL-BACKLOG.md` markers that usually mean unfinished bookkeeping (line-terminal, so prose that merely quotes the marker is skipped):
!`grep -nE 'Memory:[[:space:]]*(pending|TODO)[[:space:]]*\.?$|^[[:space:]]*-?[[:space:]]*\[ \] Built' SKILL-BACKLOG.md || echo "  (none)"`

Backticked hyphenated tokens in SKILL.md files that are not a skill directory (candidate dead pointers):
!`bt=$(printf '\140'); grep -rhoE "${bt}[a-z][a-z0-9]+(-[a-z0-9]+)+${bt}" .claude/skills --include=SKILL.md 2>/dev/null | tr -d "$bt" | sort -u | while read t; do find .claude/skills -type d -name "$t" | grep -q . || echo "  $t"; done; echo "  --- end ---"`

Known-legit non-directory refs — ignore these in the list above: `claude-api`, `code-review`,
`security-review`, `writing-skills` (Claude Code built-in / plugin skills), `spec-executor`
(an agent, `.claude/agents/spec-executor.md`). Anything else that is a real skill name and not
a directory is a genuine dead pointer.

From the output above, write a short report:

1. **Missing README rows** — list them; one-line add per skill (right group table, or a new
   `### Group` section).
2. **Unreferenced skills** — for each, say whether it plausibly shares a collision surface with
   a sibling (→ real starvation, wants a reciprocal `description` pointer) or is a standalone
   tool with no overlap (→ fine, note it and move on).
3. **Backlog markers** — cross-check against the memory directory / reality where you can.
4. **Candidate dead pointers** — filter to things that are actually skill names (ignore
   domain terms), then confirm which are genuinely dead vs. renamed.

End with **CLEAN** or a short punch-list. Do not edit any file — hand fixes to
`catalog-drift-audit` or `/new-skill`.
