#!/usr/bin/env bash
#
# commit.sh — commit with explicit-pathspec staging, a sanity pass and an optional trailer.
#
#   scripts/git/commit.sh -m "Subject line" [-m "body paragraph" ...] \
#       [--] <pathspec> [<pathspec> ...]
#
# What it does, in order:
#   1. Stages exactly the pathspecs you name — never a blanket `git add -A`
#      (a habit worth keeping in any repo). Aborts if `git add` fails, and if the
#      index already holds files outside the named paths (a plain `git commit`
#      would sweep them in).
#   2. Runs a sanity pass over the staged set: refuses on .env files, obvious
#      key/cert files (`.env.example`/`.sample`/`.template` are allowed), files
#      larger than 1 MiB (override with ALLOW_BIG=1), and staged merge-conflict
#      markers (an opening `<<<<<<<` and a closing `>>>>>>>` line — a bare
#      `=======` is ordinary markdown).
#   3. Appends a trailer unless a -m already carries it. The trailer resolves
#      as: the COMMIT_TRAILER env var if set (empty = append nothing), else
#      `git config commit-helper.trailer` if that key exists (empty = none).
#      If NEITHER is set, it looks at the repo's recent history for a
#      Co-Authored-By line with a <noreply@…> address (a bot/AI trailer); if it
#      finds one it saves it to the git-config key once, prints what it set,
#      and uses it. If history has none, NO trailer is appended — nothing is
#      invented for a repo that doesn't already use one. To set one:
#      `git config commit-helper.trailer "Co-Authored-By: Name <email>"`
#      (or "" to stop appending one).
#   4. Prints `git diff --cached --stat` and the assembled message, then commits.
#
# It does NOT push and does NOT open PRs. Use scripts/git/push.sh to push.

set -uo pipefail

top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "commit.sh: not a git repo" >&2; exit 1; }
cd "$top" || exit 1

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
  #    the repo's own recent history uses — but only a <noreply@…> (bot/AI) line,
  #    so a human collaborator's trailer is never adopted as the permanent default.
  #    Nothing in history -> no trailer, and nothing is written to config.
  local seed
  seed="$(git log -30 --pretty=%B 2>/dev/null \
          | grep -iE '^Co-authored-by: .+ <noreply@[^>]+>$' \
          | sort | uniq -c | sort -rn | head -1 \
          | sed -E 's/^ *[0-9]+ +//')"
  [ -n "$seed" ] || return 0
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
if ! git add -- "${paths[@]}"; then
  echo "commit.sh: git add failed for the named paths — nothing committed." >&2
  exit 1
fi

# Nothing staged? Stop.
if git diff --cached --quiet; then
  echo "commit.sh: nothing staged after add — aborting." >&2
  exit 1
fi

# Refuse if the index holds anything outside the named paths: `git commit`
# takes the whole index, so files staged earlier would ride along silently.
outside="$(comm -23 \
  <(git diff --cached --name-only | sort) \
  <(git diff --cached --name-only -- "${paths[@]}" | sort))"
if [ -n "$outside" ]; then
  echo "commit.sh: the index already holds files outside the named paths:" >&2
  printf '%s\n' "$outside" | sed 's/^/  /' >&2
  echo "commit.sh: unstage them (git restore --staged <file>) or name them too, then retry." >&2
  exit 1
fi

# 2. Sanity pass over the staged set. NUL-delimited so paths with spaces,
#    quotes or non-ASCII characters are seen exactly; checks read the staged
#    blob (what will actually be committed), not the working-tree copy.
problems=""
while IFS= read -r -d '' f; do
  case "$f" in
    .env.example|*/.env.example|.env.sample|*/.env.sample|.env.template|*/.env.template) ;;
    .env|*/.env|.env.*|*/.env.*)              problems="${problems}  env file staged: ${f}"$'\n' ;;
    *id_rsa|*id_ed25519|*id_ecdsa|*id_dsa|*.pem|*.p12|*.pfx|*.p8|*.key|*credentials.json)
                                              problems="${problems}  key/cert staged: ${f}"$'\n' ;;
  esac
  if git cat-file -e ":$f" 2>/dev/null; then   # skip staged deletions (no blob)
    sz="$(git cat-file -s ":$f" 2>/dev/null || echo 0)"
    if [ "${ALLOW_BIG:-0}" != "1" ] && [ "$sz" -gt 1048576 ]; then
      problems="${problems}  large file >1MiB staged: ${f} (${sz} bytes) — set ALLOW_BIG=1 to allow"$'\n'
    fi
    # A conflict needs both an opening and a closing marker; a bare `=======`
    # is ordinary markdown/rst (setext heading underline, a rule).
    blob="$(git show ":$f" 2>/dev/null)"
    if printf '%s\n' "$blob" | grep -qE '^<<<<<<<([[:space:]]|$)' \
       && printf '%s\n' "$blob" | grep -qE '^>>>>>>>([[:space:]]|$)'; then
      problems="${problems}  merge-conflict markers in: ${f}"$'\n'
    fi
  fi
done < <(git diff --cached --name-only -z)

if [ -n "$problems" ]; then
  echo "commit.sh: pre-commit checks flagged the staged set:" >&2
  printf '%s' "$problems" >&2
  echo "commit.sh: fix or unstage, then retry." >&2
  exit 1
fi

# 3. Assemble -m args, appending the trailer if set and not already present.
commit_args=()
for m in "${msgs[@]}"; do commit_args+=(-m "$m"); done
add_trailer=0
if [ -n "$TRAILER" ] && ! printf '%s\n' "${msgs[@]}" | grep -qF -- "$TRAILER"; then
  add_trailer=1
  commit_args+=(-m "$TRAILER")
fi

# 4. Show, then commit.
echo "── staged ─────────────────────────────"
git diff --cached --stat
echo "── message ────────────────────────────"
for m in "${msgs[@]}"; do printf '%s\n\n' "$m"; done
[ "$add_trailer" = 1 ] && printf '%s\n' "$TRAILER"
echo "───────────────────────────────────────"
git commit "${commit_args[@]}"
