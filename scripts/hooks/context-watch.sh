#!/usr/bin/env bash
# UserPromptSubmit hook — arm a session handoff once context crosses a ratio of
#   the model's context window.
#
# Reads the conversation transcript (path handed in on stdin), estimates how many
# tokens the last assistant turn carried, and — the first time that estimate
# reaches HANDOFF_RATIO * CONTEXT_LIMIT — prints an instruction block. On a
# UserPromptSubmit hook that stdout is added to the turn's context, so Claude
# sees it and runs the `session-handoff` skill before doing anything else.
#
# Defensive by design, like log-skill.sh / log-prompt.sh: needs jq, always exits
# 0, never blocks the prompt, only touches its own flag file. Fires at most once
# per session (delete the flag to re-arm).
#
# Tunables (export in the shell, or add an "env" block to .claude/settings.json):
#   CONTEXT_LIMIT   full context window in tokens   (default 200000;
#                   set 1000000 on the 1M-context beta, or ~140000 to track the
#                   figure the CLI shows, which counts down to auto-compact)
#   HANDOFF_RATIO   fraction of that to fire at      (default 0.60)
set -u

command -v jq >/dev/null 2>&1 || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude/_Prompts/logs"   # already gitignored

limit="${CONTEXT_LIMIT:-200000}"
ratio="${HANDOFF_RATIO:-0.60}"

payload="$(cat)"
[ -n "$payload" ] || exit 0

transcript="$(printf '%s' "$payload" | jq -r '.transcript_path // empty' 2>/dev/null)"
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0

sid="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)"
sid_short="${sid:0:8}"
[ -n "$sid_short" ] || sid_short="????????"

# Tokens live on each assistant line's .message.usage. Stream the file (no -s so a
# long transcript isn't slurped whole), emit one running-total per assistant turn,
# keep the last — that's the current context size.
used="$(jq -r 'select(.type=="assistant") | .message.usage
        | ((.input_tokens // 0)
           + (.cache_read_input_tokens // 0)
           + (.cache_creation_input_tokens // 0))' \
        "$transcript" 2>/dev/null | tail -n1)"

case "$used" in
  ''|*[!0-9]*) exit 0 ;;
esac

threshold="$(awk -v l="$limit" -v r="$ratio" 'BEGIN{printf "%d", l * r}')"
[ "$threshold" -gt 0 ] 2>/dev/null || exit 0
[ "$used" -ge "$threshold" ] || exit 0

mkdir -p "$STATE_DIR" 2>/dev/null || exit 0
flag="$STATE_DIR/.handoff-armed-${sid_short}"
[ -f "$flag" ] && exit 0
: > "$flag" 2>/dev/null || true

pct="$(awk -v u="$used" -v l="$limit" 'BEGIN{printf "%d", (u * 100) / l}')"
stamp="$(date +%Y-%m-%d)"

cat <<EOF
[context-watch] Estimated context ~${used}/${limit} tokens (~${pct}%), at or past the ${ratio} handoff threshold.
Before responding to this prompt, run the \`session-handoff\` skill:
  - write the handoff to .claude/handoffs/handoff-<short-task-name>-${stamp}.md
  - present it to the user
  - tell them to run  scripts/session/resume.sh  in a new terminal to continue in a fresh session
Then address the user's prompt as normal. (This fires once per session.)
EOF
exit 0
