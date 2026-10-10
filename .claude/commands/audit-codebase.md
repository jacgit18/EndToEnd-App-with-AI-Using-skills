---
description: Read-only codebase audit and hygiene pass for any project. Detects the stack, runs mechanical checks, delegates judgment checks to installed skills, writes one ranked report. Changes no code.
argument-hint: [area-or-path]
allowed-tools: Read, Grep, Glob, Bash, Write, Skill, Agent
---

# /audit-codebase

Audit the current project (or `$ARGUMENTS` if given: a subdirectory or area). **Report only.** Never edit
source, never commit, never push, never install tools, never run anything that mutates state
(no `npm audit fix`, no formatters in write mode, no migrations).

## 0. Resolve paths once

Run `git rev-parse --show-toplevel` and keep the result as ROOT; record `git -C "$ROOT" rev-parse --short HEAD`.
From here on use absolute paths or `git -C "$ROOT"` / `(cd "<abs dir>" && cmd)` in a subshell. Never a bare
`cd`: the shell's working directory persists between calls and drifts. Do not run dependent checks in
parallel calls that each `cd`.

## 1. Detect the stack

Read the manifests at the repo root and one level down: `package.json`, `pyproject.toml`,
`requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml`/`build.gradle`, `Gemfile`, `composer.json`,
`Dockerfile`, `compose.yaml`, `.github/workflows/`. List what you found in one line. Note monorepo
subprojects and audit each separately.

## 2. Mechanical checks (run what applies; read real output, never guess)

For each check: if the tool is not installed, record **"not run: <tool> missing"**. Do not install it.
If a check cannot run, say so; absence of output is not a pass.

| Area | Node | Python | Other |
|---|---|---|---|
| Deps with known vulnerabilities | `npm audit --omit=dev` | `pip-audit` | `govulncheck`, `cargo audit` |
| Unused code / deps | `npx knip` or `depcheck` | `vulture`, `deptry` | per ecosystem |
| Lint / typecheck | project lint script, `tsc --noEmit` | `ruff check`, `mypy`/`pyright` | per ecosystem |
| Tests run at all | project test script | `pytest -q` | per ecosystem |
| Secrets in tree | `git ls-files` + grep for key-shaped strings, tracked `.env*` | same | same |
| Stale deps | `npm outdated` | `pip list --outdated` | per ecosystem |

Also check: lockfile committed, CI exists and covers lint + tests, `.gitignore` covers env files,
dead branches (`git branch -r --merged`), very large tracked files, TODO/FIXME count.

Use the project's own scripts first (`package.json` scripts, `Makefile`, CLAUDE.md commands).
Time-box each command; report a timeout as "not run".

For test runs, report passed / failed / **skipped** counts. If more than ~10% skipped, find the reason
(`-rs` for pytest) and make it a finding: a mostly-skipped green run is weak evidence. Check whether CI
turns those skips into failures.

## 3. Judgment checks (delegate if installed, else use the inline fallback)

| Check | Use if installed | Inline fallback |
|---|---|---|
| Docs / ADRs vs real repo; does build run | `repo-reality-audit` (slash-only: suggest `/repo-reality-audit`, don't invoke) | compare README/ADR claims to manifests and CI; try the documented build |
| Structure map | `repo-scanner` | list top-level dirs and entry points |
| Security | `security-review` / `security-audit` | check auth, input handling, secrets, injection at the boundaries |
| Correctness / cleanup | `code-review`, `simplify` | skim the highest-churn files (`git log --since=90.days --name-only`) |
| Blast radius of hotspots | `change-surface-audit` | note files many others import |

Check which skills exist before calling one (the Skill tool's listing). **Delegations are not optional:**
invoke each installed one (except slash-only ones, which you only suggest) or state in the report why it
was skipped. If a skill is missing, say "skill not installed, used fallback" and run the fallback.
`security-review` and `code-review` review a diff: point them at the highest-risk area (auth, sessions,
input parsing/uploads, rate limiting, SQL built from strings) via a subagent, not just the last commit.
Fallbacks are shallow: label any finding or "clean" verdict that rests only on a fallback as
**shallow check** and list the unreviewed areas under "Not verified". Never block on a missing sibling.
Independent delegations may run in parallel as subagents.

## 4. Write the report

Find the docs root before writing. Check in this order and use the first that applies:
1. The project's CLAUDE.md or `.claude/rules/` says where docs live (e.g. "docs are edited only in <path>").
   Resolve a relative `docs/` for the audited subproject against that path.
2. `~/.claude/CLAUDE.md` names a docs root pattern: try `<root>/Projects/<project>/docs/`, then
   `<root>/<repo-name>/<subproject>/docs/`, then `<root>/<repo-name>/docs/`. Use the first that exists.
3. Else `docs/audits/` inside the project.
Write `<docs dir>/audits/YYYY-MM-DD-codebase-audit.md` (add `-<subproject>` if auditing one of several).
Create `audits/` if needed. Quote paths (they may contain spaces). Say which rule picked the location.
If a previous audit exists in that folder, read the newest one first and mark each finding
**new / still open / resolved**; a finding is resolved only if you re-checked it.

Report shape:

```
# Codebase audit: <project>, <date>
Stack: ...   Scope: ...   Commit: <short sha>
## Summary (3 lines: top risks, overall health, what was not run)
## Findings, ranked
| # | Severity (high/med/low) | Area | Finding | Evidence (file:line or command output) | Suggested fix | Status |
## Checks run / not run
| Check | Result | Notes |
## Delegated skills
Which ran, which fell back.
## Not verified
Anything that needs a human or a tool that was missing.
```

Rules for findings:
- Every finding cites evidence (path:line or the command output). No evidence, no finding.
- Rank by impact on users or data first, effort second. A failing build or a vulnerable runtime dependency
  outranks style.
- Separate **confirmed** from **suspected**. Label suspected ones.
- Do not claim the project is "secure", "compliant" or "clean". Say what was checked and what was not.

## 5. Finish

Reply with the report path, the top 3 findings, and the "not run" list. Offer next steps (fix top item on a
branch, schedule this weekly) but do not start them.
