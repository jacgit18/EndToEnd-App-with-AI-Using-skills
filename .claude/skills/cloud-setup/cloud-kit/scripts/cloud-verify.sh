#!/usr/bin/env bash
# Read-only read-back of everything the kit created. Prints "ok" or "FAILED" per line; exits 1 if any FAILED.
#   scripts/cloud-verify.sh <qa|prod|project> [--dry-run]    "project" checks only the project-level lines
# Uses read-only commands only (list, describe, get-iam-policy, git status). Secret values are never read.
set -euo pipefail
KIT_NAME=cloud-verify
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud-lib.sh"
load_conf
WHAT="${1:-}"
[[ "${2:-}" == "--dry-run" ]] && DRY=1
if [[ "$WHAT" == project ]]; then ENV_NAME=""; else set_env "$WHAT"; fi

FAILS=0
chk() { # label result(0=ok)
  if [[ "$2" == 0 ]]; then printf '   ok      %s\n' "$1"; else printf '   FAILED  %s\n' "$1"; FAILS=$((FAILS + 1)); fi
}
in_lines() { qgrep -xF "$1"; }

if ((DRY)); then
  echo "DRY RUN: nothing below is executed, and no cloud call is made."
  say "Checks this script would make (read-only)"
  for l in "project id appears in: gcloud projects list" "billing enabled: gcloud billing projects describe" "budget '${APP_SLUG}-${BUDGET_USD}' scoped to the project: gcloud billing budgets list" \
    "active gcloud configuration is '${APP_SLUG}' with the project: gcloud config configurations list"; do note "$l"; done
  if [[ -n "$WHAT" && "$WHAT" != project ]]; then
    for l in "four APIs enabled: gcloud services list --enabled" "exactly the two secrets ${APP_SECRET} and ${OWNER_SECRET}: gcloud secrets list" "policy on ${APP_SECRET} lists exactly ${SA}: gcloud secrets get-iam-policy" \
      "policy on ${OWNER_SECRET} does not list ${SA}: gcloud secrets get-iam-policy" "Neon project id from .env.deploy appears in: neon projects list"; do note "$l"; done
  fi
  note "no .neon file and no untracked file in the repo: git ls-files --others --exclude-standard"
  say "Dry run finished; nothing was changed."
  exit 0
fi

[[ -n "$WHAT" ]] || { echo "usage: $0 <qa|prod|project> [--dry-run]" >&2; exit 2; }
preflight gcloud node git
PROJECT="$(env_deploy_get GCP_PROJECT_ID)"; PROJECT="${PROJECT:-<GCP_PROJECT_ID>}"
guard_active_project
SA_EMAIL="${SA:-}@${PROJECT}.iam.gserviceaccount.com"

say "Project-level read-back"
r=1; gcloud projects list --format='value(projectId)' | in_lines "$PROJECT" && r=0; chk "project $PROJECT appears in 'gcloud projects list'" $r
r=1; [[ "$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)' | tr 'A-Z' 'a-z')" == true ]] && r=0; chk "billing is enabled" $r
bill="$(gcloud billing projects describe "$PROJECT" --format='value(billingAccountName)')"; bill="${bill##*/}"
num="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
r=1
if [[ -n "$bill" ]]; then
  gcloud billing budgets list --billing-account="$bill" --format='value(displayName,budgetFilter.projects)' \
    | awk -v n="${APP_SLUG}-${BUDGET_USD}" -v p1="projects/$PROJECT" -v p2="projects/$num" '$1==n && (index($0,p1)||index($0,p2)){f=1} END{exit !f}' && r=0
fi
chk "budget ${APP_SLUG}-${BUDGET_USD} exists and is scoped to this project" $r
r=1; [[ "$(gcloud config configurations list --filter=is_active:true --format='value(name,properties.core.project)' | tr '\t' ' ')" == "$APP_SLUG $PROJECT" ]] && r=0
chk "active gcloud configuration is $APP_SLUG with project $PROJECT" $r

if [[ "$WHAT" != project ]]; then
  say "Environment $ENV_NAME read-back"
apis="$(gcloud services list --enabled --project "$PROJECT" --format='value(config.name)')"
for a in run artifactregistry secretmanager iam; do r=1; printf '%s\n' "$apis" | in_lines "$a.googleapis.com" && r=0; chk "API $a.googleapis.com enabled" $r; done
  names="$(gcloud secrets list --project "$PROJECT" --format='value(name)' | sed 's#.*/##' | grep -E "^${PREFIX}-" | sort || true)"
  want="$(printf '%s\n%s\n' "$APP_SECRET" "$OWNER_SECRET" | sort)"
  r=1; [[ "$names" == "$want" ]] && r=0; chk "secrets for $PREFIX are exactly the expected two" $r
  members() { gcloud secrets get-iam-policy "$1" --project "$PROJECT" --format=json | node -e 'let s="";process.stdin.on("data",c=>s+=c).on("end",()=>{const d=JSON.parse(s||"{}");console.log(((d.bindings)||[]).flatMap(b=>(b.members||[]).map(m=>b.role+" "+m)).sort().join("\n"))})'; }
  r=1; [[ "$(members "$APP_SECRET")" == "roles/secretmanager.secretAccessor serviceAccount:${SA_EMAIL}" ]] && r=0; chk "policy on $APP_SECRET lists exactly $SA with secretAccessor" $r
  r=0; members "$OWNER_SECRET" | qgrep -F "$SA_EMAIL" && r=1; chk "policy on $OWNER_SECRET does not list $SA" $r
  nid="$(env_deploy_get "NEON_PROJECT_ID_$(printf '%s' "$ENV_NAME" | tr 'a-z' 'A-Z')")"
  if [[ -n "$nid" ]] && command -v neon >/dev/null 2>&1; then
    t="$(mktemp -d)"; r=1; (cd "$t" && neon projects list) | qgrep -F "$nid" && r=0; rm -rf "$t"; chk "Neon project $nid appears in 'neon projects list'" $r
  else
    printf '   skipped Neon check (no NEON_PROJECT_ID_* in .env.deploy, or neon not installed)\n'
  fi
fi

say "Repository"
r=0; [[ -e .neon ]] && r=1; chk "no .neon file in the repo folder" $r
r=1; [[ -z "$(git ls-files --others --exclude-standard)" ]] && r=0; chk "no untracked file in the repo" $r
if ((FAILS)); then echo; echo "cloud-verify: $FAILS check(s) FAILED" >&2; exit 1; fi
say "All checks ok"
