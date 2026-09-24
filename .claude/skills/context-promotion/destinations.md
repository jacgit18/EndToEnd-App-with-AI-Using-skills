# Destinations for promoted context

Read from `SKILL.md` Step 3, when you need to pick or format a destination.

## Decision table

| The statement is… | Goes to | Why |
|---|---|---|
| A standing instruction for every session on this project (conventions, commands, "always/never", architecture facts) | `.claude/rules/<topic>.md` — or one line in `CLAUDE.md` if it is tiny | Loaded automatically every session; the user stops pasting it |
| A requirement or constraint scoped to one feature or build (scope, out-of-scope, acceptance, limits) | That feature's spec file | Scoped context should not load for unrelated work; a spec is what `spec-drift-gate` diffs against |
| About the person or how they like to work, or a fact about their situation that is not in the repo | Auto-memory (`user` / `feedback` / `project` / `reference`) | Follows the user across projects and sessions |
| Derivable from the code, `git log`, or the file tree | Nowhere | It would go stale; read it live instead |
| Current task state, or "this time do X" | Nowhere (task state → `session-handoff`) | Not stable |

If a statement fits two rows, prefer the narrower scope: spec over rules, rules over `CLAUDE.md`. If you cannot tell which scope it has, ask.

## This repo's specifics

- `.claude/rules/*.md` files are loaded into every session on their own. This checkout has **no `CLAUDE.md`**, so a new rules file needs no import line. If a project does have a `CLAUDE.md` that lists rule imports, add the new file there with the user's confirmation.
- Run `ls .claude/rules/` and extend the closest topic file before creating a new one.
- Specs: look for the feature's spec first (`docs/`, or where `spec-drift-gate` wrote it). If none exists and the feature is a multi-file build, hand to `spec-drift-gate`.
- Memory: `~/.claude/projects/<project>/memory/`, one file per fact plus a one-line pointer in `MEMORY.md`.

## Entry formats

**Rules file / CLAUDE.md** — one entry, about four lines:

```markdown
- **<Rule in the user's words.>** <Why it exists, if the user said.> Applies when: <the situation>.
```

**Spec** — put it under the section it belongs to (Constraints, Out of scope, Acceptance); one line, with the user's wording.

**Memory** — copy the shape of an existing entry in `MEMORY.md`'s directory (frontmatter `name`, `description`, `metadata.type`; body with a **Why:** and **How to apply:** line for feedback and project types), then a one-line index entry.

## Already written down? (Step 2 check)

Search before proposing: `.claude/rules/`, any `CLAUDE.md`, the spec, and the memory index (`MEMORY.md`) for the key nouns of the statement. A partial match means extend or tighten the existing entry, not add a second one.

## Refusing to promote

Say "not promoting this" and why for: secrets or credentials; another person's private details; anything only true for today; anything the user has not actually stated.
