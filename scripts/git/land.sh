#!/usr/bin/env bash
#
# land.sh — merge a pull request from the terminal, then resync locally.
#
# Saves the round-trip of opening the PR in a browser to click "Merge". It
# goes through GitHub (via `gh`), so branch protection, required checks, and
# the merge-commit style are all still honoured — a merge the web UI would
# refuse is refused here too. It is NOT a direct push to `main`.
#
#   scripts/git/land.sh [PR-number | branch] [--merge | --squash | --rebase]
#
#   scripts/git/land.sh                 # the PR for the current branch, merge commit
#   scripts/git/land.sh 17              # PR #17
#   scripts/git/land.sh 17 --squash     # squash-merge instead
#   scripts/git/land.sh my-feature      # the PR whose head is branch my-feature
#
# Default method is --merge (a merge commit), matching this repo's history;
# see the `history-integration-strategy` skill for when --squash/--rebase fit.
#
# After a successful merge it deletes the PR's remote branch, checks out the
# base branch, fast-forwards it to the just-merged state, prunes stale
# remote-tracking refs, and deletes the local head branch. Anything it can't
# do cleanly (dirty tree, base checkout fails) it skips with a note rather
# than forcing.
#
# Requires the `gh` CLI, authenticated (`gh auth status`).

set -uo pipefail

top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "land.sh: not a git repo" >&2; exit 1; }
cd "$top" || exit 1
command -v gh >/dev/null 2>&1 || { echo "land.sh: needs the gh CLI on PATH" >&2; exit 1; }

target=""
method="--merge"
for a in "$@"; do
  case "$a" in
    --merge | --squash | --rebase) method="$a" ;;
    -*) echo "land.sh: unknown flag: $a" >&2; exit 2 ;;
    *)
      [ -z "$target" ] || { echo "land.sh: give at most one PR/branch (got '$target' and '$a')" >&2; exit 2; }
      target="$a" ;;
  esac
done

# Default to the current branch's PR.
[ -n "$target" ] || target="$(git rev-parse --abbrev-ref HEAD)"
if [ "$target" = "HEAD" ]; then
  echo "land.sh: detached HEAD — pass a PR number or branch name." >&2
  exit 1
fi

# Resolve number + base + state in one call.
info="$(gh pr view "$target" --json number,baseRefName,state,headRefName \
  -q '[.number, .baseRefName, .state, .headRefName] | @tsv' 2>/dev/null)"
[ -n "$info" ] || { echo "land.sh: no PR found for '$target'." >&2; exit 1; }

IFS=$'\t' read -r prnum base state head <<EOF
$info
EOF

if [ "$state" != "OPEN" ]; then
  echo "land.sh: PR #$prnum is $state, not OPEN — nothing to do." >&2
  exit 1
fi

echo "land.sh: merging PR #$prnum (${head} → ${base}) with ${method} ..."
if ! gh pr merge "$prnum" "$method" --delete-branch; then
  echo >&2
  echo "land.sh: merge did not go through — checks pending, branch protection, or a conflict." >&2
  echo "land.sh: to have GitHub merge it automatically once checks pass:" >&2
  echo "         gh pr merge $prnum $method --auto --delete-branch" >&2
  exit 1
fi

echo "land.sh: PR #$prnum merged."

# --- local resync, best-effort ---
cur="$(git rev-parse --abbrev-ref HEAD)"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "land.sh: working tree has uncommitted changes — skipping local resync of '${base}'."
  echo "land.sh: when clean:  git checkout ${base} && git pull --ff-only && git fetch --prune"
  exit 0
fi

if ! git checkout "$base" >/dev/null 2>&1; then
  echo "land.sh: merged, but could not switch to '${base}' locally — resync by hand."
  exit 0
fi

git fetch --prune origin >/dev/null 2>&1 || true
if git merge --ff-only "origin/${base}" >/dev/null 2>&1; then
  echo "land.sh: ${base} fast-forwarded to $(git rev-parse --short HEAD)."
else
  echo "land.sh: could not fast-forward ${base} (local commits?) — run 'git pull' yourself."
fi

# Drop the merged local head branch.
if [ "$cur" != "$base" ] && git show-ref --verify --quiet "refs/heads/${cur}"; then
  if git branch -D "$cur" >/dev/null 2>&1; then
    echo "land.sh: deleted local branch '${cur}'."
  fi
fi

echo "land.sh: done — on ${base} at $(git rev-parse --short HEAD)."
