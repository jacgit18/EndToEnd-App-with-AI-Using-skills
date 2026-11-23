#!/usr/bin/env bash
# Tests for the cloud kit. No real cloud: fake gcloud, neon, docker, xclip and gh sit first on PATH, log their argv and print canned output.
#   scripts/cloud-kit-test/run.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
KIT="$(cd "$SCRIPTS/.." && pwd)"
CONF="$HERE/fixtures/findash.conf"
PASS=0; FAIL=0
ok() { PASS=$((PASS + 1)); printf 'PASS  %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf 'FAIL  %s\n' "$1"; [[ -n "${2:-}" ]] && printf '      %s\n' "$2"; }
t() { # name, then 0 for pass
  if [[ "$2" == 0 ]]; then ok "$1"; else bad "$1" "${3:-}"; fi
}
SENTINEL="SENTINEL_SECRET_9f3a"

# Fresh sandbox: a git repo with a git-ignored .env.deploy, empty fake log and state. Sets T, REPO, OUT, ERR.
newenv() { # [project-id | none]
  T="$(mktemp -d)"; REPO="$T/repo"; mkdir -p "$REPO"; git -C "$REPO" init -q
  printf '.env.deploy\n.neon\n' > "$REPO/.git/info/exclude"
  [[ "${1:-test-proj-1234}" == none ]] || printf 'GCP_PROJECT_ID=%s\nGCP_REGION=us-east4\n' "${1:-test-proj-1234}" > "$REPO/.env.deploy"
  export FAKE_LOG="$T/fake.log" FAKE_STATE="$T/state"; : > "$FAKE_LOG"
  export FAKE_ACTIVE_PROJECT="${1:-test-proj-1234}"; [[ "$FAKE_ACTIVE_PROJECT" == none ]] && export FAKE_ACTIVE_PROJECT=""
  export FAKE_ACTIVE_CFG=fin-dash FAKE_CFGS="default fin-dash" FAKE_ACCOUNT=me@example.com FAKE_SECRET="$SENTINEL"
  export CLOUD_KIT_CONF="$CONF" PATH="$HERE/fakes:$ORIG_PATH"
  unset FAKE_TAKEN_COUNT FAKE_NO_PROJECT_READBACK FAKE_BILLING_OPEN FAKE_SECRETS FAKE_NEON_POOLED FAKE_NEON_EXISTING FAKE_BILLING_ENABLED FAKE_APIS FAKE_BUDGET_LINE CLOUD_KIT_CLIPBOARD
  OUT="$T/out"; ERR="$T/err"
}
ORIG_PATH="$PATH"
# Run a kit script in the sandbox repo: sets RC; stdout in $OUT, stderr in $ERR. Stdin from $IN (default empty).
runk() { local s="$1"; shift; ( cd "$REPO" && printf '%b' "${IN:-}" | bash "$SCRIPTS/$s" "$@" ) > "$OUT" 2> "$ERR"; RC=$?; }
log_empty() { [[ ! -s "$FAKE_LOG" ]]; }
logs() { grep -qF -- "$1" "$FAKE_LOG"; }
leaks() { grep -qF -- "$SENTINEL" "$FAKE_LOG" "$OUT" "$ERR" "$REPO/.env.deploy" 2>/dev/null; }
good_state() { # fake cloud state that a finished fin-dash-qa setup would have
  export FAKE_PROJECTS="test-proj-1234" FAKE_SECRETS="fin-dash-qa-app-database-url fin-dash-qa-owner-database-url"
  export FAKE_BUDGET_LINE='fin-dash-5\tprojects/123456'
  export FAKE_POLICY_FIN_DASH_QA_APP_DATABASE_URL="roles/secretmanager.secretAccessor serviceAccount:fin-dash-qa-run@test-proj-1234.iam.gserviceaccount.com"
}

echo "== syntax"
for f in "$SCRIPTS"/*.sh "$HERE/run.sh" "$KIT/install.sh"; do [[ -f "$f" ]] || continue; bash -n "$f"; t "bash -n $(basename "$f")" $?; done

echo "== dry runs make no cloud call"
newenv
for c in "cloud-bootstrap.sh qa" "cloud-bootstrap.sh prod" "cloud-new-project.sh" "cloud-new-database.sh qa" "cloud-new-database.sh prod" "cloud-verify.sh qa" "cloud-verify.sh project"; do
  : > "$FAKE_LOG"; runk $c --dry-run
  [[ $RC == 0 ]] && grep -q 'Dry run finished; nothing was changed.' "$OUT" && log_empty; t "dry run: $c" $? "rc=$RC log=$(cat "$FAKE_LOG")"
done
: > "$FAKE_LOG"; rm "$REPO/.env.deploy"; runk cloud-bootstrap.sh qa --dry-run
[[ $RC == 0 ]] && grep -q '<GCP_PROJECT_ID>' "$OUT"; t "dry run without .env.deploy shows the placeholder" $?

echo "== bootstrap dry run is byte-identical to Fin-Dash's (project id test-proj-1234)"
newenv
for e in qa prod; do
  runk cloud-bootstrap.sh $e --dry-run; cmp -s "$OUT" "$HERE/fixtures/findash-bootstrap-$e.dry.txt"; t "bootstrap $e --dry-run equals the Fin-Dash golden output" $?
done

echo "== config validation"
for bad_line in "DB_ROLE=bad\"role" "DB_ROLE=a;drop table x" "DB_ROLE=Upper_case" "APP_SLUG=Fin_Dash" "BUDGET_USD=5.5" "KIT_CONFIGURED=no" "REGION=us east4"; do
  newenv; sed "s|^${bad_line%%=*}=.*|$bad_line|" "$CONF" > "$T/bad.conf"; export CLOUD_KIT_CONF="$T/bad.conf"
  runk cloud-bootstrap.sh qa --dry-run; [[ $RC != 0 ]] && log_empty; t "rejects config line: $bad_line" $? "rc=$RC"
done
newenv; export CLOUD_KIT_CONF="$KIT/scripts/cloud-kit.conf"; runk cloud-bootstrap.sh qa --dry-run
[[ $RC != 0 ]] && grep -q KIT_CONFIGURED "$ERR"; t "the shipped template config is refused until edited" $?

echo "== active project guard"
for c in "cloud-bootstrap.sh qa" "cloud-new-database.sh qa" "cloud-verify.sh qa"; do
  newenv; export FAKE_ACTIVE_PROJECT=other-proj-9; runk $c
  [[ $RC != 0 ]] && grep -q 'activate fin-dash' "$ERR" && ! logs 'services enable' && ! logs 'neon projects create'; t "refuses when the active project differs: $c" $?
done

echo "== cloud-new-project"
newenv none; export FAKE_TAKEN_COUNT=1 FAKE_CFGS="default"; IN='y\n' runk cloud-new-project.sh
ID="$(grep '^GCP_PROJECT_ID=' "$REPO/.env.deploy" 2>/dev/null | cut -d= -f2)"
[[ $RC == 0 && "$ID" =~ ^fin-dash[0-9]{4}$ ]] && logs 'projects list' && logs 'billing budgets create' && logs "--filter-projects=projects/$ID"; t "id taken once: suffix retried, read-back confirms, .env.deploy has $ID, budget created" $? "rc=$RC id=$ID $(cat "$ERR")"
logs '--billing-account=OPENACCT' && logs '--filter=open=true' && ! logs CLOSEDACCT; t "links the open billing account only" $?
logs 'config configurations create fin-dash'; t "creates the gcloud configuration when missing" $?

newenv none; export FAKE_NO_PROJECT_READBACK=1; IN='y\n' runk cloud-new-project.sh
[[ $RC != 0 && ! -f "$REPO/.env.deploy" ]] && logs 'projects create'; t "read-back finds no project: stops before writing .env.deploy" $? "rc=$RC"

newenv none; export FAKE_BILLING_OPEN=""; IN='y\n' runk cloud-new-project.sh
[[ $RC != 0 ]] && ! logs 'billing projects link' && [[ ! -f "$REPO/.env.deploy" ]]; t "no open billing account: stops, links nothing, writes nothing" $?

newenv none; export FAKE_BILLING_ENABLED=False; IN='y\n' runk cloud-new-project.sh
[[ $RC != 0 && ! -f "$REPO/.env.deploy" ]]; t "billing not enabled on read-back: stops before .env.deploy" $?

newenv none; export FAKE_ACCOUNT=""; runk cloud-new-project.sh
[[ $RC != 0 ]] && grep -q 'gcloud auth login' "$ERR" && ! logs 'projects create'; t "not signed in: stops with the sign-in command" $?

newenv none; export FAKE_TAKEN_COUNT=9; IN='y\n' runk cloud-new-project.sh
[[ $RC != 0 && ! -f "$REPO/.env.deploy" ]] && [[ "$(grep -c 'projects create' "$FAKE_LOG")" == 4 ]]; t "gives up after three suffix retries" $?

newenv none; IN='n\n' runk cloud-new-project.sh
! logs 'billing budgets create' && ! logs 'services enable billingbudgets'; t "budget API enabled only on a yes" $?

echo "== cloud-new-database"
newenv; runk cloud-new-database.sh qa
[[ $RC == 0 ]] && logs 'neon projects create --name fin-dash-qa --region-id aws-us-east-1 --pg-version 17 --no-secrets' && [[ ! -e "$REPO/.neon" ]] && grep -q '^NEON_PROJECT_ID_QA=neon-id-fin-dash-qa$' "$REPO/.env.deploy"; t "creates the project outside the repo (no .neon), records the id" $? "rc=$RC $(cat "$ERR")"
grep -q "$SENTINEL" "$FAKE_STATE/clipboard" && ! leaks; t "connection string reaches the clipboard and no log, output or argv" $?
logs '--role-name neondb_owner --database-name neondb' && ! logs '--pooled'; t "asks for the direct (non-pooled) string" $?
newenv; export CLOUD_KIT_CLIPBOARD=none; runk cloud-new-database.sh qa
[[ $RC == 0 ]] && grep -q 'paste it by hand' "$OUT" && ! logs 'xclip' && ! leaks; t "clipboard tool missing: falls back to the hidden paste" $?
newenv; export FAKE_NEON_POOLED=1; runk cloud-new-database.sh qa
[[ $RC != 0 ]] && grep -q pooled "$ERR" && [[ ! -s "$FAKE_STATE/clipboard" ]] && ! leaks; t "a pooled string is refused and never copied" $?
newenv; export FAKE_NEON_EXISTING=fin-dash-qa; runk cloud-new-database.sh qa
[[ $RC == 0 ]] && ! logs 'projects create'; t "an existing Neon project is reused, not created twice" $?

echo "== cloud-bootstrap (real run on fakes)"
newenv; IN="postgres://neondb_owner:$SENTINEL@ep-abc-123.us-east-1.aws.neon.tech/neondb\n"
mkdir -p "$FAKE_STATE"; echo "$SENTINEL" > "$FAKE_STATE/clipboard"
export FAKE_MARK_READBACK="fin-dash-env:qa"
# the verify at the end of the bootstrap needs the state a real run would leave; the fakes build most of it, the budget and API lines are canned
export FAKE_BUDGET_LINE='fin-dash-5\tprojects/123456' FAKE_PROJECTS="test-proj-1234"
runk cloud-bootstrap.sh qa
[[ $RC == 0 ]] && grep -q 'Done. Next: npm run deploy:qa' "$OUT"; t "bootstrap qa runs to the end and its closing read-back passes" $? "rc=$RC $(tail -5 "$ERR")"
! leaks; t "sentinel secret appears in no argv log, output or file" $?
logs 'secrets create fin-dash-qa-owner-database-url --replication-policy=automatic --data-file=-' && logs 'secrets create fin-dash-qa-app-database-url' ; t "both secrets are created from stdin (--data-file=-)" $?
logs 'add-iam-policy-binding fin-dash-qa-app-database-url --member serviceAccount:fin-dash-qa-run@test-proj-1234.iam.gserviceaccount.com --role roles/secretmanager.secretAccessor' && [[ "$(grep -c add-iam-policy-binding "$FAKE_LOG")" == 1 ]]; t "one per-secret grant, nothing project-wide" $?
[[ ! -s "$FAKE_STATE/clipboard" ]]; t "the clipboard is emptied at the end" $?

# mutation: a script changed to echo the secret must make the leak check fail
newenv; cp -r "$SCRIPTS" "$T/mut"; sed -i 's|^  export PGURL="\$OWNER_URL"|  echo "$OWNER_URL"; export PGURL="$OWNER_URL"|' "$T/mut/cloud-bootstrap.sh"
IN="postgres://neondb_owner:$SENTINEL@ep-abc-123.us-east-1.aws.neon.tech/neondb\n"
( cd "$REPO" && printf '%b' "$IN" | bash "$T/mut/cloud-bootstrap.sh" qa ) > "$OUT" 2> "$ERR"
leaks; t "mutation check: a bootstrap that echoes the secret is caught by the leak check" $?

newenv; IN="postgres://neondb_owner:$SENTINEL@ep-abc-123-pooler.us-east-1.aws.neon.tech/neondb\n"; runk cloud-bootstrap.sh qa
[[ $RC != 0 ]] && grep -q pooled "$ERR" && ! logs 'secrets create' && ! leaks; t "a pooled owner URL is refused before anything is stored" $?
newenv; IN="postgres://neondb_owner:$SENTINEL@ep-abc-123.us-east-1.aws.neon.tech/neondb\n"; export FAKE_ROLE_FLAGS="true,false"; runk cloud-bootstrap.sh qa
[[ $RC != 0 ]] && ! logs 'secrets create fin-dash-qa-app-database-url'; t "a role that can bypass RLS stops the script before the app secret" $?

echo "== cloud-verify"
newenv; good_state; runk cloud-verify.sh qa
[[ $RC == 0 ]] && ! grep -q FAILED "$OUT"; t "verify: all ok on a complete setup" $? "rc=$RC $(grep FAILED "$OUT")"
newenv; good_state; export FAKE_SECRETS="fin-dash-qa-app-database-url fin-dash-qa-owner-database-url fin-dash-qa-extra"; runk cloud-verify.sh qa
[[ $RC != 0 ]] && grep -q 'FAILED  secrets for fin-dash-qa' "$OUT"; t "verify: FAILED and non-zero when a secret list has an extra secret" $?
newenv; good_state; export FAKE_POLICY_FIN_DASH_QA_APP_DATABASE_URL="roles/secretmanager.secretAccessor serviceAccount:fin-dash-qa-run@test-proj-1234.iam.gserviceaccount.com\nroles/secretmanager.secretAccessor user:x@example.com"; runk cloud-verify.sh qa
[[ $RC != 0 ]] && grep -q 'FAILED  policy on fin-dash-qa-app-database-url' "$OUT"; t "verify: FAILED when the app-URL policy lists another member" $?
newenv; good_state; export FAKE_POLICY_FIN_DASH_QA_OWNER_DATABASE_URL="roles/secretmanager.secretAccessor serviceAccount:fin-dash-qa-run@test-proj-1234.iam.gserviceaccount.com"; runk cloud-verify.sh qa
[[ $RC != 0 ]] && grep -q 'FAILED  policy on fin-dash-qa-owner-database-url' "$OUT"; t "verify: FAILED when the runtime account can read the owner-URL secret" $?
newenv; good_state; export FAKE_APIS="run.googleapis.com"; runk cloud-verify.sh project
[[ $RC != 0 ]] && grep -q 'FAILED  API iam.googleapis.com' "$OUT"; t "verify: FAILED when an API is not enabled" $?
newenv; good_state; touch "$REPO/.neon" ; runk cloud-verify.sh project
[[ $RC != 0 ]] && grep -q 'FAILED  no .neon' "$OUT"; t "verify: FAILED when a .neon file is in the repo" $?
newenv; good_state; touch "$REPO/stray.txt"; runk cloud-verify.sh project
[[ $RC != 0 ]] && grep -q 'FAILED  no untracked' "$OUT"; t "verify: FAILED when an untracked file is in the repo" $?

echo "== install.sh"
if [[ -f "$KIT/install.sh" ]]; then
  T="$(mktemp -d)"; git -C "$T" init -q; printf '# Project\n' > "$T/CLAUDE.md"
  bash "$KIT/install.sh" "$T" > "$T/run1.txt" 2>&1; rc1=$?
  [[ $rc1 == 0 && -x "$T/scripts/cloud-bootstrap.sh" && -f "$T/scripts/cloud-kit.conf" && -f "$T/scripts/cloud-kit-test/run.sh" ]] \
    && grep -qxF '.env.deploy' "$T/.gitignore" && grep -qxF '.neon' "$T/.gitignore" && [[ "$(grep -c 'cloud-kit' "$T/CLAUDE.md")" == 1 ]]; t "install into an empty git repo writes files, .gitignore lines and one CLAUDE.md line" $? "rc=$rc1"
  cp "$T/CLAUDE.md" "$T/c1"; cp "$T/.gitignore" "$T/g1"; echo "# edited" >> "$T/scripts/cloud-kit.conf"
  bash "$KIT/install.sh" "$T" > "$T/run2.txt" 2>&1; rc2=$?
  cmp -s "$T/CLAUDE.md" "$T/c1" && cmp -s "$T/.gitignore" "$T/g1" && grep -q '^# edited' "$T/scripts/cloud-kit.conf" && ! grep -q '^wrote' "$T/run2.txt"; t "second run keeps everything (no rewrite, edited conf survives)" $? "rc=$rc2"
  bash "$KIT/install.sh" "$T" --force > /dev/null 2>&1; ! grep -q '^# edited' "$T/scripts/cloud-kit.conf"; t "--force replaces" $?
  N="$(mktemp -d)"; bash "$KIT/install.sh" "$N" > "$N.out" 2>&1; [[ $? != 0 ]]; t "refuses a folder that is not a git repository" $?
else
  echo "skip  install.sh not present (installed copy)"
fi

echo
echo "$PASS passed, $FAIL failed"
[[ $FAIL == 0 ]]
