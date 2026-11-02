#!/usr/bin/env bash
# scripts/rules/sync-check.sh: drift between global and project rule copies, INDEX rows.
. "$(dirname "$0")/lib.sh"

mkrules() { # mkrules  -> $T/g and $T/p with one shared rule and an INDEX row
  mkdir -p "$T/g" "$T/p"
  echo "rule a" > "$T/g/a.md"; echo "rule a" > "$T/p/a.md"
  printf '| `a.md` | x | y |\n' > "$T/p/INDEX.md"
}
t_clean() { mkrules; RULES_GLOBAL="$T/g" RULES_PROJECT="$T/p" run bash "$SCRIPTS/rules/sync-check.sh"; assert_status "$RC" 0; }
case_ "sync-check: identical copies with an INDEX row pass" t_clean
t_drift() { mkrules; echo more >> "$T/g/a.md"; RULES_GLOBAL="$T/g" RULES_PROJECT="$T/p" run bash "$SCRIPTS/rules/sync-check.sh"; assert_status "$RC" 1; assert_contains "$OUT" "differs: a.md"; }
case_ "sync-check: a differing copy fails" t_drift
t_noindex() { mkrules; echo x > "$T/p/b.md"; RULES_GLOBAL="$T/g" RULES_PROJECT="$T/p" run bash "$SCRIPTS/rules/sync-check.sh"; assert_status "$RC" 1; assert_contains "$OUT" "no INDEX row: b.md"; }
case_ "sync-check: a rule with no INDEX row fails" t_noindex
t_projonly() { mkrules; echo x > "$T/p/b.md"; printf '| `b.md` | x | y |\n' >> "$T/p/INDEX.md"; RULES_GLOBAL="$T/g" RULES_PROJECT="$T/p" run bash "$SCRIPTS/rules/sync-check.sh"; assert_status "$RC" 0; }
case_ "sync-check: a project-only rule with a row passes" t_projonly
finish
