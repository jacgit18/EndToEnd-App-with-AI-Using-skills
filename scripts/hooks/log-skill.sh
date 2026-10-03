#!/usr/bin/env bash
# PreToolUse hook (matcher: Skill) — appends one line per skill invocation to
#   .claude/_Prompts/logs/YYYY-MM-DD-skills.md
# Defensive by design, like log-prompt.sh: needs jq, prints nothing, always
# exits 0, never blocks the tool call, only touches its own log file.
#
# Global mode (SKILL_LOG_GLOBAL=1, set by the user-level hook in ~/.claude/settings.json):
#   - defers to the project's own scripts/hooks/log-skill.sh when it has one, so a
#     project that wires this hook itself is not logged twice;
#   - writes to SKILL_LOG_DIR (this repo's gitignored log dir) instead of the current
#     project's, so no other repo gets a stray log folder;
#   - tags each line [project: <dir name>] and leaves out the skill's args, which in
#     another project may hold private text.
set -u

command -v jq >/dev/null 2>&1 || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="$PROJECT_DIR/.claude/_Prompts/logs"
project_tag=""
if [ "${SKILL_LOG_GLOBAL:-}" = "1" ]; then
  [ -x "$PROJECT_DIR/scripts/hooks/log-skill.sh" ] && exit 0
  [ -n "${SKILL_LOG_DIR:-}" ] || exit 0
  LOG_DIR="$SKILL_LOG_DIR"
  project_tag="$(basename "$PROJECT_DIR" | tr -d '`[]\n')"
  [ -n "$project_tag" ] || project_tag="unknown"
fi

payload="$(cat)"
[ -n "$payload" ] || exit 0

tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
[ "$tool" = "Skill" ] || exit 0

skill="$(printf '%s' "$payload" | jq -r '.tool_input.skill // empty' 2>/dev/null)"
[ -n "$skill" ] || exit 0

# Strip newlines and backticks so one event is always one clean line whose only
# backtick-quoted token is the skill name (the report recipes rely on that).
args="$(printf '%s' "$payload" | jq -r '.tool_input.args // "" | tostring' 2>/dev/null | tr '\n`' '  ' | sed -e 's/  */ /g' -e 's/^ //' -e 's/ $//')"
[ -n "$project_tag" ] && args=""
sid="$(printf '%s' "$payload" | jq -r '.session_id // "" ' 2>/dev/null)"
sid_short="${sid:0:8}"
[ -n "$sid_short" ] || sid_short="????????"

mkdir -p "$LOG_DIR" 2>/dev/null || exit 0

date_stamp="$(date +%Y-%m-%d)"
time_stamp="$(date +%H:%M:%S)"
log_file="$LOG_DIR/${date_stamp}-skills.md"

if [ ! -f "$log_file" ]; then
  printf '# Skill usage log — %s\n\n' "$date_stamp" >> "$log_file" 2>/dev/null || exit 0
fi

ptag=""
[ -n "$project_tag" ] && ptag="  [project: $project_tag]"

if [ -n "$args" ] && [ "$args" != " " ]; then
  printf -- '- %s  `%s`  (session %s)%s  args: %s\n' \
    "$time_stamp" "$skill" "$sid_short" "$ptag" "$args" >> "$log_file" 2>/dev/null || exit 0
else
  printf -- '- %s  `%s`  (session %s)%s\n' \
    "$time_stamp" "$skill" "$sid_short" "$ptag" >> "$log_file" 2>/dev/null || exit 0
fi

exit 0
