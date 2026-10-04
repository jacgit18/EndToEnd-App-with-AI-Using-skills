#!/usr/bin/env bash
# Skill tooling: lint.sh / lint.py and profile.sh / profile.py, plus syntax of every script.
. "$(dirname "$0")/lib.sh"
command -v python3 >/dev/null 2>&1 || { echo "SKIP  skills (python3 not installed)"; exit 0; }

S="$SCRIPTS/skills"

t_syntax() {
  local f
  for f in "$SCRIPTS"/*/*.sh; do
    run bash -n "$f"; assert_status "$RC" 0 "bash -n $f"
  done
  for f in "$SCRIPTS"/*/*.py; do
    run python3 -c "import sys; compile(open(sys.argv[1]).read(), sys.argv[1], 'exec')" "$f"
    assert_status "$RC" 0 "compile $f"
  done
}
case_ "syntax: bash -n on every .sh, compile() on every .py" t_syntax

# --- lint ---
LONG="$(python3 -c "print('word ' * 320)")"   # 1600 chars
broken_sandbox() {
  local r="$CLAUDE_PROJECT_DIR/.claude/skills"
  mkskill "$r" alpha "A fine skill."
  mkdir -p "$r/nofm"; echo "# no frontmatter" > "$r/nofm/SKILL.md"
  mkskill "$r" beta "Fine."; sed -i 's/^name: beta/name: gamma/' "$r/beta/SKILL.md"
  mkskill "$r" dead 'Use `ghost-skill` for this.'
  mkskill "$r" long "$LONG"
  mkskill "$r" comp "Has a companion."; echo "# extra" > "$r/comp/extra.md"
}
t_lint_broken() {
  broken_sandbox
  run bash "$S/lint.sh" --strict
  assert_status "$RC" 1 "--strict exits 1 on errors"
  local errs warns
  errs="$(printf '%s\n' "$OUT" | sed -n '/^ERRORS/,/^$/p')"
  warns="$(printf '%s\n' "$OUT" | sed -n '/^WARNINGS/,/^$/p')"
  assert_contains "$errs" "nofm/SKILL.md: line 1 is not '---'" "missing frontmatter"
  assert_contains "$errs" "name 'gamma' != directory 'beta'" "name != dir"
  assert_contains "$errs" "names \`ghost-skill\`" "dead pointer"
  assert_contains "$warns" "long/SKILL.md: description" "over 1536 warning"
  assert_contains "$warns" "(> 1536)"
  assert_contains "$warns" "companion 'extra.md' is never mentioned" "unreferenced companion"
  assert_not_contains "$errs" "alpha" "clean skill not flagged"
  run bash "$S/lint.sh"; assert_status "$RC" 0 "no --strict: exit 0 even with errors"
}
case_ "lint.sh: reports each seeded defect; --strict exits 1, plain run exits 0" t_lint_broken

t_lint_clean_and_budget() {
  local r="$CLAUDE_PROJECT_DIR/.claude/skills"
  mkskill "$r" alpha "A fine skill."
  mkskill "$r" over "$(python3 -c "print('x' * 500)")"    # > 430 and < 1536
  run bash "$S/lint.sh" --strict
  assert_status "$RC" 0 "clean copy exits 0 under --strict"
  assert_contains "$OUT" "LISTING-BUDGET WARNINGS" "separate 430 section"
  assert_not_contains "$(printf '%s\n' "$OUT" | sed -n '/^WARNINGS/,/^$/p')" "over/SKILL.md" "not in the 1536 section"
  run bash "$S/lint.sh" --strict --errors-only
  assert_status "$RC" 0
  assert_not_contains "$OUT" "LISTING-BUDGET" "--errors-only drops the budget section"
  assert_not_contains "$OUT" "WARNINGS"
  run bash "$S/lint.sh" --quiet
  assert_eq "$OUT" "" "--quiet ignores budget-only warnings"
  rm -r "$r/over"
  run bash "$S/lint.sh" --quiet; assert_eq "$OUT" "" "--quiet silent on a fully clean catalog"
}
case_ "lint.sh: clean copy passes --strict; 430 budget warning separate and not in --errors-only" t_lint_clean_and_budget

t_lint_symlink() {
  local r="$CLAUDE_PROJECT_DIR/.claude/skills"
  mkskill "$r" alpha "A fine skill."
  mkdir -p "$T/elsewhere/bad"; echo "# no frontmatter" > "$T/elsewhere/bad/SKILL.md"
  ln -s "$T/elsewhere/bad" "$r/bad"
  run bash "$S/lint.sh" --strict
  assert_status "$RC" 0 "symlinked skill dir skipped"
  assert_contains "$OUT" "skills: 1 "
}
case_ "lint.sh: symlinked skill directories are skipped" t_lint_symlink

t_lint_nested_and_args() {
  local r="$CLAUDE_PROJECT_DIR/.claude/skills"
  mkskill "$r/Group" nested "Nested skill."
  mkskill "$r" arg "Takes args."; echo 'run with $1 please' >> "$r/arg/SKILL.md"
  run bash "$S/lint.sh" --strict
  assert_status "$RC" 1
  assert_contains "$OUT" "nested skills are not discovered"
  assert_contains "$OUT" "arg/SKILL.md: '\$<digit>'"
}
case_ "lint.sh: nested skills and \$<digit> in body are errors" t_lint_nested_and_args

