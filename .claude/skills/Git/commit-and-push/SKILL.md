---
name: commit-and-push
description: Stage, commit, and push work to GitHub with a commit message built from the actual diff — an imperative subject, a body that says why the change was made, and the required co-author trailer. Use when the user says "commit this", "commit and push", "push my changes", "save this to git", "commit with a good message", "write the commit message", or finishes a chunk of work and wants it in version control. It reads `git status` / `git diff` / recent `git log` first, matches the repo's existing message convention, groups unrelated changes into separate commits, runs a pre-commit sanity pass (secrets, .env files, large binaries, stray debug code, merge markers), branches off the default branch when the user hasn't said to commit straight to it, and confirms the message and push target before doing anything outward-facing. It deliberately does NOT open pull requests, resolve merge conflicts, rewrite published history (rebase / amend / force-push), or decide how a branch's history should be integrated (merge vs. squash vs. rebase vs. fast-forward) — that last one is `history-integration-strategy`. It also does not write per-file documentation for newly added modules — `codebase-file-orientation` may offer to author those orientation docs before the commit, and never blocks or delays it.
---

# Commit and Push

Turn "commit this" into a clean commit whose message is actually derived from what changed — not a restatement of the filenames, and not a vague "update code". The message names *what* changed and, when it isn't obvious, *why*.

## When to use

- The user asks to commit, push, or "save this to git".
- The user asks for a commit message to be written for changes already made.
- A unit of work just finished in this session and the natural next step is getting it committed.

## Out of scope — hand these off or decline

- **Pull requests.** This skill stops after `git push`. Opening a PR is a separate, explicitly-started step.
- **Merge conflict resolution.** If a push is rejected for conflicts or the tree has conflict markers, stop and report it — don't guess at a resolution.
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

If `git status` shows nothing to commit and nothing staged, say so and stop.

If the user has already staged a subset of files, treat that as intent — commit what they staged, and mention the unstaged remainder rather than sweeping it in.

### 2. Branch guard

If the current branch is the default branch (`main` / `master`) **and** the user has not explicitly said to commit directly to it, create a branch first:

```bash
git switch -c <type>/<short-slug>   # e.g. feat/commit-push-skill, fix/null-check
```

Propose the name from the change itself and say why you're branching. If the user explicitly wants the commit on the default branch, honor that.

### 3. Group the changes

Look at the diff as a whole. If it contains **unrelated** changes (a feature + an unrelated typo fix + a dependency bump), split them into separate commits with their own messages. One commit = one coherent change. Don't over-split a single logical change across files.

### 4. Pre-commit sanity pass

Scan the diff before staging. Stop and flag — don't silently commit — if you see:

- **Secrets / credentials** — API keys, tokens, passwords, private keys, connection strings with real hosts.
- **`.env` files or local config** not already tracked, unless the user clearly wants them in.
- **Large or binary blobs** that look accidental (build output, `node_modules`, media dumps, `*.log`).
- **Stray debug code** — `console.log`, `print()`, `debugger`, `TODO: remove`, commented-out blocks that read as leftovers.
- **Merge conflict markers** — `<<<<<<<`, `=======`, `>>>>>>>`.
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

Show the user the staging plan and the full message(s) before running anything. On approval, if `scripts/git/commit.sh` is present, use it — it stages exactly the paths you name, runs the Step 4 sanity checks on the staged set, appends the trailer, and commits:

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

## Edge cases

- **Nothing staged, nothing changed** — report and stop.
- **Only whitespace / formatter churn** — call it out; the user may want to drop it or commit it separately as `style:`.
- **Pre-existing staged changes you didn't make** — ask whether to include them before committing.
- **Detached HEAD** — stop and report; committing here loses work silently.
- **No `origin` remote** — commit locally, tell the user there's nowhere to push.
