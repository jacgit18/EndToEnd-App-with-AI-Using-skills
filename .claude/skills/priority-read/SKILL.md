---
name: priority-read
description: Writes and maintains `_PriorityRead.md` in a project's docs folder, a ranked reading list saying which of the project's many generated docs matter most and which to skip. Use for "what should I read first in this project", "create the priority read", "too many docs", and on onboarding any project. Not `mind-map` (visual design map), `codebase-file-orientation` (one file's sidecar), or `session-handoff` (one session's state).
---

# Priority read

Produces `/home/jac/Videos/DevHiveMind/<project>/docs/_PriorityRead.md`: the answer to "I have 100 docs; which do I actually read?" The leading underscore keeps it at the top of the folder.

## Create

1. List every file under `<project>/docs/` (count them; note generated bulk such as audit runs, candidate JSON, agent artifacts, screenshots).
2. Read the top of each candidate doc (title, status, date, "supersedes" lines). Never rank from filenames alone. Check which docs are cited by others (`grep -l` for wikilinks): heavily linked = central.
3. Sort into tiers, each doc with a one-line *why* and, where useful, a rough read time:
   - **Read first (≤5 docs):** the doc that states what is true now (spec / feature map / backlog), the deploy or run guide, the data model.
   - **Read when you touch X:** grouped by area (decisions, a feature, deploy, security, testing). Say the trigger.
   - **Reference / history:** superseded specs, phase briefs, closed plans, ADRs you only need on challenge.
   - **Generated bulk, skip unless auditing:** name the folder, not each file; point to its summary file (e.g. `REPORT.md`).
4. Add a "Where truth lives" line: which doc wins when two disagree, and which copy of the docs is frozen.
5. Link with `[[<project>/docs/...|alias]]` (vault root `/home/jac/Videos/DevHiveMind`). Verify every link resolves.
6. Add the design map (`architecture/<Project> Design Mind Map.canvas`) as a read-first pointer when it exists.

## Maintain

When a doc is added, renamed, superseded or closed, update the tiers in the same piece of work and bump the `Last reviewed` date. Keep it to one screen; if it grows, you are listing, not prioritizing.

## Rules

- Never invent a doc's importance: if it was not read, say it was ranked from its title only.
- Keep the whole file short (target under ~60 lines).
- Report: path as a link, the read-first list, and anything ranked unread.
