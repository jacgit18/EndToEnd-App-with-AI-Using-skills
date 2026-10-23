---
name: commit-and-push
description: Stage, commit, and push work with a message built from the actual diff (imperative subject, why-body, co-author trailer), after a pre-commit sanity pass. Use when "commit this", "commit and push", "write the commit message". Does NOT open PRs, resolve merge conflicts, or rewrite history; merge vs. squash vs. rebase is `history-integration-strategy`; per-file docs are `codebase-file-orientation`.
---

# Commit and Push

Turn "commit this" into a clean commit whose message is actually derived from what changed — not a restatement of the filenames, and not a vague "update code". The message names *what* changed and, when it isn't obvious, *why*.

## When to use

- The user asks to commit, push, or "save this to git".
- The user asks for a commit message to be written for changes already made.
- A unit of work just finished in this session and the natural next step is getting it committed.

## Out of scope — hand these off or decline

- **Pull requests.** This skill stops after `git push`. Opening a PR is a separate, explicitly-started step: on "open a PR", commit and push any uncommitted or unpushed work here first, then open it with `gh pr create` (and merge with `scripts/git/land.sh` only when asked). **Ordering with `history-integration-strategy`:** if the user also wants history cleaned up ("land it without messy history"), run that skill's gate *before* pushing, or ask whether to push first — pushing makes the commits "published" and changes its answer.
  **The description is never hand-written.** Look for `.github/pull_request_template.md`, `scripts/pr-body.mjs` and any workflow that reads `github.event.pull_request.body` (`grep -l pull_request.body .github/workflows/*`). If `scripts/pr-body.mjs` exists, build the body with it (`node scripts/pr-body.mjs --what "..." > body.md`, then `gh pr create --body-file body.md`); it fills the template and ticks the Audience box from the diff, so the audience check passes without the user having to say who sees the change. If the project has a template but no script, fill every section of the template by hand and tick exactly one Audience box. If it has neither, offer to install `pr-kit/` (copy instructions in `pr-kit/README.md`) before opening the PR, as its own PR; it edits `CLAUDE.md`, so a branch that also edits `CLAUDE.md` lands after it, while a branch with no shared file need not wait (`parallel-agent-structure.md`). Then, after opening, read the checks (`gh pr checks`) and report any that failed on the description. (and merge with `scripts/git/land.sh` only when asked). **Ordering with `history-integration-strategy`:** if the user also wants history cleaned up ("land it without messy history"), run that skill's gate *before* pushing, or ask whether to push first — pushing makes the commits "published" and changes its answer.
  **A new package needs the owner's yes first** (`dependency-security.md`): if the diff adds one to a manifest, run `node scripts/dep-vet.mjs --base origin/main`, put the result and a `Dependency approval: <name>` line in the PR, and never commit an install the owner has not approved.
- **Merge conflict resolution.** If a push is rejected for conflicts or the tree has unresolved conflict markers, stop and report it — don't guess at a resolution. Lockfile/additive triage lives in `history-integration-strategy`.
- **History rewriting.** No `rebase`, no `commit --amend` on a pushed commit, no `push --force`. If the user wants history changed, that's a deliberate separate request with its own confirmation. Deciding *whether* to squash or rebase a branch for integration is `history-integration-strategy` (it picks the strategy; it doesn't run the rebase).
- **Branching / integration strategy.** This skill will branch off the default branch when needed (below), but it doesn't design a Git flow or choose how a finished branch folds back in — merge commit vs. squash vs. rebase vs. fast-forward is `history-integration-strategy`.

---

## Process

> The `scripts/git/*` helpers below (`state.sh`, `commit.sh`, `push.sh`, `batch-git-push.sh`)
> are this repo's convenience wrappers. If the skill is used somewhere they don't exist, run
> the plain-git equivalent shown alongside each step — the process is the same either way.

### 1. Read the real state first

Never draft a message from memory of the conversation alone. `scripts/git/state.sh` gives the
snapshot in one call (branch + tracking, staged vs unstaged vs untracked, diffstat, recent
log). Then pull the detail you need:

```bash
scripts/git/state.sh             # one-call snapshot
git diff                         # unstaged changes in full
git diff --cached                # already-staged changes (respect the user's staging)
git log --oneline -10            # recent history — for message convention
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main  # default branch
```

