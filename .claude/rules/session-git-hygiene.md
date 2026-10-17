# Session git hygiene (applies to every project)

Several sessions, worktrees and branches run at once. Keep them from colliding.

- One worktree (or one checkout) per session, with its own database container and port. Two sessions on one scratch database block each other.
- Before every commit run `git branch --show-current` and `git status`. A commit on the wrong branch or staged files you did not write are the common accidents.
- Never touch uncommitted changes you did not make; if they are in the way, say so and stop.
- If plain `git` fails with "must be run in a work tree", `core.bare` is wrong; use `git --git-dir=.git --work-tree=. -c core.bare=false <cmd>` and report it, do not edit the config.
- Deleting branches, worktrees or tags, `reset --hard` and force-push need the user's confirmation, on any model. Check "unmerged" branches against squash-merges first, skip worktrees with dirty files, and keep a note of what was removed.
- A stray commit is fixed with a new, user-approved step, never silently.
- When resuming from a handoff, confirm it is the right one (branch and goal) before editing.

Enforcer: `permissions.ask` entries for `reset --hard`, force-push and branch deletion (`git-actions.md`); the rest is advisory.
