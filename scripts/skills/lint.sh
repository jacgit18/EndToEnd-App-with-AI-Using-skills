#!/usr/bin/env bash
# Mechanical skill-catalog lint (read-only). See lint.py for the checks.
#   scripts/skills/lint.sh [--strict] [--quiet] [--pairs]
set -u
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 0
command -v python3 >/dev/null 2>&1 || { echo "lint.sh: python3 not found" >&2; exit 0; }
exec python3 "$(dirname "$0")/lint.py" "$@"
