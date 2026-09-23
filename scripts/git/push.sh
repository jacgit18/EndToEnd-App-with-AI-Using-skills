#!/usr/bin/env bash
#
# push.sh — push the current branch with a timeout, an HTTP/1.1 fallback, and
# one retry, so a stalled push fails fast instead of hanging a session.
#
# Always passes -u, so the local branch gets its upstream link on the first
# push (no lingering "Publish Branch" prompt in editors); re-setting an
# already-correct upstream is a harmless no-op.
#
#   scripts/git/push.sh [remote=origin] [branch=current]
#
# Env:
#   PUSH_TIMEOUT=90   per-attempt timeout, seconds

set -uo pipefail

top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "push.sh: not a git repo" >&2; exit 1; }
cd "$top" || exit 1

remote="${1:-origin}"
branch="${2:-$(git rev-parse --abbrev-ref HEAD)}"
t="${PUSH_TIMEOUT:-90}"

# `timeout` is GNU coreutils; macOS ships it as `gtimeout` (brew coreutils) or
# not at all. Without it, push without a per-attempt cap rather than failing —
# the HTTP/1.1 fallback and retry still apply, just not the hang guard.
if command -v timeout >/dev/null 2>&1; then
  cap() { timeout "$t" "$@"; }
elif command -v gtimeout >/dev/null 2>&1; then
  cap() { gtimeout "$t" "$@"; }
else
  echo "push.sh: no timeout/gtimeout on PATH — pushing without a stall guard" >&2
  cap() { "$@"; }
fi

attempt() {
  local label="$1"; shift
  echo "push.sh: ${label} ..."
  if cap "$@"; then
    echo "push.sh: ${label} — ok"
    return 0
  fi
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "push.sh: ${label} — timed out after ${t}s"
  else
    echo "push.sh: ${label} — failed (exit ${rc})"
  fi
  return 1
}

attempt "push"                git push -u "$remote" "$branch" && exit 0
attempt "push (HTTP/1.1)"     git -c http.version=HTTP/1.1 push -u "$remote" "$branch" && exit 0
sleep 3
attempt "push (retry, HTTP/1.1)" git -c http.version=HTTP/1.1 push -u "$remote" "$branch" && exit 0

echo "push.sh: all attempts failed — the remote may be having trouble; retry shortly." >&2
exit 1