If `git status` shows nothing to commit and nothing staged, say so and stop (unless the request also asks for a version bump: `release-version-calc` writes it first, then commit it).

If the user has already staged a subset of files, treat that as intent — commit what they staged (pass exactly those paths to `commit.sh`, which refuses when the index holds files outside the named paths), and mention the unstaged remainder rather than sweeping it in.

### 2. Branch guard

If the current branch is the default branch (`main` / `master`) **and** the user has not explicitly said to commit directly to it, create a branch first:

```bash
git switch -c <letter>-<slug>   # f feature, b bug, d docs, c chore, p dependencies; e.g. f-commit-push-skill, b-null-check, d-readme
```

The letter is the PR label (`rules/branch-naming.md`); `guard-pr-create.sh` blocks `gh pr create` from a branch that does not follow it. Propose the name from the change itself and say why you're branching. If the user explicitly wants the commit on the default branch, honor that.

### 3. Group the changes

Look at the diff as a whole. If it contains **unrelated** changes (a feature + an unrelated typo fix + a dependency bump), split them into separate commits with their own messages. One commit = one coherent change. Don't over-split a single logical change across files.

### 4. Pre-commit sanity pass

Scan the diff before staging. Stop and flag — don't silently commit — if you see:

- **Secrets / credentials** — API keys, tokens, passwords, private keys, connection strings with real hosts.
- **`.env` files or local config** not already tracked, unless the user clearly wants them in.
- **Large or binary blobs** that look accidental (build output, `node_modules`, media dumps, `*.log`).
- **Stray debug code** — `console.log`, `print()`, `debugger`, `TODO: remove`, commented-out blocks that read as leftovers.
- **Merge conflict markers** — `<<<<<<<`, `=======`, `>>>>>>>` (unresolved ones only; conflicts resolved per the `history-integration-strategy` triage are fine to commit).
- **Unrelated files** swept in by a broad `git add`.

Surface these as a short list and let the user decide. A `.gitignore` addition is often the right fix for the first two.

### 5. Write the message

**Match the repo's existing convention** — check `git log`. If recent messages use Conventional Commits (`feat:`, `fix:`, `chore:`…), follow that. If they're plain imperative subjects, do that. If history is inconsistent or empty, default to a plain imperative subject.

**Subject line:**
- Imperative mood — "Add retry to upload client", not "Added" / "Adds" / "Adding".
- ~50 chars, hard cap 72. No trailing period.
- Specific. "Fix login redirect loop for SSO users" beats "Fix bug".

**Body** (add when the change is non-trivial — skip for a one-line obvious fix):
- Blank line after the subject, then wrap at ~72 columns.
- Say **why**, and what the reader can't infer from the diff — the motivation, the constraint, the thing that was breaking. Not a line-by-line narration of the diff.
- Reference an issue if the user mentioned one (`Refs #123`, `Closes #123`).

**Trailer** — every commit message this skill writes ends with:

```
Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

(Blank line before the trailer; after a body, it's the last block.)

### 6. Confirm, then commit

Show the user the staging plan and the full message(s) before running anything. On approval, if `scripts/git/commit.sh` is present, use it — it stages exactly the paths you name, runs a partial sanity pass on the staged set (`.env`/key files, files over 1 MiB, conflict markers only — you still do the Step 4 checks for content secrets, debug code and unrelated files), appends the trailer, and commits:

```bash
scripts/git/commit.sh -m "<subject>" -m "<body>" -- <specific paths>
```

Equivalent by hand:

```bash
git add <specific paths>
git commit -F - <<'EOF'
<subject>

<body>

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
```

Repeat per commit when the changes were grouped. Never `git add -A` / `git add .`.

### 7. Push

Pushing is outward-facing. If the user's request already included "and push", that's your go-ahead. If they only said "commit", commit and then ask before pushing.

```bash
scripts/git/push.sh                       # current branch → origin, with timeout + retry
git push -u origin <branch>               # first push of a new branch (sets upstream)
```

`scripts/git/push.sh` wraps `git push` with a per-attempt timeout, an HTTP/1.1 fallback, and one retry, so a stalled connection fails fast instead of hanging. It does **not** paper over a real rejection.

If the push is **rejected** (non-fast-forward, protected branch, auth), stop and report the exact error. Don't `--force`, don't auto-`pull --rebase` without the user saying so.

### 8. Report

One tight summary: branch, commit hash(es) and subject(s), and push result (`pushed to origin/<branch>`, or "committed, not pushed").

---

## Large changesets

If there are many unrelated new files (roughly 90+) — a bulk import, a vault sync — a single commit/push is unwieldy. Point the user at `scripts/git/batch-git-push.sh`, which stages, commits, and pushes in fixed-size batches:

```bash
scripts/git/batch-git-push.sh 90 <branch> "<commit prefix>"
DRY_RUN=1 scripts/git/batch-git-push.sh        # preview first
```

Use it for bulk file additions, not for a normal feature change that happens to touch a lot of lines.

---

## Message examples

**Good:**

```
Add exponential backoff to the S3 upload client

