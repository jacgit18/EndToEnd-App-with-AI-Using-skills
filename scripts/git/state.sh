#!/usr/bin/env bash
#
# state.sh — one-call repo snapshot for pre-commit orientation.
#
# Replaces the usual `git status` + `git diff --stat` + `git diff --cached` +
# `git log --oneline -5` ritual with a single compact read. Read-only: it
# writes nothing and stages nothing.
#
# Usage:
#   scripts/git/state.sh [log_count=3]

set -uo pipefail

top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "state.sh: not a git repo"; exit 0; }
cd "$top" || exit 0

n="${1:-3}"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [ -n "$upstream" ]; then
  ab="$(git rev-list --left-right --count "${upstream}...HEAD" 2>/dev/null || echo '? ?')"
  behind="${ab%%[[:space:]]*}"
  ahead="${ab##*[[:space:]]}"
  printf 'branch: %s   (vs %s — ahead %s, behind %s)\n' "$branch" "$upstream" "$ahead" "$behind"
else
  printf 'branch: %s   (no upstream)\n' "$branch"
fi

staged="$(git diff --cached --name-status)"
unstaged="$(git diff --name-status)"
untracked="$(git ls-files --others --exclude-standard)"

echo
if [ -n "$staged" ]; then
  echo "staged:"
  printf '%s\n' "$staged" | sed 's/^/  /'
  git diff --cached --shortstat | sed 's/^ */  /'
else
  echo "staged: (none)"
fi

echo
if [ -n "$unstaged" ]; then
  echo "unstaged (tracked):"
  printf '%s\n' "$unstaged" | sed 's/^/  /'
  git diff --shortstat | sed 's/^ */  /'
else
  echo "unstaged (tracked): (none)"
fi

echo
if [ -n "$untracked" ]; then
  echo "untracked:"
  printf '%s\n' "$untracked" | sed 's/^/  /'
else
  echo "untracked: (none)"
fi

echo
echo "recent commits:"
git log --oneline -n "$n" | sed 's/^/  /'
