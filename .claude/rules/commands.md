# Commands

There is no build, lint, or test runner. The operational scripts live in `scripts/git/`:

```bash
# One-call repo snapshot (read-only) — replaces status + diff + diff --cached + log.
scripts/git/state.sh

# Commit: stage exactly these paths, sanity-check the staged set, append the
# Co-Authored-By trailer, commit. Never pushes, never `git add -A`.
scripts/git/commit.sh -m "Subject line" -m "Optional body para" -- path/one path/two

# Push with a timeout + HTTP/1.1 fallback + one retry, so a stalled push fails fast.
scripts/git/push.sh [remote=origin] [branch=current]

# Merge a PR via `gh` (branch protection + checks still enforced — not a direct push
# to main), then delete the remote branch and resync the local base. Default method
# is a merge commit; --squash / --rebase override. No arg = the current branch's PR.
scripts/git/land.sh [PR-number | branch] [--merge | --squash | --rebase]

# Chunked commit + push — bulk file adds, never more than N files in one push.
# Args: [batch_size=90] [branch=current] [commit_prefix="Add files"]
scripts/git/batch-git-push.sh 50 main "Add skills"
DRY_RUN=1 scripts/git/batch-git-push.sh            # preview only
INCLUDE_MODIFIED=1 scripts/git/batch-git-push.sh   # also stage modified/deleted, not just untracked
```

See `conventions.md` for the staging and prompt-log-rides-along rules these encode. The
`commit-and-push` skill drives the conversational version (message from the diff, branch
guard, confirm-before-push); these scripts are the mechanism it calls.

Two hooks run automatically (wired in `.claude/settings.json`), both defensive by design —
always exit 0, never block, only touch their own output:

- `scripts/hooks/log-prompt.sh` (`UserPromptSubmit`) — appends every prompt to the dated
  log. Needs `jq`; prints nothing.
- `scripts/hooks/catalog-drift-check.sh` (`SessionStart`) — runs the two unambiguous
  `/sync-catalog` checks (skills with no `README.md` row, open `SKILL-BACKLOG.md` markers)
  and injects a short summary only when one trips. Silent on a clean catalog and on
  resume/compact restarts. Fixes nothing — hand drift to `catalog-drift-audit` / `/new-skill`.

**"Testing" a skill is done by invoking a skill, not a shell command:**

- `Prompts/skill-interaction-testing` — run a new/changed skill against its siblings for
  stacking, contradiction, silent override, and beneficial chaining.
- `Prompts/catalog-drift-audit` — periodic whole-catalog hygiene pass.
- `Skill Development/spec-drift-gate` — gate a multi-file/multi-session build behind a
  written spec, then diff work against it at checkpoints.
