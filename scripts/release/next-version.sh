#!/usr/bin/env bash
#
# next-version.sh — evidence and arithmetic for the next release version. Read-only.
# Pairs with the `release-version-calc` skill: this script gathers and computes, the skill
# (and the human) judge. It never edits a file, creates a tag or pushes.
#
#   next-version.sh [evidence] [--since TAG] [--path DIR] [--tag-prefix P]
#       What changed since the last release, grouped by contract surface: migrations
#       (with destructive-looking lines), API contract files, deleted source files, env
#       keys added/removed, runtime pins, dependency manifests, commit-message hints, and
#       the version string in every manifest found. Default subcommand.
#
#   next-version.sh bump --level none|patch|minor|major [--stage ga|<label>]
#                        [--ladder a,b,rc] [--since TAG] [--tag-prefix P] [--path DIR]
#       The next version from the last tags + a bump level someone already decided.
#       Applies: highest-wins input, the 0.x rule (breaking -> minor, the rest -> patch
#       while major is 0), base computed from the last GA tag (not the last pre-release),
#       pre-release iteration/promotion, and a final "is it actually higher" check.
#       --stage defaults to ga. 1.0.0 is never reached by a bump: pass --level major
#       with --to-one when the owner declares the API stable.
#
#   next-version.sh check-ladder a,b,rc
#       Whether pre-release stage labels sort in the intended order under SemVer
#       precedence (ASCII per identifier). "pre-alpha" sorts AFTER "alpha"; "poc" after "mvp".
#
# Tags: <prefix>MAJOR.MINOR.PATCH[-pre] reachable from HEAD; prefix defaults to "v"
# (monorepos: --tag-prefix web/v). RELEASE_LADDER env var is the default --ladder.
set -euo pipefail
export LC_ALL=C

die() { echo "next-version: $*" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || die "not a git repo"

sub=evidence
case "${1:-}" in evidence|bump|check-ladder) sub="$1"; shift ;; esac

since="" path="." prefix="v" level="" stage="ga" ladder="${RELEASE_LADDER:-}" to_one=0
ladder_arg=""
while [ $# -gt 0 ]; do
  case "$1" in
    --since) since="${2:?}"; shift 2 ;;
    --path) path="${2:?}"; shift 2 ;;
    --tag-prefix) prefix="${2-}"; shift 2 ;;
    --level) level="${2:?}"; shift 2 ;;
    --stage) stage="${2:?}"; shift 2 ;;
    --ladder) ladder="${2:?}"; shift 2 ;;
    --to-one) to_one=1; shift ;;
    -h|--help) sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) if [ "$sub" = check-ladder ] && [ -z "$ladder_arg" ]; then ladder_arg="$1"; shift
       else die "unknown argument: $1"; fi ;;
  esac
done

# --- SemVer helpers -----------------------------------------------------------------
SEMVER_RE='^([0-9]+)\.([0-9]+)\.([0-9]+)(-([0-9A-Za-z.-]+))?$'

