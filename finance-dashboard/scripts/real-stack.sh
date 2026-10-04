#!/usr/bin/env bash
# Throwaway production-style stack for the real-stack smoke test and Lighthouse
# (browser -> Caddy -> FastAPI -> Postgres). ADR-0023 left this as a manual gap.
#
#   scripts/real-stack.sh up      build, start, wait for /health; prints nothing secret
#   scripts/real-stack.sh down    stop and delete the stack AND its database volume
#
# Safe beside the real prod stack: own project name (finance-ci), own volume, port 8081,
# random login generated per run. The login is written to $GITHUB_ENV in CI, or to
# .real-stack.env (gitignored) locally; the Playwright config and tools/lighthouse-real.mjs
# read REAL_STACK_EMAIL / REAL_STACK_PASSWORD from it. Needs docker compose >= 2.24 and uv.
set -euo pipefail
cd "$(dirname "$0")/.."

compose() {
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ci-only-password}" \
    docker compose -p finance-ci -f compose.prod.yaml -f compose.ci.yaml "$@"
}

case "${1:-}" in
  up)
    password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
    export CI_AUTH_EMAIL="ci@example.com"
    export CI_SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    # The hash is full of "$". compose.ci.yaml reads it through ${CI_AUTH_PASSWORD_HASH}
    # (one expansion, not re-expanded), so it needs no "$$" escaping like an env_file does.
    CI_AUTH_PASSWORD_HASH="$(cd backend && PW="$password" uv run --quiet python -c \
      'import os; from argon2 import PasswordHasher; print(PasswordHasher().hash(os.environ["PW"]))')"
    export CI_AUTH_PASSWORD_HASH
    compose up -d --build --wait --wait-timeout 240
    for _ in $(seq 1 30); do
      curl -fsS http://127.0.0.1:8081/health | grep -q '"db":"connected"' && break
      sleep 2
    done
    curl -fsS http://127.0.0.1:8081/health | grep -q '"db":"connected"'
    creds="REAL_STACK_EMAIL=$CI_AUTH_EMAIL"$'\n'"REAL_STACK_PASSWORD=$password"
    if [ -n "${GITHUB_ENV:-}" ]; then
      echo "::add-mask::$password"
      printf '%s\n' "$creds" >> "$GITHUB_ENV"
    else
      printf '%s\n' "$creds" > .real-stack.env
      echo "Wrote .real-stack.env (gitignored). Load it: set -a; . ./.real-stack.env; set +a"
    fi
    echo "Real stack up at http://127.0.0.1:8081"
    ;;
  down)
    compose down -v --remove-orphans
    rm -f .real-stack.env
    ;;
  logs)
    shift
    compose logs "$@"
    ;;
  *)
    echo "usage: $0 up|down|logs" >&2
    exit 2
    ;;
esac
