#!/usr/bin/env bash
# Owner-run, once per project; safe to run again (resumes from .env.deploy). Creates the Google Cloud project, links billing, sets the gcloud configuration, writes .env.deploy, creates the monthly budget.
#   scripts/cloud-new-project.sh --dry-run    print the steps; makes no gcloud call
#   scripts/cloud-new-project.sh              do it
# Sign-in (gcloud auth login) stays manual. Nothing is trusted until read back with a read-only command. A budget is an alert, not a cap.
set -euo pipefail
KIT_NAME=cloud-new-project
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud-lib.sh"
load_conf
[[ "${1:-}" == "--dry-run" ]] && DRY=1
BUDGET_NAME="${APP_SLUG}-${BUDGET_USD}"

if ((DRY)); then
  echo "DRY RUN: nothing below is executed, and no gcloud call is made."
  say "1. gcloud configuration '$APP_SLUG'"
  note "would create it if missing, activate it, and stop with 'gcloud auth login' if no account is signed in"
  say "2. Google Cloud project (name '$DISPLAY_NAME')"
  note "would run: gcloud projects create <id: $APP_SLUG, or $APP_SLUG plus four random digits if the id is taken, at most 3 retries> --name=\"$DISPLAY_NAME\""
  say "3. Billing"
  note "would take the open account from: gcloud billing accounts list (one: use it; several: ask; none: stop), then: gcloud billing projects link <id> --billing-account=<open billing account>"
  say "4. Read back, then write .env.deploy"
  note "would read: gcloud projects list (the id must appear) and gcloud billing projects describe <id> (billing enabled)"
  note "only then: gcloud config set project <id>, gcloud config set run/region $REGION, and write GCP_PROJECT_ID and GCP_REGION to .env.deploy"
  say "5. Monthly budget $BUDGET_USD USD ('$BUDGET_NAME') for this one project, alerts at 50, 90 and 100 percent"
  note "would ask once before enabling billingbudgets.googleapis.com, then: gcloud billing budgets create --billing-account=<open billing account> --display-name=$BUDGET_NAME --budget-amount=${BUDGET_USD}USD --filter-projects=projects/<id> --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0"
  note "then read it back with: gcloud billing budgets list --billing-account=<open billing account>"
  say "Dry run finished; nothing was changed."
  exit 0
fi

preflight gcloud git
[[ -n "$(git rev-parse --show-toplevel 2>/dev/null)" ]] || die "run this inside the project's git repository"

say "1. gcloud configuration '$APP_SLUG'"
if gcloud config configurations list --format='value(name)' | qgrep -x "$APP_SLUG"; then
  gcloud config configurations activate "$APP_SLUG"
else
  gcloud config configurations create "$APP_SLUG"
fi
active_cfg="$(gcloud config configurations list --filter=is_active:true --format='value(name)')"
[[ "$active_cfg" == "$APP_SLUG" ]] || die "the active gcloud configuration is '$active_cfg', not '$APP_SLUG'"
[[ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" ]] || die "no account is signed in. Run: gcloud auth login   (then run this script again)"

PROJECT="$(env_deploy_get GCP_PROJECT_ID)"
if [[ -n "$PROJECT" ]]; then
  say "2-4. .env.deploy already names a project; resuming with it"
  gcloud projects list --filter="projectId=$PROJECT" --format='value(projectId)' | qgrep -x "$PROJECT" || die "$PROJECT in .env.deploy is not in 'gcloud projects list' for this account"
else
  say "2. Billing account (looked up first, so a stop here leaves no project behind)"
  mapfile -t accts < <(gcloud billing accounts list --filter=open=true --format='value(name)')
  ((${#accts[@]} > 0)) || die "no open billing account; create one in the console first (billing is the owner's step)"
  acct="${accts[0]##*/}"
  if ((${#accts[@]} > 1)); then
    printf '   open billing accounts:\n'; printf '     %s\n' "${accts[@]##*/}"
    read -rp "Which billing account id to link? " acct
    printf '%s\n' "${accts[@]##*/}" | qgrep -xF "$acct" || die "$acct is not one of the open accounts"
  fi

  say "3. Google Cloud project"
  [[ ${#APP_SLUG} -ge 6 ]] || die "APP_SLUG must be at least 6 characters to be a project id"
  id="$APP_SLUG"; tries=0
  while :; do
    if out="$(gcloud projects create "$id" --name="$DISPLAY_NAME" 2>&1)"; then break; fi
    if [[ "$out" == *"already in use"* ]] && ((tries < 3)); then
      tries=$((tries + 1)); id="${APP_SLUG}$(printf '%04d' $((RANDOM % 10000)))"; note "id taken; trying $id"
    else
      echo "$out" >&2; die "could not create the project"
    fi
  done
  PROJECT="$id"

  say "3b. Link billing"
  gcloud billing projects link "$PROJECT" --billing-account="$acct"

  say "4. Read back, then write .env.deploy"
  gcloud projects list --filter="projectId=$PROJECT" --format='value(projectId)' | qgrep -x "$PROJECT" || die "$PROJECT does not appear in 'gcloud projects list'; nothing written"
  [[ "$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)' | tr 'A-Z' 'a-z')" == true ]] || die "billing is not enabled on $PROJECT; nothing written"
  gcloud config set project "$PROJECT"
  gcloud config set run/region "$REGION"
  { printf 'GCP_PROJECT_ID=%s\n' "$PROJECT"; printf 'GCP_REGION=%s\n' "$REGION"; } >> .env.deploy
  note "wrote .env.deploy (git-ignored by the installer; check: git check-ignore .env.deploy)"
fi

say "5. Monthly budget $BUDGET_USD USD"
bill_acct="$(gcloud billing projects describe "$PROJECT" --format='value(billingAccountName)')"; bill_acct="${bill_acct##*/}"
[[ -n "$bill_acct" ]] || die "could not read the billing account of $PROJECT"
if gcloud billing budgets list --billing-account="$bill_acct" --format='value(displayName)' | qgrep -xF "$BUDGET_NAME"; then
  note "budget '$BUDGET_NAME' exists already"
else
  read -rp "Enable the Cloud Billing Budget API on $PROJECT (needed for budgets)? [y/N] " yn
  [[ "$yn" == y || "$yn" == Y ]] || die "budget not created (API not enabled). Run again when ready."
  gcloud services enable billingbudgets.googleapis.com --project "$PROJECT"
  gcloud billing budgets create --billing-account="$bill_acct" --display-name="$BUDGET_NAME" --budget-amount="${BUDGET_USD}USD" \
    --filter-projects="projects/$PROJECT" --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
fi

bash "$KIT_DIR/cloud-verify.sh" project
cat <<MSG

Done. Reminders (the kit cannot do these):
- Neon: when its permission page asks, choose the project-limited option, not "all projects".
- Neon two-factor: the CLI cannot check it; confirm it in the Neon account settings (not checked by the kit).
- A budget is an alert, not a cap: it does not stop spending.
Next: scripts/cloud-new-database.sh qa --dry-run
MSG
