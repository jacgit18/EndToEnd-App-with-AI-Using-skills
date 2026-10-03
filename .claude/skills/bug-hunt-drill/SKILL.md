---
name: bug-hunt-drill
description: Interview-style debugging exercise: inject hidden bugs into a temporary worktree, hunt them by symptom and layer, record your findings, then clean up. Triggers: "give me a debugging exercise", "set up a bug-hunting drill", "practice finding bugs", "interview debugging prep". Not `debugging-layer-selection` (which tool), `problem-solving-gates` Rubber Duck (real problem), or `test-case-discovery` (test coverage).
disable-model-invocation: true
---

# Bug Hunt Drill

Interview debugging rounds present an unfamiliar repo and a failing behavior. You have the symptom; you hunt for the root cause. This skill sets up that scenario, runs it safely (isolated branch, no prod risk), and records what you learn.

## When to use

- You want to practice debugging under a time constraint.
- You are preparing for an interview coding round with a "debug this" section.
- You want to measure which debugging methods work best for you (DevTools, logging, breakpoints, tracing) and how fast.
- You want a systematic way to build debugging skill outside your own code.

## Out of scope — route these instead

- **Which debugging tool to reach for** (DevTools, backend observability, network tab, database GUI) → `debugging-layer-selection`. Use that first to narrow the layer; come back here to practice if you want repetition.
- **Thinking through a bug in your own code** → `problem-solving-gates` Rubber Duck. That's synchronous reasoning. This skill is a scored exercise.
- **Testing a hypothesis with a code mutation** (slow endpoint, cache not working) → `diagnostic-injection`. That's hypothesis-driven, real-world troubleshooting.
- **Finding edge cases to test** → `test-case-discovery`.
- **The build or test suite is broken** → `repo-reality-audit`.

## The exercise

### Step 1 — Choose the target and difficulty

1. **Target repository or module:** Your own codebase (e.g., your project's `backend/`), a cloned public repo, or a simplified example. For a first drill, your own code is safer; for interview prep, a repo you've never read teaches the real skill.
2. **Number of bugs:** typically 2–5. Fewer if the surface is small; more if you want to raise difficulty.
3. **Difficulty mix:** choose from:
   - **Easy:** typos, inverted conditionals, `None` vs `False`, obvious off-by-one.
   - **Medium:** missing `await`, stale cache key, wrong variable in a calculation, skipped SQL migration.
   - **Hard:** timezone boundary, race condition, cascading side effect, authorization check buried three layers deep.
4. **Test coverage rule:** do the test suite still pass, or do the bugs break tests? Bugs that tests catch are easier to find; bugs that tests miss are interview-realistic but frustrating.

### Step 2 — Isolated injection

The skill injects bugs into a temporary git worktree on a `drill/*` branch. This branch is **never merged or pushed**.

- Bugs are added as small, surgical diffs.
- The answer key (file, line, fix, reasoning) is saved to a file in the scratchpad, outside the repo.
- The conversation does not know the answers and cannot leak them.
- The worktree is deleted after you finish.

### Step 3 — The hunt

You receive:
- The target code (the worktree is open for you to browse).
- The bug count: *"There are 3 bugs in this codebase."*
- The symptom(s): *"The payment API returns 200 but the transaction never posts to the ledger."* or *"The job runs but outputs are empty."*

You then:
1. Reproduce the symptom (run the app, trigger the workflow, read the logs).
2. Form a hypothesis about which layer the bug is in (frontend, API, database, async job, cache).
3. Narrow down by inspecting code, logs, or adding temporary traces.
4. Ask for hints if you get stuck: *"Is the bug frontend-side or backend-side?"* → *"Backend."* → *"Is it in the handler or the data layer?"* → etc.
5. Find the bug, explain the root cause in your own words, and record it.
6. Move to the next bug.

**Hint protocol:** you get one hint per bug, then the answer if you're still stuck. Hints narrow by layer, not by stating the fix. The goal is measuring your method, not your speed at guessing.

### Step 4 — Debrief

For each bug found:
- **Time taken** (self-reported, not scored, just awareness).
- **Method used** (read code, added logging, used debugger, traced execution, checked tests, etc.).
- **Debugging tool(s)** (`devtools`, `print-debugging`, `breakpoint`, `tracing`, `test-output`, `git-blame`, etc.).
- **Root cause explanation** (in your own words). This is what interviewers score: can you explain *why* the code is wrong and what the correct behavior should be?
- **Confidence** (certain / likely / guessing).

Record each in the debrief as a drill session entry. To save them, the user runs `/problem-journal` (slash-only: you cannot invoke it, and do not recreate its workflow); otherwise they keep their own notes.

### Step 5 — Cleanup

The worktree is deleted. `main` is untouched. The branch never existed in the remote.

## Rules

- **Never merge or push a drill branch.** The exercise is sandboxed. If you accidentally push, delete the remote branch immediately (`git push origin --delete drill/...`).
- **The answer key is off-repo.** If you see the answer key in the conversation, the exercise is spoiled. The skill injects bugs, then steps aside so the conversation can't accidentally leak them.
- **Timeout is optional.** Some interview rounds have a 45-minute clock; most don't. Set a timer if you want one, else work at your pace.
- **Real interviews are messy.** Tests might not catch the bug. The error message might be cryptic. You might need to read a library's source. This exercise includes that noise.

## Example invocations

> "Set up a debugging exercise with 3 bugs in my project's backend. Make them medium difficulty, and I want the tests to still pass."

Fires. Creates a worktree, injects 3 bugs (cache key, missing index, wrong variable) that the test suite doesn't catch, gives you the symptom (slow endpoint, missing records), and steps back for you to hunt.

> "Give me a bug-hunting drill for interview prep. Use a codebase I've never seen."

Fires. Clones a public repo, injects 2–3 bugs, describes the symptom, and hands it over.

> "I found all 3 bugs in 40 minutes. Walk me through what I did well and what I missed."

Fires. Replay and debrief from the recorded entries (or the user's `/problem-journal` entries, if they saved any). This is the reflection phase.

> "The test suite is failing" / "Which debugging tool should I use?"

Does not fire: the first is a real problem (use `problem-solving-gates`), the second is a tool choice (`debugging-layer-selection`).

## Portability

This skill works best with `git worktree` (standard in modern git) and requires a test suite or a way to reproduce the symptom. It's agnostic to language, stack, and repo layout.

Depends on: `debugging-layer-selection`, `problem-solving-gates`, `diagnostic-injection`, `test-case-discovery`, `repo-reality-audit`, `problem-journal`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: `problem-journal` and `repo-reality-audit` are slash-only (`disable-model-invocation`): you cannot invoke them, so ask the user to type `/name` and never recreate their workflow. No `problem-journal` (not installed, or not run) → debrief in chat (per bug: time, method, root cause, confidence) and tell the user `/problem-journal` saves it; the baseline needs no audit skill: run the suite yourself, and if it doesn't run clean before injection → stop and say so, since a drill needs a working baseline (offer `/repo-reality-audit` to find out why).

## References

- `injection-patterns.md` — example bugs by difficulty (typos, missing await, race conditions) with symptoms and context.
- `hint-protocol.md` — how hints work, example conversations, and levels of narrowing.
- `README.md` — where this skill sits relative to debugging-layer-selection, problem-solving-gates, and problem-journal.
