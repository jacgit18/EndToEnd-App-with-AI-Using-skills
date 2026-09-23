#!/usr/bin/env bash
#
# batch-git-push.sh — stage, commit, and push changes in small batches
# so that no single push contains more than a set number of files.
#
# Each batch is committed with commit.sh (named-path staging, the sanity
# checks, the repo's Co-Authored-By trailer) and pushed with push.sh (timeout,
# HTTP/1.1 fallback, no retry on a rejection). It refuses to run if the index
# already holds staged files, and only pushes the branch that is checked out.
#
# Usage:
#   scripts/git/batch-git-push.sh [batch_size] [branch] [commit_prefix]
#
# Examples:
#   scripts/git/batch-git-push.sh                 # 90 files/batch, current branch
#   scripts/git/batch-git-push.sh 50              # 50 files/batch
#   scripts/git/batch-git-push.sh 90 main "Add notes"
#
# Env:
#   DRY_RUN=1   show what would happen without committing/pushing
#   INCLUDE_MODIFIED=1  also include tracked-but-modified/deleted files
#                       (default: only new/untracked files)

set -euo pipefail

BATCH="${1:-90}"
BRANCH="${2:-$(git rev-parse --abbrev-ref HEAD)}"
PREFIX="${3:-Add files}"
DRY_RUN="${DRY_RUN:-0}"
INCLUDE_MODIFIED="${INCLUDE_MODIFIED:-0}"

cd "$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "$CURRENT" ]]; then
  echo "batch-git-push.sh: '$BRANCH' is not the checked-out branch ('$CURRENT') —" >&2
  echo "  commits would land on '$CURRENT' and pushing '$BRANCH' would publish nothing new." >&2
  echo "  check out '$BRANCH' first." >&2
  exit 1
fi
if [[ "$DRY_RUN" != "1" ]] && ! git diff --cached --quiet; then
  echo "batch-git-push.sh: the index already holds staged files — commit or unstage them first," >&2
  echo "  otherwise they would be swept into batch 1." >&2
  exit 1
fi

# Collect the list of paths to process (NUL-separated for safe filenames).
if [[ "$INCLUDE_MODIFIED" == "1" ]]; then
  # Untracked + modified + deleted, path only.
  mapfile -d '' FILES < <(git -c core.quotepath=off status --porcelain -z -uall \
    | while IFS= read -r -d '' entry; do
        printf '%s\0' "${entry:3}"
        # A rename/copy is followed by a bare entry holding the old path — skip it.
        case "${entry:0:2}" in *R* | *C*) IFS= read -r -d '' _old ;; esac
      done)
else
  mapfile -d '' FILES < <(git ls-files --others --exclude-standard -z)
fi

TOTAL=${#FILES[@]}
echo "Repo:        $(pwd)"
echo "Branch:      $BRANCH"
echo "Batch size:  $BATCH"
echo "Files found: $TOTAL"
[[ "$DRY_RUN" == "1" ]] && echo "MODE:        dry run (no writes)"
echo

if (( TOTAL == 0 )); then
  echo "Nothing to do."
  exit 0
fi

i=0
batch_num=1
while (( i < TOTAL )); do
  chunk=("${FILES[@]:i:BATCH}")
  count=${#chunk[@]}
  msg="${PREFIX} batch ${batch_num} (${count} files)"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] batch ${batch_num}: ${count} files -> \"${msg}\""
  else
    "$HERE/commit.sh" -m "$msg" -- "${chunk[@]}"
    echo "Committed batch ${batch_num}: ${count} files"
    "$HERE/push.sh" origin "$BRANCH"
    echo "Pushed batch ${batch_num}"
  fi

  i=$(( i + BATCH ))
  batch_num=$(( batch_num + 1 ))
done

echo
echo "Done. Remaining untracked: $(git ls-files --others --exclude-standard | wc -l)"
