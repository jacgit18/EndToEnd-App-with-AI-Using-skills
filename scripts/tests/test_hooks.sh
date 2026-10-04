#!/usr/bin/env bash
# Hooks: log-prompt, log-skill, context-watch, catalog-drift-check.
. "$(dirname "$0")/lib.sh"
command -v jq >/dev/null 2>&1 || { echo "SKIP  hooks (jq not installed)"; exit 0; }

HOOKS="$SCRIPTS/hooks"
BAD_INPUTS=('' 'not json at all' 'null' '[]' '{}' '[1,2,3]' '"just a string"' '{"prompt":null}'
            '{"prompt":"héllo wörld 日本語 🚀","session_id":"abcdef123456"}' '{"tool_name":"Skill"}')

# --- shared: every hook exits 0 and prints nothing on hostile input, in a project dir with a space ---
hook_robust() { # hook_robust <script>
  local proj="$T/my proj"; mkdir -p "$proj"; export CLAUDE_PROJECT_DIR="$proj"
  local in
  for in in "${BAD_INPUTS[@]}"; do
    run_in "$in" bash "$1"
    assert_status "$RC" 0 "exit on input [$in]"
    assert_eq "$OUT" "" "silent on input [$in]"
  done
}
t_prompt_robust()  { hook_robust "$HOOKS/log-prompt.sh"; }
t_skill_robust()   { hook_robust "$HOOKS/log-skill.sh"; }
t_cw_robust()      { hook_robust "$HOOKS/context-watch.sh"; }
t_drift_robust()   { hook_robust "$HOOKS/catalog-drift-check.sh"; }
case_ "log-prompt: exit 0 + silent on empty/garbage/null/array/{}/unicode, path with space" t_prompt_robust
case_ "log-skill: exit 0 + silent on empty/garbage/null/array/{}/unicode, path with space" t_skill_robust
case_ "context-watch: exit 0 + silent on empty/garbage/null/array/{}/unicode, path with space" t_cw_robust
case_ "catalog-drift-check: exit 0 + silent on empty/garbage/null/array/{}/unicode, path with space" t_drift_robust

t_prompt_writes_only_log() {
  local proj="$T/my proj"; mkdir -p "$proj"; export CLAUDE_PROJECT_DIR="$proj"
  echo keep > "$proj/other.txt"
  local before; before="$(snap "$T")"
  run_in '{"prompt":"héllo 日本語 🚀\nline2","session_id":"abcdef123456789"}' bash "$HOOKS/log-prompt.sh"
  assert_status "$RC" 0
  local new; new="$(diff <(echo "$before") <(snap "$T") | grep '^[<>]' | grep -v '\.fails')"
  assert_contains "$new" "my proj/.claude/_Prompts/logs/" "new file is in the log dir"
  assert_eq "$(printf '%s\n' "$new" | grep -c .)" "1" "exactly one file changed"
  local log; log="$(cat "$proj"/.claude/_Prompts/logs/*.md)"
  assert_contains "$log" "session abcdef12" "8-char session id"
  assert_contains "$log" "héllo 日本語 🚀" "unicode prompt logged"
  assert_eq "$(ls -A "$HOME")" "" "HOME untouched"
}
case_ "log-prompt: valid payload appends to its own dated log only" t_prompt_writes_only_log

t_skill_logs() {
  local payload='{"tool_name":"Skill","tool_input":{"skill":"ambiguity-gate","args":"a `b`\nc"},"session_id":"zzzzzzzz99"}'
  run_in "$payload" bash "$HOOKS/log-skill.sh"; assert_status "$RC" 0
  local log; log="$(cat "$CLAUDE_PROJECT_DIR"/.claude/_Prompts/logs/*-skills.md)"
  assert_contains "$log" '`ambiguity-gate`' "skill name recorded"
  assert_contains "$log" "session zzzzzzzz" "session recorded"
  assert_eq "$(printf '%s\n' "$log" | grep -c 'ambiguity-gate')" "1" "one line per event"
  # wrong tool name -> no extra line
  run_in '{"tool_name":"Bash","tool_input":{"skill":"x"}}' bash "$HOOKS/log-skill.sh"
  assert_eq "$(cat "$CLAUDE_PROJECT_DIR"/.claude/_Prompts/logs/*-skills.md | grep -c '`x`')" "0" "non-Skill tool ignored"
}
case_ "log-skill: Skill event logs one clean line; other tools ignored" t_skill_logs

t_skill_global() {
  local payload='{"tool_name":"Skill","tool_input":{"skill":"foo-bar","args":"private text"},"session_id":"sess1234abcd"}'
  mkdir -p "$T/other" "$T/gl"
  CLAUDE_PROJECT_DIR="$T/other" SKILL_LOG_GLOBAL=1 SKILL_LOG_DIR="$T/gl" run_in "$payload" bash "$HOOKS/log-skill.sh"
  assert_status "$RC" 0
  local log; log="$(cat "$T/gl"/*-skills.md)"
  assert_contains "$log" "[project: other]"
  assert_not_contains "$log" "private text" "args dropped in global mode"
  assert_no_file "$T/other/.claude" "other project got no log dir"
  # defers when the project has its own hook
  mkdir -p "$T/own/scripts/hooks"; cp "$HOOKS/log-skill.sh" "$T/own/scripts/hooks/"
  CLAUDE_PROJECT_DIR="$T/own" SKILL_LOG_GLOBAL=1 SKILL_LOG_DIR="$T/gl2" run_in "$payload" bash "$HOOKS/log-skill.sh"
  assert_no_file "$T/gl2" "global mode defers to project hook"
  # no SKILL_LOG_DIR -> nothing written
  CLAUDE_PROJECT_DIR="$T/other" SKILL_LOG_GLOBAL=1 run_in "$payload" bash "$HOOKS/log-skill.sh"
  assert_no_file "$T/other/.claude"
}
case_ "log-skill: global mode tags project, drops args, defers, needs SKILL_LOG_DIR" t_skill_global

