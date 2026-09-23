#!/usr/bin/env bash
#
# commit.sh — commit with a repo's staging + message conventions baked in.
#
#   scripts/git/commit.sh -m "Subject line" [-m "body paragraph" ...] \
#       [--] <pathspec> [<pathspec> ...]
#
# What it does, in order:
#   1. Stages exactly the pathspecs you name — never a blanket `git add -A`
#      (see .claude/rules/conventions.md).
#   2. Runs a sanity pass over the staged set: refuses on .env files, obvious
#      key/cert files, files larger than 1 MiB (override with ALLOW_BIG=1),
#      and staged merge-conflict markers.
#   3. Appends a trailer unless a -m already carries it. The trailer resolves
#      as: the COMMIT_TRAILER env var if set (empty = append nothing), else
#      `git config commit-helper.trailer` if that key exists (empty = none).
#      If NEITHER is set, first run auto-initialises the git-config key once —
#      to the Co-Authored-By line the repo's recent history already uses, or
#      the built-in default if there is none — prints what it set, and uses
#      that. So a fresh repo needs no manual `git config`; to change it later,
#      `git config commit-helper.trailer "…"` (or "" to stop appending one).
#   4. Prints `git diff --cached --stat` and the assembled message, then commits.
#
# It does NOT push and does NOT open PRs. Use scripts/git/push.sh to push.

set -uo pipefail

top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "commit.sh: not a git repo" >&2; exit 1; }
cd "$top" || exit 1

DEFAULT_TRAILER="Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"

resolve_trailer() {
  # 1. Ephemeral override — COMMIT_TRAILER set (even to empty) wins, no config touched.
  if [ "${COMMIT_TRAILER+set}" = set ]; then
    printf '%s' "$COMMIT_TRAILER"
    return
  fi
  # 2. An existing git-config key (any scope) — empty value means "deliberately none".
  if git config --get commit-helper.trailer >/dev/null 2>&1; then
    git config --get commit-helper.trailer
    return
  fi
  # 3. Unconfigured — seed the key once, visibly. Prefer the Co-Authored-By line
  #    the repo's own recent history uses; fall back to the built-in default.
  local seed
  seed="$(git log -30 --pretty=%B 2>/dev/null \
          | grep -iE '^Co-authored-by: .+ <.+>$' \
          | sort | uniq -c | sort -rn | head -1 \
          | sed -E 's/^ *[0-9]+ +//')"
  [ -n "$seed" ] || seed="$DEFAULT_TRAILER"
  if git config --local commit-helper.trailer "$seed" 2>/dev/null; then
    echo "commit.sh: initialised  commit-helper.trailer = \"$seed\"" >&2
    echo "commit.sh:   change:  git config commit-helper.trailer \"…\"   ( \"\" = append no trailer )" >&2
  fi
  printf '%s' "$seed"
}

TRAILER="$(resolve_trailer)"

msgs=()
paths=()
while [ $# -gt 0 ]; do
  case "$1" in
    -m)
      shift
      [ $# -gt 0 ] || { echo "commit.sh: -m needs an argument" >&2; exit 2; }
      msgs+=("$1"); shift ;;
    --)
      shift
      while [ $# -gt 0 ]; do paths+=("$1"); shift; done ;;
    -*)
      echo "commit.sh: unknown flag: $1" >&2; exit 2 ;;
    *)
      paths+=("$1"); shift ;;
  esac
done

[ "${#msgs[@]}" -gt 0 ]  || { echo "commit.sh: need at least one -m \"message\"" >&2; exit 2; }
[ "${#paths[@]}" -gt 0 ] || { echo "commit.sh: name at least one pathspec (never blanket-add)" >&2; exit 2; }

# 1. Stage the named pathspecs.
git add -- "${paths[@]}"

# Nothing staged? Stop.
if git diff --cached --quiet; then
  echo "commit.sh: nothing staged after add — aborting." >&2
  exit 1
fi

# 2. Sanity pass over the staged set.
problems=""
staged_files="$(git diff --cached --name-only)"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    .env|*/.env|.env.*|*/.env.*)              problems="${problems}  env file staged: ${f}"$'\n' ;;
    *id_rsa|*id_ed25519|*.pem|*.p12|*.pfx)    problems="${problems}  key/cert staged: ${f}"$'\n' ;;
  esac
  if [ -f "$f" ]; then
    sz="$(wc -c < "$f" 2>/dev/null || echo 0)"
    if [ "${ALLOW_BIG:-0}" != "1" ] && [ "$sz" -gt 1048576 ]; then
      problems="${problems}  large file >1MiB staged: ${f} (${sz} bytes) — set ALLOW_BIG=1 to allow"$'\n'
    fi
    if git show ":$f" 2>/dev/null | grep -qE '^(<<<<<<<|>>>>>>>|=======)([[:space:]]|$)'; then
      problems="${problems}  merge-conflict markers in: ${f}"$'\n'
    fi
  fi
done <<EOF
$staged_files
EOF

if [ -n "$problems" ]; then
  echo "commit.sh: pre-commit checks flagged the staged set:" >&2
  printf '%s' "$problems" >&2
  echo "commit.sh: fix or unstage, then retry." >&2
  exit 1
fi

# 3. Assemble -m args, appending the trailer if set and not already present.
commit_args=()
for m in "${msgs[@]}"; do commit_args+=(-m "$m"); done
if [ -n "$TRAILER" ] && ! printf '%s\n' "${msgs[@]}" | grep -qF -- "$TRAILER"; then
  commit_args+=(-m "$TRAILER")
fi

# 4. Show, then commit.
echo "── staged ─────────────────────────────"
git diff --cached --stat
echo "── message ────────────────────────────"
for m in "${msgs[@]}"; do printf '%s\n\n' "$m"; done
[ -n "$TRAILER" ] && printf '%s\n' "$TRAILER"
echo "───────────────────────────────────────"
git commit "${commit_args[@]}"