# cmp_pre A B -> -1|0|1 for two pre-release strings (empty = release, which ranks higher)
cmp_pre() {
  local a="$1" b="$2"
  if [ -z "$a" ] && [ -z "$b" ]; then echo 0; return; fi
  if [ -z "$a" ]; then echo 1; return; fi
  if [ -z "$b" ]; then echo -1; return; fi
  local IFS=. ; local -a x=($a) y=($b); local i n=${#x[@]}
  [ ${#y[@]} -gt "$n" ] && n=${#y[@]}
  for ((i = 0; i < n; i++)); do
    local p="${x[i]-}" q="${y[i]-}"
    if [ -z "$p" ]; then echo -1; return; fi
    if [ -z "$q" ]; then echo 1; return; fi
    if [[ "$p" =~ ^[0-9]+$ && "$q" =~ ^[0-9]+$ ]]; then
      if ((10#$p < 10#$q)); then echo -1; return; elif ((10#$p > 10#$q)); then echo 1; return; fi
    elif [[ "$p" =~ ^[0-9]+$ ]]; then echo -1; return
    elif [[ "$q" =~ ^[0-9]+$ ]]; then echo 1; return
    elif [[ "$p" < "$q" ]]; then echo -1; return
    elif [[ "$p" > "$q" ]]; then echo 1; return
    fi
  done
  echo 0
}

# cmp_ver A B -> -1|0|1 (no prefix)
cmp_ver() {
  [[ "$1" =~ $SEMVER_RE ]] || die "not semver: $1"
  local a1=${BASH_REMATCH[1]} a2=${BASH_REMATCH[2]} a3=${BASH_REMATCH[3]} ap=${BASH_REMATCH[5]-}
  [[ "$2" =~ $SEMVER_RE ]] || die "not semver: $2"
  local b1=${BASH_REMATCH[1]} b2=${BASH_REMATCH[2]} b3=${BASH_REMATCH[3]} bp=${BASH_REMATCH[5]-}
  local k
  for k in "$a1 $b1" "$a2 $b2" "$a3 $b3"; do
    set -- $k
    if ((10#$1 < 10#$2)); then echo -1; return; elif ((10#$1 > 10#$2)); then echo 1; return; fi
  done
  cmp_pre "$ap" "$bp"
}

# Release tags reachable from HEAD, prefix stripped, one per line.
release_versions() {
  git tag --merged HEAD --list "${prefix}*" 2>/dev/null | while IFS= read -r t; do
    local v="${t#"$prefix"}"
    [[ "$v" =~ $SEMVER_RE ]] && echo "$v"
  done
}

highest() { # highest [ga]  -> highest version (only GA ones if $1=ga), or empty
  local best="" v
  while IFS= read -r v; do
    [ -n "$v" ] || continue
    if [ "${1-}" = ga ] && [[ "$v" == *-* ]]; then continue; fi
    if [ -z "$best" ] || [ "$(cmp_ver "$v" "$best")" = 1 ]; then best="$v"; fi
  done < <(release_versions)
  echo "$best"
}

show() { if [ -n "$1" ]; then echo "$prefix$1"; else echo "${2:-(none)}"; fi; }

check_ladder() { # check_ladder "a,b,c" -> prints findings; returns 1 if misordered
  local IFS=, ; local -a L=($1); local i bad=0
  for ((i = 1; i < ${#L[@]}; i++)); do
    if [ "$(cmp_pre "${L[i-1]}.1" "${L[i]}.1")" != -1 ]; then
      echo "MISORDERED: '${L[i-1]}' -> '${L[i]}' — under SemVer precedence 1.0.0-${L[i]}.1 sorts BELOW 1.0.0-${L[i-1]}.1, so package managers and 'latest' pickers treat the later stage as older."
      bad=1
    fi
  done
  [ "$bad" = 0 ] && echo "ok: ${1//,/ < } sorts in ladder order under SemVer precedence"
  return "$bad"
}

# --- check-ladder -------------------------------------------------------------------
if [ "$sub" = check-ladder ]; then
  l="${ladder_arg:-$ladder}"; [ -n "$l" ] || die "usage: next-version.sh check-ladder a,b,rc"
  check_ladder "$l"; exit $?
fi

last="$(highest)"; last_ga="$(highest ga)"
if [ -n "$since" ]; then
  git rev-parse -q --verify "$since^{commit}" >/dev/null || die "--since '$since' is not a commit or tag"
  base_ref="$since"
elif [ -n "$last" ]; then base_ref="$prefix$last"
else base_ref=""
fi

# --- bump ---------------------------------------------------------------------------
if [ "$sub" = bump ]; then
  case "$level" in none|patch|minor|major) ;; *) die "--level none|patch|minor|major is required" ;; esac
  ga="${last_ga:-0.0.0}"
  [[ "$ga" =~ $SEMVER_RE ]]; M=${BASH_REMATCH[1]} m=${BASH_REMATCH[2]} p=${BASH_REMATCH[3]}
  eff="$level"; note=""
  if [ "$M" = 0 ] && [ "$to_one" = 0 ]; then
    case "$level" in
      major) eff=minor; note="0.x rule: breaking change bumps MINOR while major is 0 (1.0.0 only with --to-one)" ;;
      minor) eff=patch; note="0.x rule: additive change bumps PATCH while major is 0" ;;
    esac
  fi
  [ "$to_one" = 1 ] && { [ "$level" = major ] || die "--to-one needs --level major"; }
  case "$eff" in
    major) cand="$((M + 1)).0.0" ;;
    minor) cand="$M.$((m + 1)).0" ;;
    patch) cand="$M.$m.$((p + 1))" ;;
    none)  cand="$ga" ;;
  esac
  [ -z "$last_ga" ] && [ "$level" != none ] && [ "$to_one" = 0 ] && { cand="0.1.0"; note="no GA tag yet: first base is 0.1.0"; }
  [ "$to_one" = 1 ] && { cand="1.0.0"; note="owner declared the public API stable: 1.0.0"; }

  # An open pre-release line whose base already covers the candidate keeps that base.
  open_base="" open_pre=""
  if [ -n "$last" ] && [[ "$last" == *-* ]]; then
    open_base="${last%%-*}"; open_pre="${last#*-}"
    if [ "$level" = none ] || [ "$(cmp_ver "$open_base" "$cand")" != -1 ]; then cand="$open_base"; fi
  fi

  if [ "$stage" = ga ]; then
    if [ "$level" = none ] && [ -z "$open_base" ]; then
      echo "next: none — no contract change since $(show "$last") and no pre-release to promote"; exit 0
    fi
    next="$cand"
  else
    [[ "$stage" =~ ^[0-9A-Za-z-]+$ ]] || die "bad stage label: $stage"
    if [ -n "$open_base" ] && [ "$open_base" = "$cand" ] && [[ "$open_pre" =~ ^(.+)\.([0-9]+)$ ]] \
       && [ "${BASH_REMATCH[1]}" = "$stage" ]; then
      next="$cand-$stage.$((BASH_REMATCH[2] + 1))"
    else
      next="$cand-$stage.1"
    fi
  fi

  echo "last tag:     $(show "$last")"
  echo "last GA:      $(show "$last_ga" "(none — base 0.0.0)")"
  echo "level:        $level${note:+  ($note)}"
  echo "stage:        $stage"
  echo "next:         $prefix$next"
  if [ -n "$last" ] && [ "$(cmp_ver "$next" "$last")" != 1 ]; then
    echo "WARNING: $prefix$next does not sort above $prefix$last under SemVer precedence."
    [ "$stage" != ga ] && [ -n "$open_pre" ] && echo "         (stage '$stage' vs '${open_pre%.*}': run check-ladder; rename stages so they sort, or bump the base)"
    exit 1
  fi
  if [ -n "$ladder" ]; then check_ladder "$ladder" || true; fi
  exit 0
fi

# --- evidence -----------------------------------------------------------------------
if [ -n "$base_ref" ]; then range="$base_ref..HEAD"; diff_base="$base_ref"
else range="HEAD"; diff_base="$(git hash-object -t tree /dev/null)"
fi
ncommits="$(git rev-list --count --no-merges "$range" -- "$path")"

echo "== Range"
echo "last tag: $(show "$last")   last GA: $(show "$last_ga")"
echo "range:    ${base_ref:-<root>}..HEAD   path: $path   non-merge commits: $ncommits"
[ "$ncommits" = 0 ] && { echo "Nothing changed in this path since the last tag."; exit 0; }

mapfile -t changes < <(git diff --name-status -M "$diff_base" HEAD -- "$path")
added() { git diff "$diff_base" HEAD -- "$1" | grep -E '^\+[^+]' | cut -c2- || true; }
removed() { git diff "$diff_base" HEAD -- "$1" | grep -E '^-[^-]' | cut -c2- || true; }

mig=() api=() dels=() envf=() runtime=() deps=() lock=() other=0 docs=0
for line in "${changes[@]}"; do
  st="${line%%$'\t'*}"; f="${line##*$'\t'}"
  case "$f" in
    *.lock|*lock.json|*-lock.yaml|*.lockb|go.sum|poetry.lock|uv.lock|Cargo.lock|Gemfile.lock|composer.lock) lock+=("$f"); continue ;;
  esac
  if [[ "$f" =~ (^|/)(migrations?|migrate|alembic|flyway|liquibase)/ || "$f" =~ (^|/)db/.*\.sql$ ]]; then mig+=("$st $f"); continue; fi
  if [[ "$f" =~ (openapi|swagger)[^/]*\.(ya?ml|json)$ || "$f" =~ \.(proto|graphqls?|gql|avsc)$ ]]; then api+=("$st $f"); continue; fi
  if [[ "$f" =~ (^|/)\.env\.(example|sample|template|dist)$ || "$f" =~ (^|/)(example|sample)\.env$ ]]; then envf+=("$f"); continue; fi
  if [[ "$f" =~ (^|/)(Dockerfile[^/]*|Containerfile|\.nvmrc|\.node-version|\.python-version|\.tool-versions|rust-toolchain(\.toml)?|\.ruby-version)$ ]]; then runtime+=("$f"); continue; fi
  if [[ "$f" =~ (^|/)(package\.json|pyproject\.toml|requirements[^/]*\.txt|Cargo\.toml|go\.mod|Gemfile|composer\.json|pom\.xml|build\.gradle(\.kts)?|[^/]*\.csproj)$ ]]; then deps+=("$f"); continue; fi
  if [[ "$f" =~ \.(md|mdx|rst|txt|adoc)$ || "$f" =~ (^|/)(docs?|\.github|\.gitlab|\.circleci|tests?|__tests__|e2e|spec)/ || "$f" =~ \.(test|spec)\.[a-z]+$ || "$f" =~ (^|/)test_[^/]*$ ]]; then docs=$((docs + 1)); continue; fi
  other=$((other + 1))
  [[ "$st" == D* ]] && dels+=("$f")
done

echo
echo "== Product files changed: $other   docs/CI/tests-only files: $docs   lockfiles: ${#lock[@]}"
[ "$other" = 0 ] && [ ${#mig[@]} = 0 ] && [ ${#api[@]} = 0 ] && [ ${#envf[@]} = 0 ] && [ ${#runtime[@]} = 0 ] && [ ${#deps[@]} = 0 ] \
  && echo "Only docs/CI/tests/lockfiles changed — usually no release, or a patch if a lockfile fixes a shipped vulnerability."

echo
echo "== Migrations (${#mig[@]})"
for e in ${mig[@]+"${mig[@]}"}; do
  echo "  $e"
  f="${e#* }"
  added "$f" | grep -inE 'drop|rename|alter[ _]column|remove_column|not null|nullable *= *false|truncate|delete from' \
    | head -5 | sed 's/^/      destructive-looking: /' || true
done

echo
echo "== API contract files (${#api[@]})"
for e in ${api[@]+"${api[@]}"}; do
  f="${e#* }"; echo "  $e   (+$(added "$f" | wc -l) / -$(removed "$f" | wc -l) lines)"
done

echo
echo "== Deleted source files (${#dels[@]}) — possible removed public surface"
for f in ${dels[@]+"${dels[@]}"}; do echo "  $f"; done

echo
echo "== Env/config template keys"
for f in ${envf[@]+"${envf[@]}"}; do
  a="$(added "$f" | grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' | tr -d = | sort -u || true)"
  r="$(removed "$f" | grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' | tr -d = | sort -u || true)"
  echo "  $f"
  comm -23 <(echo "$r") <(echo "$a") | sed '/^$/d; s/^/      removed key: /'
  comm -13 <(echo "$r") <(echo "$a") | sed '/^$/d; s/^/      added key (required?): /'
done

echo
echo "== Runtime pins"
for f in ${runtime[@]+"${runtime[@]}"}; do
  echo "  $f"
  { removed "$f" | grep -E '^(FROM|[0-9v])' | sed 's/^/      - /'
    added "$f" | grep -E '^(FROM|[0-9v])' | sed 's/^/      + /'; } || true
done
for f in ${deps[@]+"${deps[@]}"}; do
  { removed "$f" | grep -E '"(engines|node)"|requires-python|^go [0-9]|rust-version' | sed "s|^|      - $f: |"
    added "$f" | grep -E '"(engines|node)"|requires-python|^go [0-9]|rust-version' | sed "s|^|      + $f: |"; } || true
done

echo
echo "== Dependency manifests (${#deps[@]}) — read for runtime majors you ship to users"
for f in ${deps[@]+"${deps[@]}"}; do echo "  $f"; done

echo
echo "== Commit-message hints (hints only; the diff decides)"
git log --no-merges --format='%h %s' "$range" -- "$path" \
  | grep -iE 'break|remov|drop|renam|deprecat|migrat|incompatib|require' | head -20 | sed 's/^/  /' || true

echo
echo "== Version strings in manifests"
find "$path" -maxdepth 4 \( -name node_modules -o -name .venv -o -name venv -o -name .git -o -name dist -o -name build -o -name target \) -prune -o -type f \
  \( -name package.json -o -name pyproject.toml -o -name Cargo.toml -o -name VERSION -o -name Chart.yaml \
     -o -name pubspec.yaml -o -name composer.json -o -name '*.csproj' -o -name build.gradle -o -name build.gradle.kts -o -name setup.cfg \) -print 2>/dev/null \
| sort | while IFS= read -r f; do
  case "$f" in
    *.json) v="$(grep -m1 -oE '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$f" 2>/dev/null || true)" ;;
    *) v="$(grep -m1 -E '^\s*version\s*=|^\s*<Version>|^version:|^appVersion:|^[0-9]+\.[0-9]+' "$f" 2>/dev/null || true)" ;;
  esac
  [ -n "$v" ] && printf '  %-50s %s\n' "$f" "$(echo "$v" | sed 's/^ *//')"
done
exit 0
