#!/usr/bin/env bash
#
# notes.sh — print release-note header + the maturity ladder for a tag.
#
#   scripts/release/notes.sh v0.1.0-pre-alpha.1
#
# The stage is read from the tag's pre-release part (v<semver>-<stage>[.n]).
# A tag with no pre-release part (v1.0.0) is Gold / GA. The change list is NOT
# produced here; the workflow appends GitHub's generated notes after this.
# Also prints, on a final line, "prerelease=true|false" to stderr for the workflow.
set -euo pipefail

tag="${1:?usage: notes.sh <tag>}"
[[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-([a-z-]+)(\.[0-9]+)?)?$ ]] \
  || { echo "bad tag '$tag' (want v1.2.3 or v1.2.3-<stage>[.n])" >&2; exit 2; }
stage="${BASH_REMATCH[2]:-ga}"

# order | key | label | meaning
ladder=(
  "poc|Proof of Concept (PoC)|Is the idea feasible at all? Throwaway code, no users."
  "mvp|Minimum Viable Product (MVP)|Smallest thing that delivers value to a first real user."
  "pre-alpha|Pre-Alpha|Core features being built; incomplete, unstable, internal only."
  "alpha|Alpha|Feature-complete enough to try; known bugs, breaking changes expected."
  "beta|Beta|Feature-complete; wider testing, stabilising, fixing bugs."
  "rc|Release Candidate (RC)|Believed shippable; only blocker fixes allowed."
  "ga|Gold / RTM / General Availability (GA)|Final release for everyone."
  "gamma|Gamma / Delta (optional)|Extra Greek-letter test/rollout phases some teams use after Beta; less common than RC/GA."
)

case "$stage" in
  poc|mvp|pre-alpha|alpha|beta|rc|ga|gamma|delta) ;;
  *) echo "unknown stage '$stage'" >&2; exit 2 ;;
esac
key="$stage"; [[ "$stage" == delta ]] && key=gamma

echo "# ${tag}"
echo
for row in "${ladder[@]}"; do
  IFS='|' read -r k label meaning <<<"$row"
  [[ "$k" == "$key" ]] && echo "**Current stage: ${label}** — ${meaning}" && break
done
echo
echo "## Milestones"
echo
echo "| Stage | Meaning | |"
echo "|---|---|---|"
for row in "${ladder[@]}"; do
  IFS='|' read -r k label meaning <<<"$row"
  mark=""; [[ "$k" == "$key" ]] && mark="◀ you are here"
  echo "| ${label} | ${meaning} | ${mark} |"
done
echo
echo "Tag format: \`vX.Y.Z-<stage>.N\` (e.g. \`v0.1.0-pre-alpha.2\`); no suffix means GA. Everything before GA is published as a GitHub pre-release."
echo
echo "## Changes"
echo

[[ "$stage" == ga ]] && echo "prerelease=false" >&2 || echo "prerelease=true" >&2
