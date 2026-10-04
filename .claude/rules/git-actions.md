# Git actions: which model, and when to stop

Global copy lives in `~/.claude/CLAUDE.md`; this file is the version-controlled copy. Keep them in sync.

## Routine git work — a small model (Haiku) is enough

- staging and committing
- writing a commit message from a diff
- branching and pushing
- opening PRs
- checking status and logs

## Judgment-heavy git work — needs Sonnet or Opus

- resolving merge conflicts
- rebasing or rewriting history
- deciding what to squash or split
- recovering from a bad state (detached HEAD, a force-push mistake)
- reviewing a diff for real problems

## How to apply

- A rule cannot switch the model mid-session. If the session is on a small model and the task is in the
  second list, **say so before starting** ("this needs a stronger model — switch with `/model`, or tell
  me to proceed") and wait. Don't attempt it silently.
- The risk with a smaller model is the destructive commands: `reset --hard`, force-push, deleting
  branches. A wrong call there is costly, so confirm first on any model.
- Report outcomes exactly: a PR that is open but not merged is "open, not merged", not "done".
- In this repo the simple branch → PR → merge flow is routine; use `scripts/git/*` (`conventions.md`).
