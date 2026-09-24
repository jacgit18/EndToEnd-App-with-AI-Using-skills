# context-promotion

A procedure with one confirmation stop: find context the user keeps re-typing, decide where it should live (rules file / `CLAUDE.md`, a spec, or memory), write it once after approval, and hand back the short `@reference`.

## Files

| File | Read it when |
|---|---|
| `SKILL.md` | Always — the five steps, the write gate and the Never list |
| `destinations.md` | Picking or formatting the destination; this repo's specifics (no `CLAUDE.md`, rules auto-loaded) |

## Where it sits

- **`session-handoff`** — resume context for unfinished work; ephemeral. This skill is for what stays true across sessions.
- **`spec-drift-gate`** — drafts a spec for a new build. This skill adds to a spec that exists, and hands over when none does.
- **`decision-journal`** — a judgment call with a prediction; **`prompt-archive`** — the prompt text itself. Neither promotes context into rules.
- **`learning-gate`** — not layered on top: this is an execution procedure with its own confirmation stop.
- Built-ins: `init` generates a `CLAUDE.md` from the codebase; `update-config` owns settings, hooks and permissions.

## Using it in another repo

Copy the `context-promotion/` directory into the other repo's `.claude/skills/` and adjust the paths in `destinations.md`.
