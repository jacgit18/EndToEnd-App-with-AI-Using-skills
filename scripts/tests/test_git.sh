#!/usr/bin/env bash
# Git helpers: state.sh, commit.sh, push.sh, land.sh.
. "$(dirname "$0")/lib.sh"

G="$SCRIPTS/git"

# --- state.sh ---
t_state_normal() {
  mkrepo_commit "$T/r" "first commit"; cd "$T/r"
  echo more >> seed.txt; echo new > "new file.txt"; echo s > staged.txt; git add staged.txt
  local before; before="$(git status --porcelain)"
  run bash "$G/state.sh"
  assert_status "$RC" 0
  assert_contains "$OUT" "branch: main   (no upstream)"
  assert_contains "$OUT" "A	staged.txt"
  assert_contains "$OUT" "M	seed.txt"
  assert_contains "$OUT" "new file.txt"
  assert_contains "$OUT" "first commit"
  assert_eq "$(git status --porcelain)" "$before" "read-only"
}
case_ "state.sh: staged/unstaged/untracked/log snapshot, read-only" t_state_normal

t_state_nocommit() {
  mkrepo "$T/r"; cd "$T/r"; echo x > a.txt
  run bash "$G/state.sh"
  assert_status "$RC" 0
  assert_contains "$OUT" "branch: main (no commits yet)"
  assert_contains "$OUT" "(no commits yet)" "log section"
  assert_not_contains "$OUT" "fatal"
  mkdir "$T/plain"; cd "$T/plain"; run bash "$G/state.sh"
  assert_status "$RC" 0; assert_contains "$OUT" "not a git repo"
}
case_ "state.sh: repo with no commits prints a message, not fatal errors; non-repo ok" t_state_nocommit