t_lint_no_python() {
  mkdir "$T/bin"; ln -s "$(command -v git)" "$T/bin/git"; ln -s "$(command -v dirname)" "$T/bin/dirname"
  PATH="$T/bin" run /bin/bash "$S/lint.sh" --strict
  assert_status "$RC" 1 "--strict without python3 fails"
  assert_contains "$OUT" "python3 not found"
  PATH="$T/bin" run /bin/bash "$S/lint.sh"
  assert_status "$RC" 0 "non-strict without python3 is a no-op"
}
case_ "lint.sh: --strict exits 1 without python3, plain run exits 0" t_lint_no_python

t_lint_real() {
  CLAUDE_PROJECT_DIR="$REPO" run bash "$S/lint.sh" --strict
  assert_status "$RC" 0 "real catalog has no lint errors"
}
case_ "lint.sh --strict on the REAL catalog exits 0 (read-only)" t_lint_real

# --- profile ---
prof_sandbox() {
  local r="$CLAUDE_PROJECT_DIR/.claude/skills" n
  for n in alpha beta gamma delta; do mkskill "$r" "$n" "Skill $n."; done
  printf '# core\nalpha\n' > "$r/CORE.txt"
  mkdir -p "$CLAUDE_PROJECT_DIR/.claude"
}
SETTINGS_REL=".claude/settings.local.json"
jqv() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2]))" "$CLAUDE_PROJECT_DIR/$SETTINGS_REL" "$1"; }

t_profile_roundtrip() {
  prof_sandbox
  echo '{"other":{"keep":1},"skillOverrides":{"gamma":"off","plugin:x":"name-only","alpha":"off"}}' > "$CLAUDE_PROJECT_DIR/$SETTINGS_REL"
  run bash "$S/profile.sh" core; assert_status "$RC" 0
  assert_eq "$(jqv "d['skillOverrides']['beta'], d['skillOverrides']['delta']")" "('name-only', 'name-only')"
  assert_eq "$(jqv "d['skillOverrides']['gamma']")" "off" "'off' preserved (not in core)"
  assert_eq "$(jqv "d['skillOverrides']['alpha']")" "off" "'off' preserved (in core)"
  assert_eq "$(jqv "d['skillOverrides']['plugin:x']")" "name-only" "non-catalog override preserved"
  assert_eq "$(jqv "d['other']")" "{'keep': 1}" "unrelated key preserved"
  local sum; sum="$(md5sum < "$CLAUDE_PROJECT_DIR/$SETTINGS_REL")"
  run bash "$S/profile.sh" status; assert_status "$RC" 0
  assert_contains "$OUT" "catalog skills: 4 | fully listed: 0 | overridden: 4"
  assert_eq "$(md5sum < "$CLAUDE_PROJECT_DIR/$SETTINGS_REL")" "$sum" "status is read-only"
  run bash "$S/profile.sh" all; assert_status "$RC" 0
  assert_eq "$(jqv "sorted(d['skillOverrides'])")" "['alpha', 'gamma', 'plugin:x']" "only name-only catalog overrides removed"
  assert_eq "$(jqv "d['skillOverrides']['gamma']")" "off"
  assert_eq "$(jqv "d['other']")" "{'keep': 1}"
  run bash "$S/profile.sh" toggle; assert_status "$RC" 0
  assert_contains "$OUT" "switching to core"
  run bash "$S/profile.sh" toggle; assert_contains "$OUT" "switching to all"
}
case_ "profile.sh: core/all/status/toggle round trip keeps unrelated keys and 'off' overrides" t_profile_roundtrip

t_profile_nofile() {
  prof_sandbox
  run bash "$S/profile.sh" all; assert_status "$RC" 0
  assert_no_file "$CLAUDE_PROJECT_DIR/$SETTINGS_REL"; # no empty file created
  run bash "$S/profile.sh" status; assert_status "$RC" 0
  assert_no_file "$CLAUDE_PROJECT_DIR/$SETTINGS_REL"
  run bash "$S/profile.sh" core; assert_status "$RC" 0
  assert_eq "$(jqv "len(d['skillOverrides'])")" "3" "core creates the file when it has something to say"
  rm "$CLAUDE_PROJECT_DIR/$SETTINGS_REL"
  run bash "$S/profile.sh" bogus; assert_nonzero "$RC"
}
case_ "profile.sh: 'all'/'status' create no settings file when none exists" t_profile_nofile

t_profile_badjson() {
  prof_sandbox
  printf '{bad json,' > "$CLAUDE_PROJECT_DIR/$SETTINGS_REL"
  local sum m; sum="$(md5sum < "$CLAUDE_PROJECT_DIR/$SETTINGS_REL")"
  for m in core all status toggle; do
    run bash "$S/profile.sh" "$m"
    assert_status "$RC" 1 "$m exits 1"
    assert_contains "$OUT" "not valid JSON"
    assert_eq "$(printf '%s\n' "$OUT" | grep -c .)" "1" "$m: one-line error, no traceback"
    assert_eq "$(md5sum < "$CLAUDE_PROJECT_DIR/$SETTINGS_REL")" "$sum" "$m: file untouched"
  done
}
case_ "profile.sh: invalid JSON -> one-line error, exit 1, file untouched" t_profile_badjson

finish
