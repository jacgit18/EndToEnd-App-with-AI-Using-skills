#!/usr/bin/env bash
# SessionStart hook — mechanical catalog-drift glance.
#
# Runs the two unambiguous /sync-catalog checks and prints a short summary only
# when one trips (SessionStart stdout is added to the session's context):
#   1. skills on disk with no row in README.md
#   2. open SKILL-BACKLOG.md markers ("Memory: pending|TODO", "[ ] Built")
# Silent on a clean catalog and on resume/compact/clear restarts. Fixes nothing —
# hand drift to `catalog-drift-audit` / `/new-skill`.
#
# Checks that have nothing to check against are skipped, not failed: the README
# check needs a table row (`| ... |`) in README.md, the backlog check needs
# SKILL-BACKLOG.md. A working subset of the repo (stub README, no backlog) is
# therefore silent rather than noisy.
#
# Defensive by design, like log-skill.sh: always exits 0, never blocks, only reads.
set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# Only on a fresh start. No jq / no payload => assume fresh (harmless: still silent if clean).
payload="$(cat 2>/dev/null || true)"
if [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
  source_kind="$(printf '%s' "$payload" | jq -r '.source // "startup"' 2>/dev/null)"
  [ "$source_kind" = "startup" ] || exit 0
fi

[ -d .claude/skills ] || exit 0

MAX=5   # names listed per check before "+N more"
out=""

cap() { # cap <label> <newline-list>  -> "label: a, b, c (+N more)"
  local total shown more
  total="$(printf '%s\n' "$2" | grep -c .)"
  shown="$(printf '%s\n' "$2" | grep . | head -n "$MAX" | paste -sd, - | sed 's/,/, /g')"
  more=""; [ "$total" -gt "$MAX" ] && more=" (+$((total - MAX)) more)"
  printf '%s (%s): %s%s' "$1" "$total" "$shown" "$more"
}

if [ -f README.md ] && grep -q '^|' README.md; then
  missing=""
  while IFS= read -r skill_md; do
    name="$(basename "$(dirname "$skill_md")")"
    grep -qF "$name" README.md || missing="${missing}${name}"$'\n'
  done < <(find .claude/skills -name SKILL.md 2>/dev/null | sort)
  [ -n "$missing" ] && out="${out}- $(cap 'Skills with no README row' "$missing")"$'\n'
fi

if [ -f SKILL-BACKLOG.md ]; then
  open="$(grep -nE 'Memory:[[:space:]]*(pending|TODO)[[:space:]]*\.?$|^[[:space:]]*-?[[:space:]]*\[ \] Built' SKILL-BACKLOG.md 2>/dev/null | cut -d: -f1 | sed 's/^/line /')"
  [ -n "$open" ] && out="${out}- $(cap 'Open SKILL-BACKLOG.md markers' "$open")"$'\n'
fi

# Structural lint errors only (bad frontmatter, dead skill pointers). Warnings stay on demand:
#   scripts/skills/lint.sh
if [ -x scripts/skills/lint.sh ]; then
  lint_out="$(scripts/skills/lint.sh --quiet --errors-only 2>/dev/null | sed -n '/^ERRORS/,$p' | head -n 8)"
  [ -n "$lint_out" ] && out="${out}- Skill lint: ${lint_out}"$'\n'
fi

if [ -n "$out" ]; then
  printf 'Catalog drift check (mechanical, /sync-catalog subset):\n%sFix via `catalog-drift-audit` or `/new-skill`; nothing was changed.\n' "$out"
fi

exit 0
