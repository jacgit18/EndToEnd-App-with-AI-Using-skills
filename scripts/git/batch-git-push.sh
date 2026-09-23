#!/usr/bin/env bash
#
# chunked-push.sh — stage, commit, and push changes in small batches
# so that no single push contains more than a set number of files.
#
# Usage:
#   scripts/chunked-push.sh [batch_size] [branch] [commit_prefix]
#
# Examples:
#   scripts/chunked-push.sh                 # 90 files/batch, current branch
#   scripts/chunked-push.sh 50              # 50 files/batch
#   scripts/chunked-push.sh 90 main "Add notes"
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

# Collect the list of paths to process (NUL-separated for safe filenames).
if [[ "$INCLUDE_MODIFIED" == "1" ]]; then
  # Untracked + modified + deleted, path only.
  mapfile -d '' FILES < <(git -c core.quotepath=off status --porcelain -z -uall \
    | while IFS= read -r -d '' entry; do printf '%s\0' "${entry:3}"; done)
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
    printf '%s\0' "${chunk[@]}" | git add --pathspec-from-file=- --pathspec-file-nul
    git commit -q -m "$msg"
    echo "Committed batch ${batch_num}: ${count} files"
    git push -q origin "$BRANCH"
    echo "Pushed batch ${batch_num}"
  fi

  i=$(( i + BATCH ))
  batch_num=$(( batch_num + 1 ))
done

echo
echo "Done. Remaining untracked: $(git ls-files --others --exclude-standard | wc -l)"