# --- commit.sh ---
BOT='Co-Authored-By: Test Bot <noreply@example.com>'
mk_trailer_repo() { mkrepo_commit "$T/r" "init

$BOT"; cd "$T/r"; }

t_commit_named() {
  mk_trailer_repo
  echo a > a.txt; echo b > b.txt; echo mod >> seed.txt
  run bash "$G/commit.sh" -m "Add a" -m "body para" -- a.txt
  assert_status "$RC" 0
  assert_eq "$(git show --name-only --format= HEAD)" "a.txt" "only the named path"
  local msg; msg="$(git log -1 --format=%B)"
  assert_contains "$msg" "Add a"; assert_contains "$msg" "body para"
  assert_contains "$msg" "$BOT" "trailer seeded from history"
  assert_eq "$(git config --local commit-helper.trailer)" "$BOT" "key written once"
  assert_contains "$(git status --porcelain)" "?? b.txt" "unnamed files left alone"
  assert_contains "$(git status --porcelain)" " M seed.txt"
}
case_ "commit.sh: commits only named paths, trailer taken from history" t_commit_named

t_commit_no_trailer() {
  mkrepo_commit "$T/r" "plain history"; cd "$T/r"; echo a > a.txt
  run bash "$G/commit.sh" -m "No trailer" -- a.txt
  assert_status "$RC" 0
  assert_not_contains "$(git log -1 --format=%B)" "Co-Authored"
  assert_eq "$(git config --local commit-helper.trailer || echo unset)" "unset" "nothing invented"
  echo b > b.txt
  COMMIT_TRAILER="Co-Authored-By: X <noreply@x.io>" run bash "$G/commit.sh" -m "Env trailer" -- b.txt
  assert_contains "$(git log -1 --format=%B)" "Co-Authored-By: X <noreply@x.io>"
}
case_ "commit.sh: no trailer when history has none; COMMIT_TRAILER override" t_commit_no_trailer

t_commit_deletion() {
  mk_trailer_repo; echo y > gone.txt; git add gone.txt; git commit -q -m "add gone"
  rm gone.txt
  run bash "$G/commit.sh" -m "Delete gone" -- gone.txt
  assert_status "$RC" 0 "deleted path commits"
  assert_eq "$(git show --name-status --format= HEAD)" "D	gone.txt"
  # git rm'd (gone from disk and index) path
  echo z > gone2.txt; git add gone2.txt; git commit -q -m "add gone2"
  git rm -q gone2.txt
  run bash "$G/commit.sh" -m "Delete gone2" -- gone2.txt
  assert_status "$RC" 0 "git rm'd path commits"
  assert_eq "$(git show --name-status --format= HEAD)" "D	gone2.txt"
}
case_ "commit.sh: deletions commit (rm and git rm)" t_commit_deletion

t_commit_reject_tree() {
  mk_trailer_repo; echo a > a.txt
  local head p; head="$(git rev-parse HEAD)"
  for p in . ./ : :/ '*' '**' ..; do
    run bash "$G/commit.sh" -m "x" -- "$p"
    assert_status "$RC" 2 "reject '$p'"
    assert_contains "$OUT" "whole-tree" "message for '$p'"
  done
  mkdir sub; echo s > sub/s.txt; (cd sub && run bash "$G/commit.sh" -m x -- .)
  assert_eq "$(git rev-parse HEAD)" "$head" "no commit made"
  assert_eq "$(git diff --cached --name-only)" "" "nothing staged"
}
case_ "commit.sh: rejects whole-tree pathspecs . ./ : :/ * ** .." t_commit_reject_tree

t_commit_unrelated_staged() {
  mk_trailer_repo; echo a > a.txt; echo o > other.txt; git add other.txt
  local head; head="$(git rev-parse HEAD)"
  run bash "$G/commit.sh" -m "x" -- a.txt
  assert_status "$RC" 1
  assert_contains "$OUT" "outside the named paths"; assert_contains "$OUT" "other.txt"
  assert_eq "$(git rev-parse HEAD)" "$head" "no commit made"
}
case_ "commit.sh: refuses when an unrelated file is already staged" t_commit_unrelated_staged

t_commit_space_unicode() {
  mk_trailer_repo; echo a > "my file.txt"; mkdir "dir with space"; echo b > "dir with space/é ü.txt"
  run bash "$G/commit.sh" -m "Spaces" -- "my file.txt" "dir with space"
  assert_status "$RC" 0
  assert_eq "$(git -c core.quotepath=off show --name-only --format= HEAD | sort)" "$(printf 'dir with space/é ü.txt\nmy file.txt')"
}
case_ "commit.sh: paths with spaces and unicode" t_commit_space_unicode

t_commit_binary() {
  mk_trailer_repo; head -c 4096 /dev/urandom | tr -d '\n' > bin.dat; printf 'a\0b\0\xff' >> bin.dat
  run bash "$G/commit.sh" -m "Binary" -- bin.dat
  assert_status "$RC" 0
  assert_not_contains "$OUT" "null byte" "no bash NUL warning"
  assert_eq "$(git show --name-only --format= HEAD)" "bin.dat"
}
case_ "commit.sh: binary file commits cleanly (no NUL warnings)" t_commit_binary

t_commit_sanity() {
  mk_trailer_repo; local head; head="$(git rev-parse HEAD)"
  echo SECRET=1 > .env
  run bash "$G/commit.sh" -m x -- .env; assert_status "$RC" 1; assert_contains "$OUT" "env file staged"
  git reset -q; rm .env
  printf '<<<<<<< a\nx\n=======\ny\n>>>>>>> b\n' > c.txt
  run bash "$G/commit.sh" -m x -- c.txt; assert_status "$RC" 1; assert_contains "$OUT" "merge-conflict markers"
  git reset -q; rm c.txt
  printf 'Title\n=======\n' > ok.md
  run bash "$G/commit.sh" -m x -- ok.md; assert_status "$RC" 0 "bare ======= is fine"
  assert_eq "$(git rev-list --count "$head"..HEAD)" "1"
}
case_ "commit.sh: refuses .env and conflict markers, allows setext markdown" t_commit_sanity

t_commit_args() {
  mk_trailer_repo
  run bash "$G/commit.sh" -- seed.txt; assert_status "$RC" 2 "no -m"
  run bash "$G/commit.sh" -m x; assert_status "$RC" 2 "no paths"
  run bash "$G/commit.sh" -m x -- seed.txt; assert_status "$RC" 1 "nothing staged"
  mkdir "$T/nogit"; cd "$T/nogit"; run bash "$G/commit.sh" -m x -- f; assert_status "$RC" 1 "not a repo"
}
case_ "commit.sh: usage errors and nothing-to-commit" t_commit_args

# --- push.sh ---
mk_remote() { # origin bare + working repo with one commit pushed to nothing yet
  git init -q --bare -b main "$T/origin.git"
  mkrepo_commit "$T/w"; cd "$T/w"; git remote add origin "$T/origin.git"
}
t_push_ok() {
  mk_remote
  PUSH_TIMEOUT=30 run bash "$G/push.sh"
  assert_status "$RC" 0; assert_contains "$OUT" "push — ok"
  assert_eq "$(git --git-dir="$T/origin.git" rev-parse main)" "$(git rev-parse HEAD)"
  assert_eq "$(git rev-parse --abbrev-ref '@{u}')" "origin/main" "upstream set"
}
case_ "push.sh: pushes to a bare remote and sets upstream" t_push_ok

t_push_nff() {
  mk_remote; PUSH_TIMEOUT=30 bash "$G/push.sh" >/dev/null 2>&1
  git clone -q "$T/origin.git" "$T/other"; git -C "$T/other" config user.email o@x.com; git -C "$T/other" config user.name o
  echo o > "$T/other/o.txt"; git -C "$T/other" add o.txt; git -C "$T/other" commit -q -m other; git -C "$T/other" push -q origin main
  echo l > l.txt; git add l.txt; git commit -q -m local
  local remote_head; remote_head="$(git --git-dir="$T/origin.git" rev-parse main)"
  PUSH_TIMEOUT=30 run bash "$G/push.sh"
  assert_nonzero "$RC"; assert_contains "$OUT" "not retrying"
  assert_not_contains "$OUT" "HTTP/1.1" "no fallback/retry loop on rejection"
  assert_eq "$(printf '%s\n' "$OUT" | grep -c '^push.sh: push \.\.\.')" "1" "exactly one attempt"
  assert_eq "$(git --git-dir="$T/origin.git" rev-parse main)" "$remote_head" "remote unchanged"
}
case_ "push.sh: non-fast-forward is rejected, stops without a retry loop" t_push_nff

t_push_detached() {
  mkrepo_commit "$T/w"; cd "$T/w"; git checkout -q --detach
  run bash "$G/push.sh"; assert_status "$RC" 1; assert_contains "$OUT" "detached HEAD"
}
case_ "push.sh: refuses detached HEAD" t_push_detached

# --- land.sh ---
t_land_no_gh() {
  mkrepo_commit "$T/r"; cd "$T/r"
  mkdir "$T/bin"; ln -s "$(command -v git)" "$T/bin/git"
  PATH="$T/bin" run /bin/bash "$G/land.sh"
  assert_nonzero "$RC"; assert_contains "$OUT" "needs the gh CLI"
  PATH="$T/bin" run /bin/bash "$G/land.sh" --bogus
  assert_nonzero "$RC"
}
case_ "land.sh: without gh on PATH exits non-zero with a clear message" t_land_no_gh

finish
