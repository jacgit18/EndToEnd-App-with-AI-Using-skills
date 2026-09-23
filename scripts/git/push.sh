#!/usr/bin/env bash
#
# push.sh — push the current branch with a timeout, an HTTP/1.1 fallback, and
# one retry, so a stalled push fails fast instead of hanging a session.
#
# Always passes -u, so the local branch gets its upstream link on the first
# push (no lingering "Publish Branch" prompt in editors); re-setting an
# already-correct upstream is a harmless no-op.
#
# Only a stall (timeout, exit 124) or a connection failure (git exit 128) is
# retried. A rejection — non-fast-forward, protected branch, a hook — exits
# immediately: retrying it cannot succeed and it needs a human.
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

if [ "$branch" = "HEAD" ]; then
  echo "push.sh: detached HEAD — pass a branch name." >&2
  exit 1
fi

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

# Runs one push attempt. Exits 0 on success and exits 1 straight away on a
# non-transient failure (a rejection); returns 1 only for a stall/connection
# failure, which the caller may retry.
attempt() {
  local label="$1" rc; shift
  echo "push.sh: ${label} ..."
  cap "$@"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "push.sh: ${label} — ok"
    exit 0
  fi
  if [ "$rc" -eq 124 ]; then
    echo "push.sh: ${label} — timed out after ${t}s"
    return 1
  fi
  if [ "$rc" -eq 128 ]; then
    echo "push.sh: ${label} — connection failure (exit 128)"
    return 1
  fi
  echo "push.sh: ${label} — rejected or failed (exit ${rc}); not a transient stall, so not retrying." >&2
  exit 1
}

attempt "push"                git push -u "$remote" "$branch"
attempt "push (HTTP/1.1)"     git -c http.version=HTTP/1.1 push -u "$remote" "$branch"
sleep 3
attempt "push (retry, HTTP/1.1)" git -c http.version=HTTP/1.1 push -u "$remote" "$branch"

echo "push.sh: all attempts failed — the remote may be having trouble; retry shortly." >&2
exit 1
