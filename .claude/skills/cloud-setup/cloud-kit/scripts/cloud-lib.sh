#!/usr/bin/env bash
# Shared helpers for the cloud kit scripts. Sourced, never run. No cloud call is made at load time.
# An agent never runs the kit's scripts; the owner does. Secret values never go in argv, output or files: hidden prompts, stdin, pipes and environment variables only.

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_CONF="${CLOUD_KIT_CONF:-$KIT_DIR/cloud-kit.conf}"
DRY=0

say() { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
die() { echo "${KIT_NAME:-cloud-kit}: $*" >&2; exit 1; }
# Run a command, or only print it in a dry run.
run() { if ((DRY)); then printf '   would run: %s\n' "$*"; else "$@"; fi; }

# Pattern check for one config value.
need_pattern() { # key value regex
  [[ "$2" =~ $3 ]] || die "cloud-kit.conf: $1 has an invalid value (must match $3)"
}

# The conf is parsed line by line, never sourced: a value is data, so "DB_ROLE=a;touch x" is rejected by its pattern, not executed.
load_conf() {
  [[ -f "$KIT_CONF" ]] || die "missing $KIT_CONF (copy the kit's scripts/cloud-kit.conf and edit it)"
  local line key val n=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    n=$((n + 1)); line="${line%$'\r'}"
    line="$(printf '%s' "$line" | sed -E 's/[[:space:]]+#.*$//; s/^[[:space:]]+//; s/[[:space:]]+$//')"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" =~ ^([A-Z_]+)=(.*)$ ]] || die "cloud-kit.conf line $n is not KEY=value"
    key="${BASH_REMATCH[1]}"; val="${BASH_REMATCH[2]}"
    case "$key" in
      KIT_CONFIGURED|APP_SLUG|REPO_NAME|DB_ROLE|MARK_KEY|LOG_NAME|REGION|NEON_REGION|PG_VERSION|BUDGET_USD|DISPLAY_NAME) printf -v "$key" '%s' "$val" ;;
      *) die "cloud-kit.conf line $n: unknown key $key" ;;
    esac
  done < "$KIT_CONF"
  local k
  for k in KIT_CONFIGURED APP_SLUG REPO_NAME DB_ROLE MARK_KEY LOG_NAME REGION NEON_REGION PG_VERSION BUDGET_USD DISPLAY_NAME; do
    [[ -n "${!k:-}" ]] || die "cloud-kit.conf: $k is not set"
  done
  need_pattern APP_SLUG "$APP_SLUG" '^[a-z][a-z0-9-]{2,23}$'
  need_pattern REPO_NAME "$REPO_NAME" '^[a-z][a-z0-9-]{1,62}$'
  need_pattern DB_ROLE "$DB_ROLE" '^[a-z][a-z0-9_]{2,40}$'
  need_pattern MARK_KEY "$MARK_KEY" '^[a-z][a-z0-9-]{1,40}$'
  need_pattern LOG_NAME "$LOG_NAME" '^[a-z][a-z0-9-]{1,62}$'
  need_pattern REGION "$REGION" '^[a-z]+-[a-z]+[0-9]+$'
  need_pattern NEON_REGION "$NEON_REGION" '^[a-z]+-[a-z]+-[a-z]+-[0-9]+$'
  need_pattern PG_VERSION "$PG_VERSION" '^[0-9]{2}$'
  need_pattern BUDGET_USD "$BUDGET_USD" '^[1-9][0-9]{0,5}$'
  need_pattern DISPLAY_NAME "$DISPLAY_NAME" '^[A-Za-z0-9][A-Za-z0-9 -]{0,39}$'
  [[ "$KIT_CONFIGURED" == yes ]] || die "cloud-kit.conf is still the template: edit the values, then set KIT_CONFIGURED=yes"
}

# <qa|prod> -> ENV_NAME, PREFIX, MARK (dies with usage on anything else)
set_env() {
  ENV_NAME="${1:-}"
  case "$ENV_NAME" in
    qa) PREFIX="${APP_SLUG}-qa"; MARK=qa ;;
    prod) PREFIX="${APP_SLUG}-prod"; MARK=production ;;
    *) echo "usage: $0 <qa|prod> [--dry-run]" >&2; exit 2 ;;
  esac
  SA="${PREFIX}-run"
  OWNER_SECRET="${PREFIX}-owner-database-url"
  APP_SECRET="${PREFIX}-app-database-url"
}

# Read GCP_PROJECT_ID / GCP_REGION / NEON_PROJECT_ID_* from the git-ignored .env.deploy (plain KEY=value, never sourced as code: parsed line by line).
env_deploy_get() { # key -> value or empty (strips CR, a leading "export ", and one pair of quotes)
  [[ -f .env.deploy ]] || return 0
  local line v
  line="$(tr -d '\r' < .env.deploy | sed -E 's/^export[[:space:]]+//' | grep -E "^$1=" | tail -1 || true)"
  v="${line#*=}"
  if [[ "$v" =~ ^\"(.*)\"$ || "$v" =~ ^\'(.*)\'$ ]]; then v="${BASH_REMATCH[1]}"; fi
  printf '%s' "$v"
}

# Refuse unless the active gcloud project is the one in .env.deploy (real runs only).
guard_active_project() {
  [[ "$PROJECT" != "<GCP_PROJECT_ID>" ]] || die "Set GCP_PROJECT_ID in .env.deploy first."
  local active
  active="$(gcloud config get-value project 2>/dev/null || true)"
  [[ "$active" == "$PROJECT" ]] || die "The active gcloud project is not the one in .env.deploy. Switch with: gcloud config configurations activate ${APP_SLUG}"
}

# Read-only preflight (real runs only). Prints one line per problem, dies if any.
preflight() { # tool...   (each tool must be on PATH)
  local bad=0 t
  for t in "$@"; do command -v "$t" >/dev/null 2>&1 || { echo "preflight: missing tool: $t" >&2; bad=1; }; done
  ((bad == 0)) || die "preflight failed; install the missing tool(s) and run again"
}

# gh must be installed and signed in (read-only). If the status shows token scopes and 'repo' is not among them, that is a problem too.
preflight_gh() {
  command -v gh >/dev/null 2>&1 || die "preflight: gh is not installed"
  local st; st="$(gh auth status 2>&1)" || die "preflight: gh is not signed in (run: gh auth login)"
  if printf '%s' "$st" | grep -q 'Token scopes'; then printf '%s' "$st" | grep 'Token scopes' | grep -q "repo" || die "preflight: the gh token has no 'repo' scope"; fi
}

# Pick a clipboard tool; prints its name or nothing. CLOUD_KIT_CLIPBOARD=none turns the clipboard hand-off off; xclip or wl-copy forces one.
clipboard_tool() {
  case "${CLOUD_KIT_CLIPBOARD:-auto}" in none) return 0 ;; xclip|wl-copy) command -v "$CLOUD_KIT_CLIPBOARD" >/dev/null 2>&1 && echo "$CLOUD_KIT_CLIPBOARD"; return 0 ;; esac
  if command -v xclip >/dev/null 2>&1; then echo xclip
  elif command -v wl-copy >/dev/null 2>&1; then echo wl-copy
  fi
}
clipboard_clear() {
  case "$(clipboard_tool)" in
    xclip) printf '' | xclip -selection clipboard ;;
    wl-copy) wl-copy --clear ;;
  esac
}

# grep that reads all of its input (no early exit), so a pipeline under pipefail never fails on SIGPIPE.
qgrep() { grep "$@" >/dev/null; }
