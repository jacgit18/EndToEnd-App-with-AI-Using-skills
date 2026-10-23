#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) — enforces the global rule "never hand-write a PR description".
# Blocks `gh pr create` in a project that has scripts/pr-body.mjs unless the body comes from a
# file (--body-file / -F), which is how the script's output is passed. Exit 2 = block, and the
# message on stderr goes back to Claude. A git repo without the kit is blocked until pr-kit/install.sh
# is run (opt out: .no-pr-kit or PR_KIT_SKIP=1). Any other case (no jq, other command, not a git repo) exits 0.
set -u
command -v jq >/dev/null 2>&1 || exit 0
payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)"
# Only a real command: at the start of the line or after ; & | ( (not the words inside a heredoc or a quoted note).
printf '%s\n' "$cmd" | grep -Eq '(^|[;&|(])[[:space:]]*(cd [^;&|]*(&&|;)[[:space:]]*)?gh pr create' || exit 0
dir="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$dir" ] || dir="${CLAUDE_PROJECT_DIR:-$PWD}"
# Branch naming (rules/branch-naming.md): <f|b|d|c|p>-<slug>. Exempt: main/master, release/*, dependabot/*, claude/*, worktree-*.
if [ -z "${BRANCH_NAME_SKIP:-}" ] && ! printf '%s' "$cmd" | grep -q 'BRANCH_NAME_SKIP=1'; then
  branch="$(git -C "$dir" branch --show-current 2>/dev/null)"
  if [ -n "$branch" ] && ! printf '%s' "$branch" | grep -Eq '^([fbdcp]-[a-z0-9]+(-[a-z0-9]+)*|main|master|release/.*|dependabot/.*|claude/.*|worktree-.*)$'; then
    echo "Blocked: branch '$branch' does not follow the naming rule. Use <letter>-<slug> (f feature, b bug, d docs, c chore, p dependencies), e.g. f-rest-day-timer: rename with 'git branch -m <new-name>', or prefix the command with BRANCH_NAME_SKIP=1. Rule: /home/jac/.claude/rules/branch-naming.md" >&2
    exit 2
  fi
fi
if [ ! -f "$dir/scripts/pr-body.mjs" ]; then
  # No PR kit yet: block until it is installed. Opt out with a .no-pr-kit file in the repo or PR_KIT_SKIP=1.
  [ -n "${PR_KIT_SKIP:-}" ] && exit 0
  printf '%s' "$cmd" | grep -q 'PR_KIT_SKIP=1' && exit 0
  top="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
  [ -f "$top/.no-pr-kit" ] && exit 0
  echo "Blocked: this project has no PR kit. Run /home/jac/Pictures/EndToEnd-App-with-AI-Using-skills/.claude/skills/commit-and-push/pr-kit/install.sh \"$top\", adapt scripts/pr-body.mjs, commit it, then build the body with it. Not your repo? touch .no-pr-kit (or prefix the command with PR_KIT_SKIP=1)." >&2
  exit 2
fi
case "$cmd" in *"--body-file"*|*" -F "*|*"--fill"*) ;; *)
  echo "Blocked: this project builds PR descriptions with scripts/pr-body.mjs. Run: node scripts/pr-body.mjs --what \"...\" > body.md, then gh pr create --body-file body.md (keep the attribution line at the end)." >&2
  exit 2 ;;
esac
exit 0
