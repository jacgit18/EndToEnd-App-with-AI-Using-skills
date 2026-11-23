#!/usr/bin/env bash
# Owner-run. Creates the Neon project for one environment and puts its DIRECT connection string on the clipboard for cloud-bootstrap.sh's hidden prompt.
#   scripts/cloud-new-database.sh <qa|prod> --dry-run    print the steps; makes no neon or gcloud call
#   scripts/cloud-new-database.sh <qa|prod>              do it (sign in first: neon auth)
# neon writes a .neon file into its working folder, so every neon call runs in a temporary folder outside the repo.
# The connection string goes through a pipe into the clipboard tool only: never argv, never the screen, never a file.
set -euo pipefail
KIT_NAME=cloud-new-database
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud-lib.sh"
dry_arg 2 "$@"
load_conf
validate_env_deploy
set_env "${1:-}"
ENV_VAR="NEON_PROJECT_ID_$(printf '%s' "$ENV_NAME" | tr 'a-z' 'A-Z')"

if ((DRY)); then
  echo "DRY RUN for '$ENV_NAME': nothing below is executed, and no neon or gcloud call is made."
  say "1. Neon project $PREFIX"
  note "would run (in a temporary folder outside the repo): neon projects create --name $PREFIX --region-id $NEON_REGION --pg-version $PG_VERSION --no-secrets"
  note "then read the project id with: neon projects list -o json, and add $ENV_VAR to .env.deploy"
  say "2. Clipboard hand-off"
  note "would run: neon connection-string --project-id <id> --role-name neondb_owner --database-name neondb | tr -d '\\n' into the clipboard (xclip or wl-copy; if neither is installed you paste by hand into the hidden prompt)"
  note "the string is checked for a postgres prefix, no '-pooler' and its length, and is never printed"
  say "Dry run finished; nothing was changed."
  exit 0
fi

preflight gcloud neon node
PROJECT="$(env_deploy_get GCP_PROJECT_ID)"; PROJECT="${PROJECT:-<GCP_PROJECT_ID>}"
guard_active_project

neon_out() { local t rc=0; t="$(mktemp -d)"; ( cd "$t" && neon "$@" ) || rc=$?; rm -rf "$t"; return $rc; }
neon_find_id() { # prints the id of the project named $PREFIX, or nothing
  neon_out projects list -o json | PROJ_NAME="$PREFIX" node -e '
    let s="";process.stdin.on("data",c=>s+=c).on("end",()=>{const d=JSON.parse(s);const a=Array.isArray(d)?d:(d.projects||[]);
    const p=a.find(x=>x.name===process.env.PROJ_NAME);process.stdout.write(p?String(p.id):"")})'
}

say "1. Neon project $PREFIX"
id="$(neon_find_id)"
if [[ -n "$id" ]]; then
  note "a Neon project named $PREFIX exists already; using it"
else
  neon_out projects create --name "$PREFIX" --region-id "$NEON_REGION" --pg-version "$PG_VERSION" --no-secrets
  id="$(neon_find_id)"
  [[ -n "$id" ]] || die "the project was created but 'neon projects list' does not show it; nothing recorded"
fi
if [[ -z "$(env_deploy_get "$ENV_VAR")" ]]; then printf '%s=%s\n' "$ENV_VAR" "$id" >> .env.deploy; note "wrote $ENV_VAR to .env.deploy"; fi

say "2. Clipboard hand-off"
cs="$(neon_out connection-string --project-id "$id" --role-name neondb_owner --database-name neondb | tr -d '\n')"
[[ "$cs" == postgres* ]] || die "the connection string does not start with postgres"
[[ "$cs" != *-pooler* ]] || die "the connection string is the pooled one; the owner needs the direct one"
((${#cs} >= 40)) || die "the connection string is too short"
case "$(clipboard_tool)" in
  xclip) printf '%s' "$cs" | xclip -selection clipboard; note "the direct string is on the clipboard (not printed). Paste it into cloud-bootstrap.sh's hidden prompt; the bootstrap empties the clipboard at the end." ;;
  wl-copy) printf '%s' "$cs" | wl-copy; note "the direct string is on the clipboard (not printed). Paste it into cloud-bootstrap.sh's hidden prompt; the bootstrap empties the clipboard at the end." ;;
  *) note "no clipboard tool (xclip or wl-copy) found: copy the direct connection string from the Neon console and paste it by hand into the hidden prompt." ;;
esac
unset cs
note "Next: scripts/cloud-bootstrap.sh $ENV_NAME --dry-run"
