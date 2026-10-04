#!/usr/bin/env bash
# Tiny test harness, sourced by every scripts/tests/test_*.sh.
#   case_ "name" fn      run fn in a subshell, inside a fresh throwaway dir
#   assert_eq / assert_contains / assert_not_contains / assert_status / assert_file / assert_no_file
# A case passes when no assert in it failed. Output of a case is shown only on failure.
# Each case gets: $T (temp dir), HOME=$T/home, CLAUDE_PROJECT_DIR=$T/proj (created), git identity
# pinned, global/system git config off, COMMIT_TRAILER / SKILL_LOG_* unset. Nothing in the real
# repo or real home is written by the harness itself.
set -u
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$LIB_DIR/../.." && pwd)"
# SCRIPTS_DIR lets a test run be pointed at a modified copy of scripts/ (used to prove tests can fail).
SCRIPTS="${SCRIPTS_DIR:-$REPO/scripts}"
export PYTHONDONTWRITEBYTECODE=1
_TMPS="$(mktemp -d)"
trap 'rm -rf "$_TMPS"' EXIT
_pass=0; _fail=0; _n=0

_fail_msg() { printf '    FAILED: %s\n' "$*"; echo 1 >> "$T/.fails"; }

assert_eq()           { [ "$1" = "$2" ] || _fail_msg "${3:-eq}: expected [$2] got [$1]"; }
assert_contains()     { case "$1" in *"$2"*) ;; *) _fail_msg "${3:-contains}: [$2] not in output: $1" ;; esac; }
assert_not_contains() { case "$1" in *"$2"*) _fail_msg "${3:-not-contains}: [$2] unexpectedly in output: $1" ;; esac; }
assert_status()       { [ "$1" = "$2" ] || _fail_msg "${3:-status}: expected exit $2 got $1"; }
assert_nonzero()      { [ "$1" != 0 ] || _fail_msg "${2:-status}: expected non-zero exit"; }
assert_file()         { [ -e "$1" ] || _fail_msg "missing file: $1"; }
assert_no_file()      { [ ! -e "$1" ] || _fail_msg "unexpected file: $1"; }

# run <cmd...>: capture combined output in $OUT and exit code in $RC (never aborts the case).
run() { OUT="$("$@" 2>&1)"; RC=$?; }
# run_in <stdin-string> <cmd...>
run_in() { local in="$1"; shift; OUT="$(printf '%s' "$in" | "$@" 2>&1)"; RC=$?; }

# Snapshot of every file under a dir: path, size, mtime. Used to prove "no writes outside X".
snap() { (cd "$1" && find . -type f -printf '%p %s %T@\n' | sort); }

# git helpers -------------------------------------------------------------
mkrepo() { # mkrepo dir  -> git repo on branch main (no commits)
  mkdir -p "$1" && git -C "$1" init -q -b main && git -C "$1" config user.name tester \
    && git -C "$1" config user.email t@example.com && git -C "$1" config commit.gpgsign false
}
mkrepo_commit() { # mkrepo_commit dir [message]  -> repo with one commit (file seed.txt)
  mkrepo "$1"; echo seed > "$1/seed.txt"; git -C "$1" add seed.txt
  git -C "$1" commit -q -m "${2:-init}"
}
copy_scripts() { # copy_scripts dest  -> scripts/ (git hooks skills session) without tests
  mkdir -p "$1/scripts"
  local d; for d in git hooks skills session; do cp -r "$SCRIPTS/$d" "$1/scripts/"; done
}
mkskill() { # mkskill root name "description"  -> valid skill dir
  mkdir -p "$1/$2"
  printf -- '---\nname: %s\ndescription: %s\n---\n\n# %s\n\nBody.\n' "$2" "$3" "$2" > "$1/$2/SKILL.md"
}

case_() { # case_ "name" fn
  local name="$1" fn="$2" out rc
  _n=$((_n + 1))
  local t="$_TMPS/c$_n"; mkdir -p "$t/home" "$t/proj"
  out="$( (
    set +e
    export T="$t" HOME="$t/home" CLAUDE_PROJECT_DIR="$t/proj"
    export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1
    export GIT_AUTHOR_NAME=tester GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=tester GIT_COMMITTER_EMAIL=t@example.com
    unset COMMIT_TRAILER SKILL_LOG_GLOBAL SKILL_LOG_DIR CONTEXT_LIMIT HANDOFF_RATIO
    cd "$t"
    : > "$t/.fails"
    "$fn"
    [ ! -s "$t/.fails" ]
  ) 2>&1 )"; rc=$?
  if [ "$rc" -eq 0 ]; then _pass=$((_pass + 1)); echo "PASS  $name"
  else _fail=$((_fail + 1)); echo "FAIL  $name"; printf '%s\n' "$out" | sed 's/^/      /'; fi
}

finish() { echo "-- $(basename "$0"): $_pass passed, $_fail failed"; [ "$_fail" -eq 0 ]; }
