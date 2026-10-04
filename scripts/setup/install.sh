#!/usr/bin/env bash
# One-shot setup of a fresh machine from a clone of this repo: "globalize" the
# skills and plugins into ~/.claude so they work in every project.
#
#   scripts/setup/install.sh              # do it
#   scripts/setup/install.sh --dry-run    # print what would change, touch nothing
#   scripts/setup/install.sh --claude-md  # also write ~/.claude/CLAUDE.md if absent
#   DEVHIVEMIND_ROOT=/path scripts/setup/install.sh --claude-md   # journal/docs root
#
# What it does (idempotent — safe to re-run, e.g. after moving the clone):
#   1. Symlinks the 3 plugins and the personal-core skills into ~/.claude/skills.
#      Real (non-symlink) entries are never overwritten; stale symlinks are repointed.
#   2. Merges into ~/.claude/settings.json (backed up first, other keys preserved):
#      the feature-dev + linkedin-skills plugins/marketplace, and the global
#      skill-usage hook pointed at THIS clone.
#   3. With --claude-md: writes ~/.claude/CLAUDE.md from scripts/setup/global-CLAUDE.md.
# Needs: bash, git, jq. Optional: python3 (lint/profile), gh (land.sh), claude (CLI).
set -euo pipefail

DRY=0; WRITE_MD=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --claude-md) WRITE_MD=1 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLAUDE_HOME="${HOME}/.claude"
SKILLS_DIR="$CLAUDE_HOME/skills"
SETTINGS="$CLAUDE_HOME/settings.json"

PLUGINS=(architecture-skills testing-skills planning-skills)
# Keep in sync with "Personal core" in plugins/README.md.
CORE_SKILLS=(
  ambiguity-gate learning-gate problem-solving-gates entry-point-first
  explaining-my-work delete-ai-words software-carpentier-brand
  codebase-file-orientation document-page-check
  prompt-authoring prompt-tester idea-to-first-test incremental-build-pacing
  commit-and-push history-integration-strategy
  tech-decision-walkthrough system-design-communication bug-hunt-drill
  decision-journal problem-journal repo-reality-audit context-promotion
)

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then say "  [dry-run] $*"; else "$@"; fi; }

say "Repo:   $REPO"
say "Target: $CLAUDE_HOME$([ "$DRY" = 1 ] && echo '  (dry run)')"

# --- prerequisites -----------------------------------------------------------
missing=0
for t in git jq; do
  command -v "$t" >/dev/null 2>&1 || { say "MISSING required tool: $t"; missing=1; }
done
[ "$missing" = 0 ] || { say "Install the missing tools and re-run."; exit 1; }
for t in python3 gh claude; do
  command -v "$t" >/dev/null 2>&1 || say "note: optional tool not found: $t"
done

run mkdir -p "$SKILLS_DIR"

# --- 1. symlinks -------------------------------------------------------------
link() { # link <source> <name>
  local src="$1" dest="$SKILLS_DIR/$2"
  if [ ! -e "$src" ]; then say "  skip $2 (source missing: $src)"; return; fi
  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$src" ] && [ -e "$dest" ]; then say "  ok     $2"; return; fi
    say "  repoint $2"; run ln -sfn "$src" "$dest"
  elif [ -e "$dest" ]; then
    say "  KEEP   $2 (real file/dir exists, not touching it)"
  else
    say "  link   $2"; run ln -s "$src" "$dest"
  fi
}
say; say "Plugins:"
for p in "${PLUGINS[@]}"; do link "$REPO/plugins/$p" "$p"; done
say; say "Personal-core skills:"
for s in "${CORE_SKILLS[@]}"; do link "$REPO/.claude/skills/$s" "$s"; done

# --- 2. settings.json merge --------------------------------------------------
say; say "Settings ($SETTINGS):"
HOOK_CMD="SKILL_LOG_GLOBAL=1 SKILL_LOG_DIR=$REPO/.claude/_Prompts/logs $REPO/scripts/hooks/log-skill.sh"
[ -f "$SETTINGS" ] || { say "  creating empty settings.json"; [ "$DRY" = 1 ] || echo '{}' > "$SETTINGS"; }
if [ "$DRY" = 1 ] && [ ! -f "$SETTINGS" ]; then base='{}'; else base="$(cat "$SETTINGS")"; fi

merged="$(printf '%s' "$base" | jq --arg cmd "$HOOK_CMD" '
  .enabledPlugins = ((.enabledPlugins // {}) + {
    "feature-dev@claude-plugins-official": true,
    "linkedin-skills@linkedin-skills": true })
  | .extraKnownMarketplaces = ((.extraKnownMarketplaces // {}) + {
    "linkedin-skills": {"source": {"source": "git", "url": "https://github.com/jacgit18/linkedin-skills.git"}} })
  # drop any earlier copy of this hook (e.g. from a previous clone path), then add ours
  | .hooks.PreToolUse = (
      [ (.hooks.PreToolUse // [])[]
        | select(((.hooks // []) | map(.command // "") | any(test("log-skill\\.sh"))) | not) ]
      + [{"matcher": "Skill", "hooks": [{"type": "command", "command": $cmd}]}] )
')"

if [ "$(printf '%s' "$base" | jq -S .)" = "$(printf '%s' "$merged" | jq -S .)" ]; then
  say "  already up to date"
elif [ "$DRY" = 1 ]; then
  say "  [dry-run] would write merged settings:"; printf '%s\n' "$merged" | sed 's/^/    /'
else
  bak="$SETTINGS.bak.$(date +%Y%m%d-%H%M%S)"; cp "$SETTINGS" "$bak"
  printf '%s\n' "$merged" > "$SETTINGS"
  say "  merged (backup: $bak)"
fi

# --- 3. global CLAUDE.md (opt-in) --------------------------------------------
say; say "Global CLAUDE.md:"
MD="$CLAUDE_HOME/CLAUDE.md"
if [ "$WRITE_MD" = 0 ]; then
  say "  skipped (pass --claude-md to write it; set DEVHIVEMIND_ROOT first)"
elif [ -e "$MD" ]; then
  say "  KEEP   $MD exists — compare with scripts/setup/global-CLAUDE.md by hand"
else
  root="${DEVHIVEMIND_ROOT:-$HOME/DevHiveMind}"
  say "  writing $MD (DevHiveMind root: $root)"
  if [ "$DRY" = 0 ]; then
    sed "s|@DEVHIVEMIND_ROOT@|$root|g" "$REPO/scripts/setup/global-CLAUDE.md" > "$MD"
    mkdir -p "$root/AI Generated Content"
  fi
fi

say; say "Done. Restart Claude Code. Skipped by design (do by hand): docker MCP / .mcp.json,"
say "claude.ai connector auth, ~/.claude/.credentials.json, and the gitignored data (*.csv, logs)."
say "The ~/.claude/skills symlinks point INTO this clone — don't move or delete it (or re-run this)."
