#!/usr/bin/env bash
# Install the cloud kit into a project: the cloud scripts, their config and tests, two .gitignore lines, and the CLAUDE.md rule.
# Usage: install.sh [project-dir] [--force]   (default: current directory; existing files are kept unless --force; the project's own cloud-kit.conf is never replaced without --force)
# The kit repo is the source of truth: fix the kit first, then refresh a project with --force (then re-apply the project's cloud-kit.conf values from git).
set -eu
kit="$(cd "$(dirname "$0")" && pwd)"
dir="."; force=0
while [ $# -gt 0 ]; do case "$1" in --force) force=1 ;; *) dir="$1" ;; esac; shift; done
cd "$dir"
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "not a git repository: $PWD" >&2; exit 1; }
root="$(git rev-parse --show-toplevel)"; cd "$root"
put() { # src dest
  if [ -e "$2" ] && [ "$force" = 0 ]; then echo "kept     $2 (exists; --force to replace)"; return; fi
  mkdir -p "$(dirname "$2")"; cp "$kit/$1" "$2"; echo "wrote    $2"
}
for f in cloud-lib.sh cloud-kit.conf cloud-new-project.sh cloud-new-database.sh cloud-bootstrap.sh cloud-verify.sh; do put "scripts/$f" "scripts/$f"; done
put scripts/cloud-kit-test/run.sh scripts/cloud-kit-test/run.sh
for f in "$kit"/scripts/cloud-kit-test/fakes/*; do put "scripts/cloud-kit-test/fakes/$(basename "$f")" "scripts/cloud-kit-test/fakes/$(basename "$f")"; done
for f in "$kit"/scripts/cloud-kit-test/fixtures/*; do put "scripts/cloud-kit-test/fixtures/$(basename "$f")" "scripts/cloud-kit-test/fixtures/$(basename "$f")"; done
for l in .env.deploy .neon; do
  if [ -f .gitignore ] && grep -qxF "$l" .gitignore; then echo "kept     .gitignore ($l already there)"
  else { [ -s .gitignore ] && [ -n "$(tail -c1 .gitignore)" ] && echo; printf '%s\n' "$l"; } >> .gitignore; echo "appended .gitignore: $l"; fi
done
for f in scripts/cloud-*.sh scripts/cloud-kit-test/run.sh; do bash -n "$f" || { echo "WARNING: $f has a syntax error" >&2; }; done
rule='Cloud steps (Google Cloud, Neon, secrets) are the owner'"'"'s: run `scripts/cloud-*.sh <args> --dry-run` first; an agent never runs a cloud command. Settings live in `scripts/cloud-kit.conf` (cloud-kit).'
if [ -f CLAUDE.md ]; then
  if grep -q 'cloud-kit' CLAUDE.md; then echo "kept     CLAUDE.md (rule already there)"
  else printf '\n- %s\n' "$rule" >> CLAUDE.md; echo "appended CLAUDE.md rule"; fi
else echo "no CLAUDE.md: add this line to the project's instructions: $rule"; fi
cat <<'MSG'

Done. Per project, edit only scripts/cloud-kit.conf (every value, then KIT_CONFIGURED=yes). Then, in your own terminal (an agent never runs these):
  1. gcloud auth login          (and: neon auth)           manual sign-ins
  2. scripts/cloud-new-project.sh --dry-run   then without --dry-run
  3. scripts/cloud-new-database.sh qa --dry-run   then without
  4. scripts/cloud-bootstrap.sh qa --dry-run      then without
  5. scripts/cloud-verify.sh qa
Test the kit without any cloud: scripts/cloud-kit-test/run.sh. See the kit README for what each script does and where the kit stops.
MSG
