#!/usr/bin/env bash
# Install the PR kit into a project: template, two CI checks, pr-body script, its test, the dependency scan (dependency-security.md), the CI timeout check (ci-budget.md), and the CLAUDE.md rule.
# Usage: install.sh [project-dir] [--force]   (default: current directory; existing files are kept unless --force)
set -eu
kit="$(cd "$(dirname "$0")" && pwd)"
dir="."; force=0
for a in "$@"; do case "$a" in --force) force=1 ;; *) dir="$a" ;; esac; done
cd "$dir"
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "not a git repository: $PWD" >&2; exit 1; }
root="$(git rev-parse --show-toplevel)"; cd "$root"
put() { # src dest
  if [ -e "$2" ] && [ "$force" = 0 ]; then echo "kept     $2 (exists; --force to replace)"; return; fi
  mkdir -p "$(dirname "$2")"; cp "$kit/$1" "$2"; echo "wrote    $2"
}
put pull_request_template.md .github/pull_request_template.md
put pr-audience.yml .github/workflows/pr-audience.yml
put pr-changelog.yml .github/workflows/pr-changelog.yml
put pr-body.mjs scripts/pr-body.mjs
put pr-kit.json .github/pr-kit.json
put dependency-scan.yml .github/workflows/dependency-scan.yml
put dependabot.yml .github/dependabot.yml
put dep-vet.mjs scripts/dep-vet.mjs
put ci-timeouts.yml .github/workflows/ci-timeouts.yml
put ci-timeouts.mjs scripts/ci-timeouts.mjs
put claude-review.yml .github/workflows/claude-review.yml
put review-model.mjs scripts/review-model.mjs
if [ -f package.json ] && grep -q '"vitest"' package.json; then put prBody.test.js scripts/prBody.test.js; put depVet.test.js scripts/depVet.test.js; put ciTimeouts.test.js scripts/ciTimeouts.test.js; put reviewModel.test.js scripts/reviewModel.test.js
else echo "skipped  scripts/prBody.test.js, scripts/depVet.test.js, scripts/ciTimeouts.test.js, scripts/reviewModel.test.js (no vitest in package.json)"; fi
if [ -f package.json ] && grep -q '"vitest"' package.json && [ -f scripts/prBody.test.js ]; then
  echo "smoke    running the kit tests against this project's config and template"
  npx --no-install vitest run scripts/prBody.test.js scripts/depVet.test.js scripts/ciTimeouts.test.js scripts/reviewModel.test.js || echo "WARNING: kit tests fail here: fix pr-kit.json or the template before the first PR" >&2
fi
rule='Pull requests: never write the description by hand. Run `node scripts/pr-body.mjs --what "<what and why>" > body.md`, then `gh pr create --body-file body.md`.'
if [ -f CLAUDE.md ]; then
  if grep -q 'scripts/pr-body.mjs' CLAUDE.md; then echo "kept     CLAUDE.md (rule already there)"
  else printf '\n- %s\n' "$rule" >> CLAUDE.md; echo "appended CLAUDE.md rule"; fi
else echo "no CLAUDE.md: add this line to the project's instructions: $rule"; fi
node scripts/ci-timeouts.mjs || echo "WARNING: some jobs have no timeout-minutes (ci-budget.md): add one to each, about 2x its measured runtime, before the first PR" >&2
cat <<MSG

Done: the script and CI checks are identical in every project. Per project, edit only these two files:
- .github/pr-kit.json: "audiences" (extra rules such as admin only or paid, each with a label, a changed file or a line added to a file's diff), and optionally "notUserFacing", "ui", "autoTickWhenNoUi" (see DEFAULTS at the top of scripts/pr-body.mjs).
- .github/pull_request_template.md: one Audience box per audience label, and this project's own Checks lines.
Also per project: add the CLAUDE_CODE_OAUTH_TOKEN repository secret (run `claude setup-token` in your own terminal, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner/repo>`; it bills your Claude subscription, not API credits; without it the automatic PR review posts "did not run" on every PR; model rule pr-review-bot.md, per-project settings under "review" in .github/pr-kit.json), and a CI budget (PR wall-clock, runner minutes per PR, baseline from real runs) in its CLAUDE.md and CI-BUDGET.md (ci-budget.md), and the PR template's CI minutes line.
scripts/prBody.test.js checks that every audience in the config has exactly one box in the template.
MSG
