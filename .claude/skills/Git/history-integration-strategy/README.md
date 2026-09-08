# history-integration-strategy skill

A gate for one decision: **how** to fold a branch's commits into another branch — a merge
commit (`--no-ff`), a fast-forward, a squash-merge, or a rebase-then-fast-forward — and the
related question of how to bring a branch up to date with its trunk (merge the trunk in vs.
rebase onto it). It withholds the recommendation until five facts are stated: whether the
commits being rewritten are already shared, whether the repo/forge mandates a strategy,
whether each commit is independently meaningful or WIP noise, whether you're integrating a
finished branch or syncing an in-progress one, and whether the team reads history for
archaeology. Then it gives one recommendation with the reason — not a tour of all four.

## Where it sits

```
commit-and-push               →  stage, message-from-diff, commit, push        (no artifact; stops at push)
history-integration-strategy  →  pick merge / squash / rebase / ff for an integration   (this skill; chat block, no file)
scripts/git/batch-git-push.sh →  bulk stage/commit/push in fixed-size batches   (script)
learning-gate                 →  classifies intent; its Step 3 "git history / merge-vs-rebase as a concept" row defers here for a concrete case, or answers conceptually itself
```

The boundary that most needs stating: **`commit-and-push` vs this skill.** `commit-and-push`
turns a working tree into commits and pushes them; it explicitly does *not* pick a branching
or integration strategy and points here. This skill decides *how histories combine* and
produces no commits itself. If the ask is "get this committed", that's `commit-and-push`; if
it's "how do these two branches come together", it's this one.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point — when it applies / doesn't, the five-fact precondition, the ordered decision (mandated rule → shared-history safety → sync vs. integrate → the commit-quality table), the output block. |

No companion reference file — the decision fits in `SKILL.md`, matching `commit-and-push`.

## What it produces

No artifact. A short chat block: the chosen strategy, the one or two preconditions that
decided it, a one-line close-second, and the specific risk to watch on that path. Then it
stops — running the merge/rebase/squash is ordinary work, and a conflict mid-way is a
stop-and-report.

## When it does NOT apply

- "Commit and push this" / "write the commit message" → `commit-and-push`.
- A merge or rebase threw conflicts and you want them resolved → no skill does that; stop
  and report.
- "Explain merge vs rebase" with no specific branch to integrate → learning request,
  `learning-gate` sets the ceiling.
- Which branch merges into which is itself unclear → `ambiguity-gate` first.
- "What is a fast-forward merge?" → answered directly, no gate.
- All five facts were already in the request → gate satisfied on arrival; give the
  recommendation.

## Using it in another repo

Repo-agnostic. Produces no files.

```
cp -r ".claude/skills/Git/history-integration-strategy" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` whenever this skill or a sibling's description changes.
Known boundaries to hold:

- **vs `commit-and-push`** — creating/pushing commits vs. deciding how histories combine.
  `commit-and-push`'s "Branching strategy" out-of-scope bullet names this skill; this
  skill's out-of-scope names `commit-and-push` for the staging/message/push half. Neither
  resolves conflicts.
- **vs `learning-gate`** — a request to *understand* merge/squash/rebase in the abstract is
  capped by `learning-gate`; a request to *decide* a concrete integration runs this gate.
  Don't stack both — if there's a real branch and target, this skill owns it.
- **vs `ambiguity-gate`** — `ambiguity-gate` disambiguates *what* is being integrated into
  *what*; this skill takes that as settled and decides the *method*.
