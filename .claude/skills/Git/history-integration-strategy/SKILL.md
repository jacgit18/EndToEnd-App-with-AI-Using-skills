---
name: history-integration-strategy
description: >
  Decide HOW to fold one branch's commits into another — merge commit (--no-ff),
  fast-forward, squash-merge, or rebase-then-fast-forward — and how to bring a
  branch up to date with its trunk (merge trunk in vs. rebase onto it). A gate:
  it withholds the recommendation until five facts are on the table — whether the
  commits being rewritten are already published/shared, whether the repo or forge
  already mandates a strategy, whether each commit is independently meaningful or
  WIP noise, whether you're integrating a finished branch or syncing an
  in-progress one, and whether the team reads history for archaeology. Fires on
  "merge or rebase", "squash or merge this PR", "merge / squash / rebase", "how
  should I integrate this branch", "my branch is behind main — merge or rebase",
  "squash these commits before merging", "clean up history before the merge",
  "should this be a fast-forward". NOT `commit-and-push` — that stages, writes the
  message for, and pushes a set of changes, and explicitly hands the
  integration-strategy choice here. NOT mechanical merge-conflict resolution —
  no skill does that; stop and report conflicts. NOT `learning-gate` — "explain
  how rebase differs from merge" with no specific integration to decide is a
  learning request, this skill decides a concrete case. NOT `ambiguity-gate` —
  that fires when which branch or which direction is unclear; once that's clear,
  this decides the method. A bare conceptual question ("what is a fast-forward
  merge") is answered directly, no gate.
---

# History integration strategy

The failure this prevents: reaching for a default — always squash, always rebase, always a
merge commit — without checking the two or three facts that actually decide it, and in the
worst case **rewriting commits other people have already pulled**. "Squash it" is wrong when
a branch holds three separately revertible changes; "rebase onto main" is wrong when the
branch is shared; a merge commit is noise for a one-line fix.

This is a **gate**. When someone asks "merge, squash, or rebase?", it does not answer until
the deciding facts are stated. Once they are, it gives one recommendation with the reason,
not a survey of all options.

## When to use

- "I'm about to merge this PR — squash, rebase, or merge commit?"
- "My feature branch is 20 commits behind main. Merge main in, or rebase?"
- "Should I clean up / squash these WIP commits before merging?"
- "Do we want a merge commit here or a fast-forward?"
- "What's the right way to get this long-lived branch back in sync?"

## Out of scope — hand these off

- **Staging, writing the commit message, pushing** — that's `commit-and-push`. It stops
  after `git push` and explicitly defers the integration-strategy choice to this skill;
  this skill decides the method and hands back.
- **Mechanical merge-conflict resolution** — no skill guesses at conflict resolutions. If a
  merge or rebase throws conflicts, stop and report them (same rule `commit-and-push`
  holds).
- **Walking an interactive rebase / history surgery step by step** — this skill picks
  *rebase vs merge vs squash*; it does not narrate `rebase -i`, `reflog` recovery, or
  `filter-repo`. Once the strategy is chosen, executing it is ordinary work.
- **"Explain how rebase differs from merge" with nothing concrete to integrate** — that's a
  learning request; `learning-gate` sets the ceiling. This skill needs a real branch and a
  real target.
- **Which branch, or which direction** is unclear — `ambiguity-gate` first. This skill
  assumes you know what you're integrating into what.
- **`problem-solving-gates` Options Generator** — the integration options are a fixed set of
  four (merge commit / fast-forward / squash / rebase), not an open design space, so its
  "list your own candidate options and a leaning first" rep doesn't apply. The five-fact
  precondition here is the rep. Options Generator's own trigger list names this skill for
  exactly this reason.
- **A bare conceptual question** — "what is a fast-forward merge?" — answered directly, no
  gate.

---

## The precondition

Before recommending anything, get answers to these five. If the user hasn't supplied one,
ask for it and stop — don't assume.

1. **Is any commit you'd be rewriting already published where others could have based work
   on it?** (pushed to a shared branch, in an open PR others are reviewing against, a
   release tag). Rewriting shared history — rebase, squash, amend, force-push — is off the
   table unless every affected person has agreed.
2. **Does the repo or forge already mandate a strategy?** A squash-only merge button, a
   "require linear history" branch-protection rule, a written "no merge commits" (or the
   opposite) convention, a `.gitattributes`/CONTRIBUTING note. If there's a rule, it wins —
   say so and stop.
3. **Is each commit on the branch independently meaningful** — buildable, revertible,
   useful under `git bisect` / `git blame` — **or is it WIP noise?** ("wip", "fix",
   "review comments", "oops", "typo", commits that don't build).
4. **Are you integrating a finished branch into the trunk, or syncing an in-progress branch
   with the trunk?** Different questions: the first is about what trunk history should look
   like afterward; the second is about how to absorb upstream changes with least disruption.
5. **Does the team use history for archaeology** — bisecting, reverting a whole feature as
   one unit, reading the trunk as a sequence of deliberate changes — **or is trunk treated
   as a flat changelog** where one commit per PR is all anyone wants?

Once these are answered, Claude gives **one** recommendation and the reason. It may note a
close second choice in a sentence; it does not lay out all four options and leave the
decision open.

---

## The decision

Apply in order — the first that matches wins.

### A. A mandated strategy exists (Q2)

Follow it. A squash-only merge button, enforced linear history, or a written convention is
not yours to override in a single PR. Say which rule applies and stop.

### B. Rewriting would touch shared history (Q1) and no one has agreed

Rebase, squash, and amend are out. Your options collapse to: **merge the trunk into the
branch** (for syncing) or **a merge commit** (for integrating). Note that the history is
messier than ideal and why that's the correct trade.

### C. Syncing an in-progress branch with its trunk (Q4 = syncing)

- Branch is **private to you** and commits are still malleable → **rebase onto the trunk**.
  Keeps the branch a clean linear delta, no recurring "Merge main" commits. Re-run as
  often as needed.
- Branch is **shared** with others, or already merged into elsewhere → **merge the trunk
  in**. A rebase would force everyone else to recover. Accept the merge commits.
- Either way: if conflicts appear, that's `commit-and-push`'s rule — stop and report, don't
  guess.

### D. Integrating a finished branch into the trunk (Q4 = integrating)

| Commits (Q3) | Team reads history? (Q5) | Recommendation |
|---|---|---|
| WIP noise | either | **Squash-merge** — one coherent commit on trunk, message written from the whole diff. |
| Each meaningful | yes, archaeology | **Merge commit (`--no-ff`)** — keeps the individual commits *and* a merge commit marking the feature boundary, so the feature reverts and bisects as a unit. |
| Each meaningful | no, flat changelog | **Rebase then fast-forward** — replays the clean commits onto the trunk tip, linear, no merge commit. Only if the branch is private (Q1). |
| Exactly one commit, trunk hasn't moved | either | **Fast-forward** — no merge commit for a single change; nothing to mark. |
| Each meaningful, but branch is shared (Q1) | either | **Merge commit** — you cannot rebase; keep the commits, accept the merge node. |

### E. Long-lived branch, badly diverged

If the branch has drifted for weeks and Q1 makes rebase unsafe, the real answer is often
*not* a clever integration — it's to cut a fresh branch from the trunk and re-apply the
work in reviewable pieces. Say so when that's the case.

---

## Output

A short chat block — no file:

```
Integration strategy: <squash-merge | merge commit (--no-ff) | rebase then fast-forward | fast-forward | merge trunk in>

Why: <the one or two preconditions that decided it — e.g. "commits are WIP noise + squash-only
merge button" or "branch is shared, so rebase is unsafe">

Close second: <one line, or "none — this one is clear">

Watch out: <the specific risk for this path — e.g. "don't force-push after; the PR branch is
shared" or "resolve conflicts as they come, don't -X theirs">
```

Then stop. Executing the merge/rebase/squash is ordinary work; a conflict during it is a
stop-and-report, per `commit-and-push`.

---

## Example invocations

> "Feature branch, six commits, half of them are 'fix review comments'. Merging to main today.
> Squash, rebase, or merge?"

Gate: ask Q1 (is the branch shared / PR based-on by anyone?), Q2 (does the repo force
squash or linear history?), Q5 (does the team bisect / revert features as a unit?). With
"private branch, no rule, we don't really bisect" → **squash-merge**, message from the full
diff. With "we revert whole features and each commit builds" → **merge commit**, keep them.

> "My branch is 30 commits behind main, what's the cleanest way to catch up?"

That's Q4 = syncing. Ask Q1. Private branch → **rebase onto main**. Shared branch →
**merge main in**.

> "Can you explain when you'd rebase instead of merge?"

No concrete integration to decide → this is a learning request. `learning-gate` sets the
ceiling; answer conceptually, don't run the gate.

> "Should I merge this?" (unclear which branch into which)

`ambiguity-gate` first — establish the source and target before this skill can decide the
method.

---

## Portability

Repo-agnostic — it reasons about branches and history, assumes no paths. Copy the directory
into another repo's `.claude/skills/`. See `README.md` for where it sits next to
`commit-and-push`.
