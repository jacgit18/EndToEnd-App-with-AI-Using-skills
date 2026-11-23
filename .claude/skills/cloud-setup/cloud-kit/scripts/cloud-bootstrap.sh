#!/usr/bin/env bash
# Owner-run, safe to run again. Creates the Google Cloud resources and the database role/mark for one environment.
#   scripts/cloud-bootstrap.sh <qa|prod> --dry-run    print every command and SQL statement; makes no gcloud, docker or network call
#   scripts/cloud-bootstrap.sh <qa|prod>              do it. Prompts (hidden) for the direct owner database URL from the Neon console
#                                                     (or paste it from the clipboard hand-off of cloud-new-database.sh).
# Reads GCP_PROJECT_ID (and optionally GCP_REGION) from the git-ignored .env.deploy; names come from scripts/cloud-kit.conf.
# Secret values never appear in argv, output or shell history: hidden prompts, stdin and environment variables only. An agent does not run this script.
set -euo pipefail
KIT_NAME=cloud-bootstrap
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud-lib.sh"
load_conf
set_env "${1:-}"
[[ "${2:-}" == "--dry-run" ]] && DRY=1

PROJECT="<GCP_PROJECT_ID>"
if [[ -f .env.deploy ]]; then
  PROJECT="$(env_deploy_get GCP_PROJECT_ID)"; PROJECT="${PROJECT:-<GCP_PROJECT_ID>}"
  r="$(env_deploy_get GCP_REGION)"; REGION="${r:-$REGION}"
fi
SA_EMAIL="${SA}@${PROJECT}.iam.gserviceaccount.com"
REGISTRY_HOST="${REGION}-docker.pkg.dev"
PG_IMAGE="postgres:${PG_VERSION}-alpine"

# Run the owner SQL read from stdin through the postgres image's psql. The URL travels in the environment (PGURL), never in argv.
owner_sql() {
  docker run --rm -i -e PGURL "$PG_IMAGE" sh -c 'exec psql "$PGURL" -v ON_ERROR_STOP=1 -X -q -t -A'
}

if ((DRY)); then
  echo "DRY RUN for '$ENV_NAME': nothing below is executed, and no gcloud, docker or network call is made."
else
  guard_active_project
  if [[ "$ENV_NAME" == prod ]]; then
    read -rp "Type the service name ($PREFIX) to confirm: " typed
    [[ "$typed" == "$PREFIX" ]] || die "confirmation did not match; nothing done"
  fi
  preflight gcloud docker openssl node
  preflight_gh
  docker info >/dev/null 2>&1 || die "preflight: the docker server is not running"
  [[ -d node_modules ]] || note "preflight: node_modules is missing; run 'npm ci --ignore-scripts' before the first deploy (not run by this script)"
  note "preflight: the first run pulls $PG_IMAGE from Docker Hub (one-time download)"
fi

say "1. Enable the APIs"
run gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com --project "$PROJECT"

say "2. Image repository '$REPO_NAME' in $REGION (created if missing)"
if ((DRY)); then
  echo "   would run: gcloud artifacts repositories describe $REPO_NAME --location $REGION --project $PROJECT   (and create it with --repository-format=docker if that fails)"
else
  gcloud artifacts repositories describe "$REPO_NAME" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1 \
    || gcloud artifacts repositories create "$REPO_NAME" --repository-format=docker --location "$REGION" --project "$PROJECT" --description="$DISPLAY_NAME images"
fi

say "3. Service account $SA (created if missing)"
if ((DRY)); then
  echo "   would run: gcloud iam service-accounts describe $SA_EMAIL --project $PROJECT   (and create it if that fails)"
else
  gcloud iam service-accounts describe "$SA_EMAIL" --project "$PROJECT" >/dev/null 2>&1 \
    || gcloud iam service-accounts create "$SA" --display-name "$DISPLAY_NAME $ENV_NAME runtime" --project "$PROJECT"
fi

say "4. Let docker push to $REGISTRY_HOST (edits your docker config)"
run gcloud auth configure-docker "$REGISTRY_HOST" --quiet

say "5. Owner database URL -> secret $OWNER_SECRET"
if ((DRY)); then
  echo "   would prompt (hidden) for the DIRECT (non-pooled) owner URL from the Neon console and store it with: gcloud secrets create $OWNER_SECRET --data-file=- (value on stdin)"
  echo "   if the secret exists already, it is read back instead of asked again"
  OWNER_URL="<owner url>"
