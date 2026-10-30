# Lean CLAUDE.md template for a new project (see `new-project-order.md`)

Copy the block below into the new project's `CLAUDE.md`, fill the brackets, keep it under about 40 lines. Add a section only when a trigger in `new-project-order.md` fires; do not paste the Iron Log guardrails in on day 1.

```markdown
# [Project name]

[One line: what it is and who it is for.] Stack: [language, framework, database, host].

## Commands
- Dev: `[command]`   Typecheck: `[command]`   Unit tests: `[command]`   Deploy: `[command]`

## Data rules (load-bearing; do not change without asking)
- Units: [canonical unit and display rule]
- Dates and weeks: [local date strings, week start]
- IDs and deletes: [client ids, tombstones or hard delete]
- Ownership: [who owns a row, how it is enforced]
- Sync: [none / last-writer-wins / versioned rows]

## Conventions
- All new code in [TypeScript strict]. Logic is a pure function with a unit test; components only wire it.
- Migrations are plain SQL files in `[folder]`; never edit one that has run.
- No package is added without the owner's yes in chat.

## Definition of done
- Typecheck and unit tests pass; the change was seen in a browser at phone and desktop width.
- Report each check as verified, read-only, agent-reported or not run.

## Docs
- Decisions: `DECISIONS.md`. Plan: `ROADMAP.md`. Project docs: `/home/jac/Videos/DevHiveMind/Projects/[project]/`.

## Guardrails added so far
- (none yet; each line names the trigger that added it and its date)
```
