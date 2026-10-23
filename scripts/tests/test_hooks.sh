#!/usr/bin/env bash
# Hooks: log-prompt, log-skill, context-watch, catalog-drift-check, guard-pr-create.
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

# --- guard-pr-create: branch naming (rules/branch-naming.md) -----------------------------------
# The hook reads {cwd, tool_input.command}; a repo with scripts/pr-body.mjs gets past the "no PR kit" block.
guard_on_branch() { # guard_on_branch <branch> [command]  -> sets OUT/RC
  local repo="$T/guard repo"
  if [ ! -d "$repo/.git" ]; then mkrepo_commit "$repo"; mkdir -p "$repo/scripts"; : > "$repo/scripts/pr-body.mjs"; fi
  git -C "$repo" switch -q -C "$1"
  local cmd="${2:-gh pr create --title t --body-file body.md}"
  run_in "$(jq -n --arg cwd "$repo" --arg c "$cmd" '{cwd:$cwd,tool_input:{command:$c}}')" bash "$HOOKS/guard-pr-create.sh"
}
t_guard_allows_names() {
  local b
  for b in f-rest-day-timer b-second-rest-day d-readme c-ci-shard-e2e p-zod-advisory f-a main master release/1.2 dependabot/npm_and_yarn/vite claude/f-x worktree-abc; do
    guard_on_branch "$b"; assert_status "$RC" 0 "allowed [$b]"; assert_eq "$OUT" "" "silent on [$b]"
  done
}
t_guard_blocks_names() {
  local b
  for b in badname feature/x F-Upper f- f-a--b x-thing fix/null-check f-has_underscore f-Mixed; do
    guard_on_branch "$b"; assert_status "$RC" 2 "blocked [$b]"; assert_contains "$OUT" "naming rule" "message on [$b]"
  done
}
t_guard_skip_and_other_commands() {
  guard_on_branch badname "BRANCH_NAME_SKIP=1 gh pr create --body-file body.md"; assert_status "$RC" 0 "inline skip"
  BRANCH_NAME_SKIP=1 guard_on_branch badname; assert_status "$RC" 0 "env skip"
  guard_on_branch badname "git status"; assert_status "$RC" 0 "other commands untouched"
  guard_on_branch f-ok "gh pr create --title t"; assert_status "$RC" 2 "still needs --body-file"
}
case_ "guard-pr-create: allows <f|b|d|c|p>-slug and the exempt names" t_guard_allows_names
case_ "guard-pr-create: blocks names outside the form, with the rule in the message" t_guard_blocks_names
case_ "guard-pr-create: BRANCH_NAME_SKIP, other commands, and the body-file rule still hold" t_guard_skip_and_other_commands

finish
