#!/usr/bin/env bash
# Open a fresh Claude Code session seeded with the most recent handoff file.
#
# Pairs with scripts/hooks/context-watch.sh: when that hook trips, Claude writes
# a handoff into .claude/handoffs/ . Run this in a new terminal to start a clean
# session that already has that context.
#
#   scripts/session/resume.sh            # newest handoff in .claude/handoffs/
#   scripts/session/resume.sh path.md    # a specific handoff file
#   scripts/session/resume.sh some/dir   # newest handoff in some/dir
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
arg="${1:-$PROJECT_DIR/.claude/handoffs}"

if [ -f "$arg" ]; then
  latest="$arg"
elif [ -d "$arg" ]; then
  latest="$(ls -t "$arg"/handoff-*.md 2>/dev/null | head -n1 || true)"
else
  latest=""   # dir not created yet == no handoffs
fi

[ -n "${latest:-}" ] && [ -f "$latest" ] || {
  echo "resume: no handoff-*.md found in ${arg}" >&2
  echo "       (the context-watch hook writes one once context crosses the threshold)" >&2
  exit 1
}

command -v claude >/dev/null 2>&1 || {
  echo "resume: 'claude' is not on PATH" >&2
  exit 127
}

echo "resume: seeding a new session from ${latest#"$PROJECT_DIR"/}" >&2
exec claude "Resume this work from the handoff below. Confirm you have it, restate the next steps in order, then continue.

$(cat "$latest")"
