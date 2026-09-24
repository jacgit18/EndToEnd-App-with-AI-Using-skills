#!/usr/bin/env bash
# Run docker compose against the PRODUCTION stack with its own env file.
#
#   scripts/prod.sh up -d --build      scripts/prod.sh logs cloudflared      scripts/prod.sh down
#
# Why a wrapper: the prod POSTGRES_PASSWORD lives in finance-dashboard/.env.prod, not in
# a file named `.env`. Compose auto-loads any `.env` in the project folder for EVERY
# stack there, so the dev stack would silently pick up the prod password (it did once:
# the dev database was initialised with it and host-side tests lost access).
set -euo pipefail
cd "$(dirname "$0")/.."
exec docker compose --env-file .env.prod -f compose.prod.yaml "$@"
