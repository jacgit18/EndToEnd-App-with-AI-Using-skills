#!/usr/bin/env bash
# Toggle the skill profile in .claude/settings.local.json (see profile.py).
#   scripts/skills/profile.sh core|all|status
set -u
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 1
command -v python3 >/dev/null 2>&1 || { echo "profile.sh: python3 not found" >&2; exit 1; }
exec python3 "$(dirname "$0")/profile.py" "$@"
