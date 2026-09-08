# commit-and-push skill

Stage → commit → push, with the commit message built from the actual diff instead of the
filenames or a vague "update". Reads `git status` / `git diff` / recent `git log` first,
matches the repo's message convention, splits unrelated changes into separate commits, runs a
pre-commit sanity pass (secrets, `.env`, large blobs, debug code, merge markers), branches off
the default branch when the user hasn't said to commit straight to it, and confirms before
anything outward-facing.

## Files

| File | Role |
|---|---|
| `SKILL.md` | The whole process — read state, branch guard, group, sanity pass, message rules, commit, push, report. |

## Boundaries

Stops after `git push`. Does **not** open PRs, resolve merge conflicts, rewrite published
history (`rebase` / `amend` / `--force`), or design a branching strategy.

- **vs `history-integration-strategy`** — this skill turns a working tree into commits and
  pushes them; it does not choose *how* a branch's history folds into another (merge commit
  vs. squash vs. rebase vs. fast-forward, or merge-in vs. rebase-onto for syncing). That
  decision is `history-integration-strategy`, which produces no commits itself. "Commit
  this" → here; "squash or rebase before merging?" → there.

## Related

- `scripts/git/state.sh` / `commit.sh` / `push.sh` / `batch-git-push.sh` — this repo's
  convenience wrappers for the steps. The skill prefers them when present and shows the
  plain-git equivalent for each, so it works with or without them.
- Commit trailer (`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`) comes from the
  session's attribution guidance; the skill enforces whatever the active trailer is on every
  message it writes.

## Portability

Repo-agnostic — the process is plain git. Copy the directory into another repo's
`.claude/skills/`; nothing here hard-depends on this repo's paths. Two soft references to
tidy for a new home:

- The `scripts/git/*` wrappers named in the steps are optional — copy them across too, or
  ignore them and use the plain-git commands shown beside each step.
- The `Co-Authored-By` trailer is this project's. If you carry `commit.sh` across it
  self-initialises `git config commit-helper.trailer` on first run (adopting the repo's own
  `Co-Authored-By` history, else the default) — override any time with
  `git config commit-helper.trailer "…"`, or `""` for none. Working by hand instead, just
  use the trailer the new repo wants in Step 5.
