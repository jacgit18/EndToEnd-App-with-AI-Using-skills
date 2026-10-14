#!/usr/bin/env bash
# Release helpers: next-version.sh (bump arithmetic, ladder check, evidence).
. "$(dirname "$0")/lib.sh"

NV="$SCRIPTS/release/next-version.sh"

tagrepo() { # tagrepo tag...  -> repo with one commit per tag, each tagged
  mkrepo_commit "$T/r" "init"; cd "$T/r"; local t
  for t in "$@"; do echo "$t" >> seed.txt; git add seed.txt; git commit -qm "c $t"; git tag "$t"; done
}

t_zero_rule() {
  tagrepo v0.3.0
  run bash "$NV" bump --level major; assert_status "$RC" 0
  assert_contains "$OUT" "next:         v0.4.0" "breaking -> minor under 0.x"
  run bash "$NV" bump --level minor; assert_contains "$OUT" "next:         v0.3.1" "additive -> patch under 0.x"
  run bash "$NV" bump --level major --to-one; assert_contains "$OUT" "next:         v1.0.0"
}
case_ "next-version bump: 0.x rule, 1.0.0 only with --to-one" t_zero_rule

t_stable() {
  tagrepo v1.4.2
  run bash "$NV" bump --level major; assert_contains "$OUT" "next:         v2.0.0"
  run bash "$NV" bump --level minor; assert_contains "$OUT" "next:         v1.5.0"
  run bash "$NV" bump --level patch; assert_contains "$OUT" "next:         v1.4.3"
  run bash "$NV" bump --level none; assert_contains "$OUT" "next: none"
}
case_ "next-version bump: stable major/minor/patch/none" t_stable

t_prerelease() {
  tagrepo v1.0.0 v2.0.0-beta.1
  run bash "$NV" bump --level major --stage beta
  assert_contains "$OUT" "next:         v2.0.0-beta.2" "base from last GA: no second major bump"
  run bash "$NV" bump --level patch --stage rc; assert_contains "$OUT" "next:         v2.0.0-rc.1" "stage promotion resets iteration"
  run bash "$NV" bump --level none; assert_contains "$OUT" "next:         v2.0.0" "GA promotes the open pre-release"
}
case_ "next-version bump: pre-release iteration, promotion, base from last GA" t_prerelease

t_ladder() {
  tagrepo v0.1.0-pre-alpha.1
  run bash "$NV" bump --level patch --stage alpha
  assert_nonzero "$RC"; assert_contains "$OUT" "does not sort above"
  run bash "$NV" check-ladder poc,mvp,pre-alpha,alpha,beta,rc
  assert_nonzero "$RC"; assert_contains "$OUT" "MISORDERED: 'pre-alpha' -> 'alpha'"
  run bash "$NV" check-ladder alpha,beta,rc; assert_status "$RC" 0
}
case_ "next-version: misordered stage labels are caught" t_ladder

t_evidence() {
  mkrepo_commit "$T/r" "init"; cd "$T/r"
  printf 'A=1\nB=2\n' > .env.example; git add .env.example; git commit -qm "env"; git tag v1.0.0
  mkdir -p app/migrations; printf 'op.drop_column("t", "c")\n' > app/migrations/002.py
  git add app; git commit -qm "Add migration"
  printf 'A=1\nC=3\n' > .env.example; git add .env.example; git commit -qm "Rename B to C"
  local before; before="$(git status --porcelain; git tag)"
  run bash "$NV"; assert_status "$RC" 0
  assert_contains "$OUT" "destructive-looking"
  assert_contains "$OUT" "removed key: B"
  assert_contains "$OUT" "added key (required?): C"
  assert_contains "$OUT" "Rename B to C" "commit hint"
  assert_eq "$(git status --porcelain; git tag)" "$before" "read-only"
  echo '{ "name": "w", "version": "1.0.0" }' > package.json
  run bash "$NV"; assert_contains "$OUT" '"version": "1.0.0"' "one-line package.json manifest"
}
case_ "next-version evidence: migrations, env keys, hints; read-only" t_evidence

t_prefix() {
  tagrepo web/v1.2.0 api/v3.0.0
  run bash "$NV" bump --level minor --tag-prefix web/v; assert_contains "$OUT" "next:         web/v1.3.0"
}
case_ "next-version bump: --tag-prefix for monorepos" t_prefix

finish
