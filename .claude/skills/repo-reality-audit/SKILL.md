---
name: repo-reality-audit
description: Read-only whole-codebase check that the repo's docs/ADRs/CI claims are still true now, and that the build/test suite actually runs clean. Triggers: "does this repo still match its docs", "are our ADRs still accurate", "does the test suite actually pass", "is our CI real or just documented". Bare "audit my codebase" is `ambiguity-gate` first. Not one diff (`code-review`), one change (`change-surface-audit`), or the skill catalog (`catalog-drift-audit`).
---

# Repo Reality Audit

Docs and ADRs describe a system's intent. Code is what actually runs. No sibling skill closes
that loop by executing commands and diffing claims against the current tree —
`code-review` reads one diff, `change-surface-audit` reasons about one proposed change before
it happens, `spec-drift-gate` checkpoints one tracked build against its own spec, `sync-catalog`
is scoped to a skill catalog. This skill is a **procedure, not a gate**: it withholds
nothing, runs two checks against a whole codebase as it stands right now, and reports.

It never fixes anything and never judges security, error-handling, structure, or observability
quality — those findings route to the specialist that owns them. It answers exactly two
questions: **does the repo's documentation still match its code, and does the repo actually
build/test/run clean when you try it.**

## Step 1 — Scope

Ask if unstated: **which repo or directory**, and whether the scan is the whole tree or one
deployable unit inside a monorepo (an `apps/api/`-style subdirectory). This is read +
execute only — any command run (test suite, linter, build) must not mutate committed state.
Running tests/migrations against a throwaway or already-running dev DB is fine; never run
destructive commands, never touch git, never open a PR.

## Step 2 — Check 1: doc/ADR-vs-reality drift

1. Find the ADR directory (`docs/architecture/decisions/`, or search for "ADR"/"decision" if
   not obvious) and any docs describing testing, CI, or how to run the system (`README.md`,
   `docs/testing/*`, `CONTRIBUTING.md`).