# --- context-watch ---
mk_transcript() { # mk_transcript file used_tokens
  {
    echo '{"type":"user","message":{"content":"hi"}}'
    printf '{"type":"assistant","message":{"usage":{"input_tokens":%s,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}}\n' "$2"
    echo '{"type":"assistant","message":{"usage":{"input_tok'     # malformed (truncated) line
    echo 'null'
    echo '{"type":"assistant","message":{"usage":null}}'           # final null-usage line
  } > "$1"
}
t_cw_once() {
  mk_transcript "$T/tr.jsonl" 150000
  local p='{"transcript_path":"'"$T"'/tr.jsonl","session_id":"sess0001xxxx"}'
  run_in "$p" bash "$HOOKS/context-watch.sh"
  assert_status "$RC" 0
  assert_contains "$OUT" "[context-watch]" "fires at 150k/200k despite malformed + null-usage lines"
  assert_contains "$OUT" "~150000/200000"
  assert_file "$CLAUDE_PROJECT_DIR/.claude/_Prompts/logs/.handoff-armed-sess0001"
  run_in "$p" bash "$HOOKS/context-watch.sh"
  assert_status "$RC" 0; assert_eq "$OUT" "" "second prompt, same session: silent"
  run_in '{"transcript_path":"'"$T"'/tr.jsonl","session_id":"sess0002xxxx"}' bash "$HOOKS/context-watch.sh"
  assert_contains "$OUT" "[context-watch]" "a different session fires again"
  # nothing else written
  assert_eq "$(find "$CLAUDE_PROJECT_DIR" -type f | grep -vc '\.handoff-armed-')" "0" "only flag files written"
}
case_ "context-watch: fires once per session; survives malformed line + final null-usage line" t_cw_once

t_cw_below() {
  mk_transcript "$T/tr.jsonl" 1000
  run_in '{"transcript_path":"'"$T"'/tr.jsonl","session_id":"s"}' bash "$HOOKS/context-watch.sh"
  assert_status "$RC" 0; assert_eq "$OUT" ""
  assert_no_file "$CLAUDE_PROJECT_DIR/.claude" "no flag/dir created below threshold"
  CONTEXT_LIMIT=1500 run_in '{"transcript_path":"'"$T"'/tr.jsonl","session_id":"s"}' bash "$HOOKS/context-watch.sh"
  assert_contains "$OUT" "[context-watch]" "CONTEXT_LIMIT knob respected"
  # transcript missing / all garbage
  run_in '{"transcript_path":"/nonexistent/x","session_id":"s"}' bash "$HOOKS/context-watch.sh"
  assert_status "$RC" 0; assert_eq "$OUT" ""
  printf 'garbage\n{{{\n' > "$T/bad.jsonl"
  run_in '{"transcript_path":"'"$T"'/bad.jsonl","session_id":"s"}' bash "$HOOKS/context-watch.sh"
  assert_status "$RC" 0; assert_eq "$OUT" ""
}
case_ "context-watch: silent below threshold / missing / garbage transcript; limit knob" t_cw_below

# --- catalog-drift-check ---
drift_sandbox() { # sandbox with scripts + one broken skill
  local p="$CLAUDE_PROJECT_DIR"; copy_scripts "$p"
  mkdir -p "$p/.claude/skills/broken"; echo "# no frontmatter" > "$p/.claude/skills/broken/SKILL.md"
}
t_drift_resume() {
  drift_sandbox
  run_in '{"source":"startup"}' bash "$HOOKS/catalog-drift-check.sh"
  assert_status "$RC" 0; assert_contains "$OUT" "Catalog drift check" "startup reports lint errors"
  assert_contains "$OUT" "broken"
  local s
  for s in resume compact clear; do
    run_in "{\"source\":\"$s\"}" bash "$HOOKS/catalog-drift-check.sh"
    assert_status "$RC" 0; assert_eq "$OUT" "" "silent on $s"
  done
  run_in '' bash "$HOOKS/catalog-drift-check.sh"
  assert_contains "$OUT" "Catalog drift check" "no payload = assume fresh"
}
case_ "catalog-drift-check: reports on startup, silent on resume/compact/clear" t_drift_resume

t_drift_clean() {
  local p="$CLAUDE_PROJECT_DIR"; copy_scripts "$p"
  mkskill "$p/.claude/skills" alpha "A fine skill."
  printf '# stub\n' > "$p/README.md"
  local before; before="$(snap "$p")"
  run_in '{"source":"startup"}' bash "$HOOKS/catalog-drift-check.sh"
  assert_status "$RC" 0; assert_eq "$OUT" "" "clean catalog is silent"
  assert_eq "$(snap "$p")" "$before" "read-only"
  # README with a table that omits the skill -> flagged
  printf '# r\n| skill | desc |\n|---|---|\n| other | x |\n' > "$p/README.md"
  run_in '{"source":"startup"}' bash "$HOOKS/catalog-drift-check.sh"
  assert_contains "$OUT" "Skills with no README row (1): alpha"
  # open backlog marker
  printf -- '- [ ] Built thing\n' > "$p/SKILL-BACKLOG.md"
  run_in '{"source":"startup"}' bash "$HOOKS/catalog-drift-check.sh"
  assert_contains "$OUT" "Open SKILL-BACKLOG.md markers (1): line 1"
}
case_ "catalog-drift-check: clean catalog silent + read-only; README/backlog drift flagged" t_drift_clean

finish