else
  if gcloud secrets describe "$OWNER_SECRET" --project "$PROJECT" >/dev/null 2>&1; then
    OWNER_URL="$(gcloud secrets versions access latest --secret "$OWNER_SECRET" --project "$PROJECT")"
  else
    read -rsp "Paste the DIRECT owner database URL from the Neon console (hidden): " OWNER_URL; echo
    [[ "$OWNER_URL" != *-pooler* ]] || die "That is the pooled address. Use the direct one (no '-pooler') for the owner."
    [[ "$OWNER_URL" == postgres* ]] || die "That does not look like a postgres URL."
    printf '%s' "$OWNER_URL" | gcloud secrets create "$OWNER_SECRET" --replication-policy=automatic --data-file=- --project "$PROJECT"
  fi
  export PGURL="$OWNER_URL"
fi

say "6. Database role $DB_ROLE (no bypass of row-level security) and its pooled URL -> secret $APP_SECRET"
if ((DRY)); then
  cat <<SQL
   would send to the owner database (the password is generated with openssl, 24 random bytes, and never shown):
     DO \$\$ BEGIN
       IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_ROLE}') THEN
         CREATE ROLE ${DB_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD '<generated>';
       ELSE
         ALTER ROLE ${DB_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD '<generated>';
       END IF;
       EXECUTE format('GRANT CONNECT ON DATABASE %I TO ${DB_ROLE}', current_database());
     END \$\$;
   then it reads back rolbypassrls and rolsuper for ${DB_ROLE} and stops unless both are false,
   builds the pooled URL (host gets '-pooler') in memory and stores it with: gcloud secrets create <the app-database-url secret> --data-file=- (stdin)
SQL
else
  if gcloud secrets describe "$APP_SECRET" --project "$PROJECT" >/dev/null 2>&1; then
    echo "   $APP_SECRET exists already; leaving the role and its password alone."
    echo "   (To rotate: delete nothing by hand; ask for a rotate option to be added to this script.)"
  else
    APP_PW="$(openssl rand -hex 24)"
    owner_sql <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_ROLE}') THEN
    CREATE ROLE ${DB_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD '${APP_PW}';
  ELSE
    ALTER ROLE ${DB_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD '${APP_PW}';
  END IF;
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO ${DB_ROLE}', current_database());
END \$\$;
SQL
    flags="$(owner_sql <<<"SELECT rolbypassrls::text || ',' || rolsuper::text FROM pg_roles WHERE rolname = '${DB_ROLE}';")"
    [[ "$flags" == "false,false" ]] || die "$DB_ROLE can bypass row-level security or is a superuser ($flags). Stopping; nothing stored."
    APP_URL="$(OWNER_URL="$OWNER_URL" APP_PW="$APP_PW" APP_ROLE="$DB_ROLE" node -e '
      const u = new URL(process.env.OWNER_URL);
      u.username = process.env.APP_ROLE; u.password = process.env.APP_PW;
      u.hostname = u.hostname.replace(/^(ep-[^.]*?)(-pooler)?\./, "$1-pooler.");
      process.stdout.write(u.toString());')"
    printf '%s' "$APP_URL" | gcloud secrets create "$APP_SECRET" --replication-policy=automatic --data-file=- --project "$PROJECT"
    unset APP_PW APP_URL
  fi
fi

say "7. Environment mark '$MARK' on the database"
if ((DRY)); then
  echo "   would send: DO \$\$ BEGIN EXECUTE format('COMMENT ON DATABASE %I IS %L', current_database(), '${MARK_KEY}:$MARK'); END \$\$;   and read it back"
else
  owner_sql <<SQL
DO \$\$ BEGIN EXECUTE format('COMMENT ON DATABASE %I IS %L', current_database(), '${MARK_KEY}:${MARK}'); END \$\$;
SQL
  got="$(owner_sql <<<"SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = current_database();")"
  [[ "$got" == "${MARK_KEY}:${MARK}" ]] || die "The environment mark did not read back as expected."
fi

say "8. Let $SA read $APP_SECRET and nothing else"
run gcloud secrets add-iam-policy-binding "$APP_SECRET" --member "serviceAccount:${SA_EMAIL}" --role roles/secretmanager.secretAccessor --project "$PROJECT"

unset PGURL OWNER_URL 2>/dev/null || true
if ((DRY)); then
  say "Dry run finished; nothing was changed."
else
  clipboard_clear 2>/dev/null || true
  bash "$KIT_DIR/cloud-verify.sh" "$ENV_NAME"
  say "Done. Next: npm run deploy:$ENV_NAME"
fi