2. Extract concrete claims from each: named tools ("we use ruff"), named mechanisms ("JWT
   auth", "webhook delivery"), named files/paths ("see `.github/workflows/ci.yml`").
3. Check each claim against the actual tree — does the file/tool/config exist (`ls`, `grep` in
   dependency manifests), or does a *later* ADR/commit supersede it without the earlier doc
   being updated?
4. See `claim-patterns.md` for the recurring claim shapes and the commands that check each one.

## Step 3 — Check 2: does it actually run

1. Find how the repo says to build/test/run (README, package-manifest scripts, CI config if
   any exists).
2. Execute the test suite(s) as documented. Note the outcome precisely: clean pass, clean fail
   (with reason), or ambiguous failure (hang, unclear error, missing precondition with no
   guard or clear message).
3. Check whether any CI the docs/ADRs claim actually exists (`.github/workflows/`,
   `.gitlab-ci.yml`, etc.) and whether it would run what's claimed.
4. A missing precondition (dev DB not running, env var unset) that fails ambiguously instead
   of naming what's missing is a finding on its own — not just "tests fail."
5. If satisfying a precondition would mean going beyond a read-only check (standing up
   infrastructure, provisioning a database) rather than using one the user already has
   *running*, don't do it — a container or service that exists but is currently stopped still
   counts as "not already running"; starting it is setup, not observation, even though it
   requires no new provisioning. Report the suite as **unable to verify**, name exactly what's
   missing and the exact command that would satisfy it, and stop — don't skip the check
   silently and don't run that command yourself.

## Step 4 — Report

Cited findings only — file:line or the exact command and its output, never an impression.
Rate each:

| Rating | Meaning |
|---|---|
| **Blocker** | A doc/ADR claim that is flatly false right now (claims CI runs X; nothing runs it), or the suite cannot be run at all as documented. |
| **Should-fix** | A claim that was true and quietly went stale (superseded by a later ADR, doc never updated), or the suite runs but fails ambiguously / hangs without a clear precondition message. |
| **Nit** | Small terminology drift that wouldn't mislead a careful reader. |

A claim can earn more than one finding — a doc that's both stale *and* backing a suite that
fails ambiguously is two findings, not one merged into the higher rating.

For every finding, name which existing specialist skill owns fixing it if one does (a missing
CI pipeline is an implementation gap; an ambiguous test failure routes to `test-strategy` or
`database-test-tooling`), or say **"no owner — drift only, needs a doc update."**

End with a one-line verdict: does the repo's story about itself currently hold up, or not.

**Hand off, then stop.** This skill never opens a PR, never edits docs, never fixes the suite.
Offer the next step in one line.

## Never

- Report a broad security / structure / error-handling / observability critique — that is the
  six-dimension audit this skill deliberately is not. Redirect to the owning specialist.
- Run destructive commands, mutate git state, or touch anything beyond reading and executing
  the documented build/test commands.
- Judge whether a design decision was *right* — only whether the repo's current claims about
  itself are *true*.
- Report a claim's status without citing the doc line and the command/`ls`/`grep` output that
  checked it.

## Escape hatch

If the user only wants one check, do that one and say the other was skipped. If the repo has
no ADRs or docs describing mechanisms at all, Step 2 is "no evidence found — nothing to check
drift against," not a finding. If the test suite genuinely can't be run in this environment
(no access, no runtime), say so and stop rather than guessing an outcome.

## Example invocations

> "Does this repo still match its own docs?"

Applies. Both checks run.

> "Check our ADRs are still accurate."

Applies, Step 2 only — say Step 3 was skipped unless they also want the run check.

> "Review this PR for bugs."

Does not apply — that's `code-review` (one diff).

> "What could this schema change break?"

Does not apply — that's `change-surface-audit` (one proposed change, pre-flight).

> "Is our test suite well-designed — right mix of unit/integration?"

Does not apply — that's `test-strategy` (mix decision, not execution/drift).

> "Audit whether our skill catalog is stale — any skills missing README rows or backlog markers left open?"

Does not apply — that's `catalog-drift-audit` (this skill catalog's own hygiene, not the general codebase this skill checks).

## Portability

Needs no repo setup; read + execute only, produces no files. Step 2 assumes an ADR-style decisions directory and a README/docs folder — adjust the search if the repo keeps decisions elsewhere (issue tracker, wiki). Step 3 assumes a documented test-run command; if there is none, say so and stop.

Depends on: `change-surface-audit`, `spec-drift-gate`, `test-strategy`, `observability-strategy`, `database-test-tooling`, `catalog-drift-audit`, `ambiguity-gate`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: no `ambiguity-gate` and the ask is a bare "audit my codebase" → ask one question: docs-vs-code drift and does-it-run (this skill), or a quality review; no specialist for a finding outside the two checks → name the concern (security, structure, observability) and leave it unjudged.

## Routing boundaries (full)

- Use when someone wants a read-only, whole-codebase check that the repo's docs/ADRs/CI claims
  are still true, and/or that the build/test suite actually runs clean right now.
- NOT `code-review` — diff-scoped correctness/quality review.
- NOT `change-surface-audit` — pre-flight blast-radius audit of one proposed change.
- NOT `spec-drift-gate` — checkpoints one tracked, spec-gated build against its own spec
  mid-build.
- NOT `sync-catalog` — this skill catalog's own consistency only.
- NOT `catalog-drift-audit` — this skill catalog's own periodic hygiene pass, not general repo
  claims.
- NOT `repo-scanner` — maps a repo's structure; doesn't execute commands or judge claims. "Map
  this repo and tell me if anything's broken" chains both: repo-scanner maps, this skill
  verifies build/test/doc claims.
- NOT a bare "audit my codebase"/"audit this repo" with no scope stated — that's unstated
  scope for `ambiguity-gate` to resolve first, not this skill's trigger.
- NOT `security-review`, `code-review`, `observability-strategy`, `test-strategy` — this skill
  hands findings to them; it never does their job itself.
