#!/usr/bin/env bash
# UserPromptSubmit hook — appends every submitted prompt to
#   .claude/_Prompts/logs/YYYY-MM-DD.md
# Format (the skill-usage-log feedback recipe joins on the session id):
#   ## HH:MM:SS  ·  session <8-char id>
#   <blank>
#   <prompt text>
# Defensive by design, like log-skill.sh: needs jq, prints nothing, always
# exits 0, never blocks the prompt, only touches its own log file.
set -u

command -v jq >/dev/null 2>&1 || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="$PROJECT_DIR/.claude/_Prompts/logs"

payload="$(cat)"
[ -n "$payload" ] || exit 0

prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null)"
[ -n "$prompt" ] || exit 0

sid="$(printf '%s' "$payload" | jq -r '.session_id // ""' 2>/dev/null)"
sid_short="${sid:0:8}"
[ -n "$sid_short" ] || sid_short="????????"

mkdir -p "$LOG_DIR" 2>/dev/null || exit 0

date_stamp="$(date +%Y-%m-%d)"
time_stamp="$(date +%H:%M:%S)"
log_file="$LOG_DIR/${date_stamp}.md"

if [ ! -f "$log_file" ]; then
  printf '# Prompt log — %s\n\n' "$date_stamp" >> "$log_file" 2>/dev/null || exit 0
fi

printf '## %s  ·  session %s\n\n%s\n\n' "$time_stamp" "$sid_short" "$prompt" >> "$log_file" 2>/dev/null || exit 0

exit 0
