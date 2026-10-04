#!/usr/bin/env bash
# Run every scripts/tests/test_*.sh. One command, plain bash, no bats.
#   scripts/tests/run.sh [name-fragment]      e.g.  scripts/tests/run.sh commit
# Exits non-zero if any case fails, or if the run touched the real prompt logs / settings.local.json.
# SCRIPTS_DIR=/path/to/modified/scripts points the tests at another copy of scripts/.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
guard() { { find "$repo/.claude/_Prompts/logs" -type f -printf '%p %s %T@\n' 2>/dev/null
            ls -l --time-style=+%s "$repo/.claude/settings.local.json" 2>/dev/null; } | sort; }
before="$(guard)"
start=$SECONDS; failed=0; pass=0; fail=0
for f in "$here"/test_*"${1:-}"*.sh; do
  [ -f "$f" ] || continue
  out="$(bash "$f" 2>&1)"; rc=$?
  printf '%s\n' "$out"
  pass=$((pass + $(printf '%s\n' "$out" | grep -c '^PASS ')))
  fail=$((fail + $(printf '%s\n' "$out" | grep -c '^FAIL ')))
  [ "$rc" -eq 0 ] || failed=1
done
if [ "$(guard)" != "$before" ]; then
  echo "FAIL  guard: the suite modified the real .claude/_Prompts/logs or settings.local.json"
  fail=$((fail + 1)); failed=1
fi
echo "== $pass passed, $fail failed in $((SECONDS - start))s"
exit "$failed"
