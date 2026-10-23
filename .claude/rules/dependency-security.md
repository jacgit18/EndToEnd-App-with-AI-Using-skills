# Dependency security: an agent never installs what you would not install (applies to every project)

<!-- toc -->
## Contents

- [[#The rules]]
- [[#Vet before approving: the checklist]]
- [[#What CI must block]]
- [[#Setup per project]]
- [[#Prerequisites outside the repo]]
- [[#When something is already installed]]
- [[#Enforcers]]
<!-- /toc -->

A dependency is code from the internet that runs with your app's permissions, at install time as well as run time. An AI agent will add a package to finish a task and cannot tell a five-year-old maintained library from a three-day-old typosquat (`react-datepiicker` for `react-datepicker`) that steals environment variables or wallets. This rule adds the security check that `dependency-selection.md` (whether to add one) does not cover.

## The rules

1. **No install without the owner's yes.** An agent never runs `npm install <pkg>`, `pnpm add`, `yarn add`, `pip install`, `uv add`, `poetry add` or edits a manifest to add a package on its own. It names the package, the rung of the ladder that fell short (`dependency-selection.md`) and the vetting result below, then waits for a clear yes in chat. Approval covers that package and version range, not "dependencies" in general.
2. **Name check first.** Type the exact name from the package's own documentation or repository, never from memory or a search snippet. A name one letter off a popular package, a scope you do not recognise, or a package with the right name but a new publisher is refused until checked.
3. **Install without scripts, then look.** Use `--ignore-scripts` (npm, pnpm) for the first install of a new package; run its install script only after reading what it does. Never `curl | sh`, never an install command copied from a README of an unvetted package, never a package fetched from a git URL or tarball URL unless the owner approves that source.
4. **Lockfile is the truth.** Commit it; CI installs with `npm ci` / `uv sync --frozen`; a PR that changes the lockfile without a matching manifest change is suspect. Pin exact versions for anything load-bearing.
5. **Scan automatically on every PR.** The scanners below run in CI and block the merge; the agent does not rely on remembering.
6. **Secrets stay out of reach.** Install and test with the least environment: no production database URL, no deploy keys, no cloud credentials in the shell where a new package first runs.

## Vet before approving: the checklist

Each line is a fact the agent reads and reports, with its evidence label (`evidence-labels.md`). Script: `node scripts/dep-vet.mjs <name>...` (PR kit) prints the registry facts for npm.

| Check | Red flag |
|---|---|
| First published | under 30 days old, or the current owner changed recently |
| Weekly downloads | under about 1,000, or far below a similarly named package |
| Name distance | within 1 to 2 edits of a popular package or one already in the tree |
| Publisher | one unknown maintainer, no linked repository, repository does not match the package |
| Install scripts | `preinstall`, `install` or `postinstall` present (read them) |
| Advisories | any open high or critical (`npm audit`, OSV, GitHub advisories); malware advisories (OSV `MAL-` ids) block outright |
| License | not compatible with the project (record it) |
| Transitive weight | many new packages for a small job (count the delta) |

Two or more red flags, or any malware hit, means refuse and pick a lower rung. One flag means ask the owner with the evidence.

## What CI must block

Every project with a package manifest runs these on pull requests and on a weekly schedule:

- `npm audit --omit=dev --audit-level=high` (or `pip-audit`, `uv audit`): fails on a known high or critical advisory in production dependencies. Dev dependencies are reported; a project with existing dev findings starts non-blocking and ratchets.
- GitHub **dependency review** on PRs: fails a PR that adds a package with a known vulnerability or a disallowed license, and shows the whole delta.
- `dep-vet` on new packages in a PR: fails a package that is brand new, near-zero downloads or a near-name of an existing package, unless the PR body records the owner's approval (`Dependency approval:` line).
- **Dependabot** (or Renovate) for version and security updates, grouped weekly so updates are one PR, not many (`feature-delivery.md`).
- Workflow actions pinned to a version tag at least (a full commit SHA for third-party actions that handle secrets).

## Setup per project

`commit-and-push/pr-kit/install.sh` installs `dependency-scan.yml`, `dependabot.yml` and `scripts/dep-vet.mjs`. Before the first run, turn on **Dependency graph** (and Dependabot alerts and security updates) in the repository's Settings, Code security; until it is on the review job skips itself with a warning annotation (without that it fails with "Dependency review is not supported", even in a public repository: iron-log's first run, 2026-10-21), so a skipped review is visible in the run but the guard is not complete. Then the project's `CLAUDE.md` gets the Definition of done line and the PR template gets the package-delta line. For non-npm stacks name the equivalent (`pip-audit`, `osv-scanner`, `cargo audit`) in the project's `CLAUDE.md`.

## Prerequisites outside the repo

A workflow can pass in review and still fail on its first real PR because it assumes a setting or an identity the code does not show (2026-10-21: the dependency graph was off; the audience check read the triggering actor, not the PR author). When a rule adds or changes a workflow, list in the PR what it needs from outside the repo and check each one:

- Repository settings: dependency graph, Dependabot alerts, required status checks, branch protection, Actions permissions.
- Identities: which PR authors are bots (Dependabot, release bots) and whether each check skips them by PR author, not by the actor that triggered the run.
- Secrets and tokens the workflow reads, and what happens when they are absent (skip with a warning, never silently pass).

Then open a throwaway PR (or re-run on an existing one) and read `gh pr checks` before calling the setup done.

## When something is already installed

If an agent finds a package it did not get approval for, or an advisory or malware hit on an installed one: stop, say so, do not "fix" by upgrading blindly. Report package, version, how it got in (lockfile diff, `git log -S`), whether install scripts ran, and rotate any secret that was present in that environment. Removal and rotation are the owner's call.

## Enforcers

- Install commands: `permissions.ask` entries in `~/.claude/settings.json` (`npm install *`, `npm i *`, `pnpm add *`, `yarn add *`, `pip install *`, `pip3 install *`, `uv add *`, `uv pip install *`, `poetry add *`) so a person approves each one. `npm ci` and the project's own `npm install` with no package stay unprompted.
- CI: `dependency-scan.yml` (audit, dependency review, dep-vet) fails the PR.
- PR kit: the template's package-delta line (`dependency-selection.md`) plus a `Dependency approval:` line.
- Everything else (name check, scripts, secrets) is advisory.

Related: `dependency-selection.md` (whether to add one), `production-access.md`, `rule-enforcers.md`, `definition-of-done.md`.
