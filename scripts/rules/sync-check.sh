#!/usr/bin/env bash
# Rule-copy drift check. Exits 1 when a rule file differs between the global and the project copy,
# or when a project rule file has no row in INDEX.md.
#   scripts/rules/sync-check.sh
# RULES_GLOBAL / RULES_PROJECT point it at other folders (used by the tests).
set -u
repo="$(cd "$(dirname "$0")/../.." && pwd)"
global="${RULES_GLOBAL:-$HOME/.claude/rules}"
proj="${RULES_PROJECT:-$repo/.claude/rules}"
bad=0
for f in "$proj"/*.md; do
  b="$(basename "$f")"
  [ "$b" = INDEX.md ] && continue
  grep -q "\`$b\`" "$proj/INDEX.md" || { echo "no INDEX row: $b"; bad=1; }
  # project-only rules (no global copy) are fine; a shared one must be identical
  if [ -f "$global/$b" ] && ! cmp -s "$f" "$global/$b"; then
    echo "differs: $b (global vs project)"; bad=1
  fi
done
[ "$bad" -eq 0 ] && echo "rules in sync"
exit "$bad"
