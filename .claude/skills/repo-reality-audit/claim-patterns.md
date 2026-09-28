# Claim patterns — what to check and how

Read once a mechanism claim is found in a doc or ADR and it's time to verify it. Skip straight
to the row that matches; this is a lookup, not a sequence.

## Contents

- CI/pipeline claims
- Named-tool claims (linter, formatter, type-checker)
- Auth/mechanism claims superseded by a later decision
- Test-suite-run claims
- File/path claims

## CI / pipeline claims

**Claim shape:** "CI runs X" (lint, tests, build, deploy) in an ADR, README badge, or
`CONTRIBUTING.md`.

**Check:** `find . -iname '*.yml' -path '*workflows*'` or the platform's equivalent
(`.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`, `azure-pipelines.yml`). No match at
all → the claim is false; the pipeline is documented but doesn't exist (blocker). A file
exists but doesn't run the specific claimed step (e.g. lints but doesn't run the test suite) →
should-fix, cite which step is missing from the actual workflow file.

## Named-tool claims

**Claim shape:** "we use `ruff`/`black`/`mypy`/`eslint`/`prettier`" in an ADR or README.

**Check:** grep the dependency manifest (`pyproject.toml`, `package.json`, `requirements*.txt`,
`Gemfile`, etc.) for the tool name, and check for its config file (`ruff.toml`, `.eslintrc*`,
`mypy.ini`). Listed as a dev dependency with no config and no CI step invoking it is worth a
nit ("declared but unused, or config drifted"); not listed at all despite an ADR committing to
it is a should-fix — the decision was never implemented, or was reverted without updating the
doc.

## Auth/mechanism claims superseded by a later decision

**Claim shape:** an older doc (a test plan, a README section, a comment) still names a
mechanism (JWT, a specific auth flow, a queue technology, a caching layer) that a *later* ADR
replaced.

**Check:** find the ADR sequence (they're usually numbered) and read the most recent one
touching the same subsystem. If it supersedes an earlier decision, the earlier doc — often
one that isn't itself an ADR, so it wasn't part of the ADR chain's own supersession note —
should have been updated and wasn't. Cite both: the stale doc's line, and the ADR that
actually changed the mechanism.

## Test-suite-run claims

**Claim shape:** README or `CONTRIBUTING.md` says "run `<command>` to test" without documenting
a precondition (a database, an env var, a running dependency).

**Check:** run the documented command exactly as written, from a clean state if possible. Three
outcomes:
- **Clean pass** — no finding.
- **Clean fail with a legible message** naming the missing precondition — no finding; that's
  a fast-fail guard doing its job.
- **Ambiguous failure** — a hang, a stack trace that doesn't name the missing precondition, or
  a long timeout before any error — should-fix. Name the actual root cause found (after
  satisfying the precondition, if possible) and note there's no guard telling a new contributor
  what to do.

## File/path claims

**Claim shape:** a doc says "see `<path>`" for a script, config, or reference file.

**Check:** `ls <path>`. Missing → should-fix (or blocker if the whole workflow depends on it,
e.g. a claimed setup script that doesn't exist). Present but stale (last-modified far before
the doc that cites it, or contents that no longer match the doc's description) → should-fix,
cite the mismatch specifically rather than just "looks old."
