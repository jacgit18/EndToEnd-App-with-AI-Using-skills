#!/usr/bin/env bash
# Is the running prod backend the code in THIS checkout, with the config prod needs?
#
#   scripts/prod-verify.sh                 read-only: config, code, health, auth
#   scripts/prod-verify.sh --rate-limit    also send 11 bad logins with rotating X-Forwarded-For
#                                          (expects a 429; locks YOUR login for the limiter
#                                          window, ~15 min, so use it once after a deploy)
#   PROD_URL=http://localhost:8080 scripts/prod-verify.sh     check without the tunnel
#
# Why it exists: on 2026-10-11 `scripts/prod.sh up -d --build | tail` looked successful, but the
# image build had failed (DNS), so the old container kept running with the new env and the
# old code. Nothing noticed until a manual diff. Exit 0 only if every check passes; run it
# after every backend deploy and read the output, do not pipe the build through `tail`.
set -uo pipefail
cd "$(dirname "$0")/.."

URL="${PROD_URL:-https://findash.us.ci}"
fail=0
ok()  { echo "ok    $*"; }
bad() { echo "FAIL  $*"; fail=1; }

# 1. Config: uvicorn must trust only private proxy ranges, never "*" (a visitor-controlled
#    X-Forwarded-For would give every login attempt its own rate-limit bucket).
ips=$(scripts/prod.sh exec -T backend printenv FORWARDED_ALLOW_IPS 2>/dev/null | tr -d '\r')
if [ -z "$ips" ] || [ "$ips" = "*" ]; then
  bad "FORWARDED_ALLOW_IPS is '${ips:-unset}' (want the private ranges, not *)"
else
  ok "FORWARDED_ALLOW_IPS=$ips"
fi

# 2. Code: every .py under app/ in the container must match backend/app in this checkout.
sums() { find . -name '*.py' -not -path '*/__pycache__/*' | LC_ALL=C sort | xargs sha256sum; }  # C locale: host and container otherwise order _x.py differently
remote=$(scripts/prod.sh exec -T backend sh -c "cd app && $(declare -f sums); sums" 2>/dev/null)
local_sums=$(cd backend/app && sums)
if [ -z "$remote" ]; then
  bad "could not read app code from the backend container (is it running?)"
elif [ "$remote" = "$local_sums" ]; then
  ok "container code matches backend/app ($(echo "$local_sums" | wc -l) files)"
else
  bad "container code differs from backend/app (rebuild needed, or the checkout is not what was deployed):"
  diff <(echo "$remote") <(echo "$local_sums") | grep '^[<>]' | awk '{print "        " $1, $3}' | sort -k2 -u
fi

# 3. Alive and gated.
health=$(curl -fsS --max-time 10 "$URL/health" 2>/dev/null)
case "$health" in
  *'"status":"ok"'*'"db":"connected"'*) ok "GET /health -> $health" ;;
  *) bad "GET /health -> '${health:-no response}'" ;;
esac
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL/api/budgets")
[ "$code" = "401" ] && ok "unauthenticated GET /api/budgets -> 401" || bad "unauthenticated GET /api/budgets -> $code (want 401)"

# 4. Optional live proof of the rate limit.
if [ "${1:-}" = "--rate-limit" ]; then
  last=""
  for i in $(seq 1 11); do
    last=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "$URL/api/auth/login" \
      -H 'Content-Type: application/json' -H "X-Forwarded-For: 203.0.113.$i" \
      -d '{"email":"nobody@example.com","password":"wrong"}')
  done
  [ "$last" = "429" ] && ok "11th login with rotating X-Forwarded-For -> 429" \
    || bad "11th login with rotating X-Forwarded-For -> $last (want 429: the limiter can be bypassed)"
fi

[ "$fail" = 0 ] && echo "prod-verify: all checks passed" || echo "prod-verify: FAILED"
exit "$fail"
