---
name: priority-read
description: Writes and maintains `_PriorityRead.md` in a project's docs folder, a ranked reading list saying which of the project's many generated docs matter most and which to skip. Use for "what should I read first in this project", "create the priority read", "too many docs", and on onboarding any project. Not `mind-map` (visual design map), `codebase-file-orientation` (one file's sidecar), or `session-handoff` (one session's state).
---

# Priority read

Produces `/home/jac/Videos/DevHiveMind/Projects/<project>/docs/_PriorityRead.md`: the answer to "I have 100 docs; which do I actually read?" The leading underscore keeps it at the top of the folder.

## Create

1. List every file under `<project>/docs/` (count them; note generated bulk such as audit runs, candidate JSON, agent artifacts, screenshots).
2. Read the top of each candidate doc (title, status, date, "supersedes" lines). Never rank from filenames alone. Check which docs are cited by others (`grep -l` for wikilinks): heavily linked = central.
3. Sort into tiers, each doc with a one-line *why* and, where useful, a rough read time:
   - **Read first (≤5 docs):** the doc that states what is true now (spec / feature map / backlog), the deploy or run guide, the data model.
   - **Read when you touch X:** grouped by area (decisions, a feature, deploy, security, testing). Say the trigger.
   - **Reference / history:** superseded specs, phase briefs, closed plans, ADRs you only need on challenge.
   - **Generated bulk, skip unless auditing:** name the folder, not each file; point to its summary file (e.g. `REPORT.md`).
4. Add a "Where truth lives" line: which doc wins when two disagree, and which copy of the docs is frozen.
5. Link with `[[Projects/<project>/docs/...|alias]]` (vault root `/home/jac/Videos/DevHiveMind`). Verify every link resolves.
6. Add the design map (`architecture/<Project> Design Mind Map.canvas`) as a read-first pointer when it exists.

## Onboarding: the five agent-guardrail docs

On onboarding a new project, also make sure these five exist (create any that are missing; never overwrite). `README.md` lives in the project repo (its public front door); the other four live in `/home/jac/Videos/DevHiveMind/Projects/<project>/docs/`. Keep them short and link to the detailed docs instead of copying them.

1. `README.md`: what the app does, stack, install/run, main features, folder layout.
2. `ROADMAP.md`: priorities, milestones, and an explicit **Out of scope** list; tell agents to build only what is listed. Point to the backlog; do not duplicate it.
3. `ARCHITECTURE.md`: system shape, where code lives (path table), data flow, key dependencies, links to ADRs and data model.
4. `CHANGELOG.md`: newest first, dated, built from `git log --first-parent`; add an entry in the same PR as each change.
5. `DECISIONS.md`: index of ADRs (one row each: decision, choice, link) with the rule "do not re-litigate; new decision means new ADR plus a row here".

Add all five to the read-first or read-when tiers. Reference example: iron-log.

### UX set (any project with a user interface)

Also create these five in `<project>/docs/ux/` when missing, filled from the real code (stylesheet tokens, component files, routes/tabs), not invented. Read all five before changing UI; update them with each UI change.

1. `UX-DESIGN-BRIEF.md`: who it is for, the problem, what the user must accomplish, principles, not in scope.
2. `USERFLOW.md`: step-by-step journeys (first run, main loop, errors, settings/data, offline).
3. `DESIGN-SYSTEM.md`: colour tokens (light and dark), type, spacing, radius, interaction rules (tap targets, focus, motion). Say that the stylesheet wins if they differ.
4. `COMPONENTS.md`: reusable pieces (buttons, forms, cards, sheets, notices) with their states: default, hover, focus, disabled, error, loading, empty.
5. `SCREEN-SPECS.md`: per screen: layout, main action, mobile layout, loading and empty states.

Link them from the README or CLAUDE.md "Read first" block and from `_PriorityRead.md`.

## Maintain

After any bulk move or rename of docs, re-check every link in `_PriorityRead.md` (links by bare name survive a folder move, path-qualified ones do not); retarget, recreate or drop each broken one, and say which. When a doc is added, renamed, superseded or closed, update the tiers in the same piece of work and bump the `Last reviewed` date. When a PR changes behaviour, a decision or the plan, update `CHANGELOG.md`, `DECISIONS.md` or `ROADMAP.md` in the same piece of work. Keep it to one screen; if it grows, you are listing, not prioritizing.

## Rules

- Never invent a doc's importance: if it was not read, say it was ranked from its title only.
- Keep the whole file short (target under ~60 lines).
- Report: path as a link, the read-first list, and anything ranked unread.