Uploads were failing hard on transient 503s during peak hours. Retry
up to 4 times with jitter; give up and surface the original error
after that so callers still see a real failure.

Refs #218

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

```
fix: stop double-counting refunds in the daily revenue rollup

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

**Bad:**

- `Update files` — says nothing.
- `Added new function and fixed some stuff and updated tests` — multiple changes, past tense, vague.
- `WIP` / `.` / `asdf` — placeholder noise (this repo has some; don't add more).
- A body that just lists the changed filenames.

---

## Routing: requests that do not fire this skill

- "Open a PR for this branch" or "merge this PR" is not a commit; opening a PR is out of scope, and merging is `scripts/git/land.sh`, not this skill.
- "Squash or rebase this before merging?" is `history-integration-strategy`; answer nothing here, hand off.
- "Amend the last commit" / "force-push" / "resolve these conflicts" rewrite history or need conflict work; stop and say so.

## Edge cases

- **Nothing staged, nothing changed** — report and stop.
- **Only whitespace / formatter churn** — call it out; the user may want to drop it or commit it separately as `style:`.
- **Pre-existing staged changes you didn't make** — treat them as someone else's (next bullet): do not stage them unless the user says they belong in this commit.
- **Detached HEAD** — stop and report; committing here loses work silently.
- **Wrong branch or someone else's changes** — run `git branch --show-current` and `git status` before staging. "The branch for this task" is the one the user named, or the one this session created or checked out for the work. If it is not, or the tree holds changes you did not make (another session or worktree), stop and ask once, folding the question into the Step 6 plan; never stage them. If plain `git` fails with "must be run in a work tree", `core.bare` is set wrongly: use `git --git-dir=.git --work-tree=. -c core.bare=false <cmd>` and report it; do not edit the config.
- **Pre-push hook fails with timeouts** — check machine load first. Rerun the tests with fewer workers (`--maxWorkers=4`); push with `SKIP_CHECK=1` only after `npm run check` passes cleanly and the user has allowed skipping hooks. See `.claude/rules/test-run-protocol.md`.
- **No `origin` remote** — commit locally, tell the user there's nowhere to push.
- **A pre-commit hook fails** — the commit did not happen. Show the hook's output, fix what it names (formatter, lint, tests) if that is in scope, re-stage those paths, and make a NEW commit; never `--no-verify` unless the user says so, and never `--amend` (the previous commit is not yours to rewrite).
- **Signing fails** (GPG/SSH key unavailable, agent locked) — stop and report the error; don't disable `commit.gpgsign` or pass `--no-gpg-sign` without the user's explicit say-so.

## Portability

Needs only `git` (and `gh` for the PR hand-off). The `scripts/git/*` helpers are this repo's wrappers: when `scripts/git/` is absent, use the plain-git equivalent shown beside each step. The co-author trailer comes from `git config commit-helper.trailer` or the repo's recent history; with neither, ask once rather than invent one. Writes nothing outside the repo.

Depends on: `history-integration-strategy`. If it isn't installed, say so and give the one-line answer inline instead of dropping the hand-off. The load-bearing fallback: no `history-integration-strategy` and the user wants history cleaned up before pushing → say the strategy gate isn't installed, push nothing yet, and ask which strategy they want.

## Routing boundaries (full)

- Use when the user says "commit this", "commit and push", "push my changes", "save this to git", "commit with a good message", "write the commit message", or finishes a chunk of work and wants it in version control.
- It also does not write per-file documentation for newly added modules — `codebase-file-orientation` may offer to author those orientation docs before the commit, and never blocks or delays it.
- Not for deciding the release version before committing a bump ("bump the version and commit it"): `release-version-calc` picks the number and edits the manifests, then this skill commits them.
