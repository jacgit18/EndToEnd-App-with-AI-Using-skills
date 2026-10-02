---
name: diagnostic-injection
description: Narrow a real issue by injecting a strategic code mutation to test a hypothesis without redeploying. Triggers: "I think the bug is in X, let me test it", "add a breakpoint or return early here to confirm", "inject a mutation to see if that's the problem". Not `debugging-layer-selection` (which tool), `problem-solving-gates` Rubber Duck (reasoning through symptoms), or `bug-hunt-drill` (practice exercise).
---

# Diagnostic Injection

You have a live issue, a hypothesis about which layer or component is broken, and access to the code. Rather than adding logging (which requires a redeploy) or reasoning in circles, inject a surgical mutation — a return early, a forced miss, a sleep, a null assignment — and observe whether the symptom changes. The change or lack thereof confirms or rules out your hypothesis, narrowing where the real bug lives.

## When to use

- You have a symptom and a hypothesis about the cause ("the cache isn't working", "the queue job never finishes", "the permission check is wrong").
- You've narrowed to a layer or module but not a specific function.
- Adding logging or re-running with a debugger would take too long (a redeploy, a rebuild, or a waiting cycle).
- You want to confirm a hypothesis quickly without reasoning in circles.

## Out of scope — route these instead

- **Choosing which tool to use** (debugger, logs, tracer, profiler) → `debugging-layer-selection`. Use that first; come back here if you want to test a hypothesis faster than the tool allows.
- **Forming a hypothesis about root cause** by reasoning through a symptom → `problem-solving-gates` Rubber Duck. That skill helps you *think through* the bug; this skill helps you *test* a guess you've already formed.
- **Writing test cases** to expose a bug → `test-case-discovery`.
- **A debugging exercise with injected bugs** → `bug-hunt-drill`. That's practice; this is live troubleshooting.
- **The build or test suite is broken** → `repo-reality-audit`.

## The procedure

### Step 1 — Confirm the hypothesis

Before injecting anything, state the hypothesis in one sentence: *"The cache key includes the user ID but not the org ID, so different orgs see each other's cached data."* or *"The coroutine is created but never awaited, so the job exits before the work completes."*

If you can't state it clearly, you're not ready to inject yet. Go back to `problem-solving-gates` Rubber Duck or `debugging-layer-selection` first.

### Step 2 — Pick the injection point

Choose a spot in the code where injecting a mutation would test the hypothesis:

- **Hypothesis:** Cache is returning stale data.
- **Injection point:** Right before the cached value is returned.
- **Mutation:** `return None` (forces a cache miss).
- **Expected result if true:** Performance drops (cache was helping); correctness is OK (shows the backend is correct).
- **Expected result if false:** No change (cache wasn't the problem).

Other examples:

| Hypothesis | Injection point | Mutation | Expected if true | Expected if false |
|---|---|---|---|---|
| Queue job exits before async work completes | Just before `await work()` returns | `return` (skip the await) | Job completes instantly, no side effects | Job still takes time (work was happening) |
| Permission check is bypassed | At the auth check line | Delete/comment the check | Unauthorized user succeeds (auth is broken) | Unauthorized user still fails (auth works) |
| A variable is mutated unintentionally | Where it's assigned | `print(old_value)` before assignment | Old value differs from expected (mutation is happening) | Value is as expected (no unexpected mutation) |
| Timezone conversion is wrong | At the conversion point | Use UTC directly instead of converting | Times match if UTC is correct, differ if conversion is wrong | Result shows conversion was right |

### Step 3 — Create an isolated worktree

Use `git worktree` to create a temporary, isolated branch. The mutation is **never committed or pushed**.

```bash
git worktree add /tmp/diag-<issue> -b diag/<issue>
cd /tmp/diag-<issue>
# make the mutation
# run the test/app
# observe
git worktree remove /tmp/diag-<issue>
```

### Step 4 — Inject and observe

Make the mutation. Keep it minimal — one line changed, one return added, one assignment removed. Run the app or test suite and observe:

- **If the symptom *changes* (goes away, gets worse, or becomes different):** Your hypothesis is gaining credibility. The bug is at this layer or above it. Narrow further: within this function, which path does the mutation affect? Does a second mutation confirm?
- **If the symptom *doesn't change*:** The bug is not here. Rule this layer out and form a new hypothesis. Repeat.

### Step 5 — Cleanup

Delete the worktree. The mutation never reaches version control or the remote.

### Step 6 — Use what you learned

Once you've narrowed to the right layer, you have options:
- Switch to `problem-solving-gates` Rubber Duck to reason through the exact fix.
- Use your debugging tool (`debugging-layer-selection`) with new focus.
- Write a test case (`test-case-discovery`) that will catch this class of bug in the future.
- If you found the bug, fix it and commit.

## Rules

- **Mutations are temporary and local.** Never commit or push a diagnostic branch.
- **Keep mutations minimal.** One line changed is better than three. The goal is isolation, not a full fix.
- **The symptom must be reproducible.** If you can't reliably trigger it, you can't reliably see whether the mutation changed it.
- **Mutations should be *different* from the fix.** A diagnostic mutation forces a behavior to test the hypothesis; the real fix addresses the root cause. Example: injecting `return None` on cache retrieval is not the same as fixing the cache key (which is the real fix).
- **Record your hypothesis and result.** Write it down inline or in a session note so you don't repeat the same test twice. If you want a full post-resolution record with recurrence analysis and verdicts, use `problem-journal` Journal mode once the bug is fixed.

## Example invocations

> "The email isn't being sent. I think the send function is being called but the result is being ignored. Let me inject a return early to see if the job still completes."

Fires. Injects `return` before the send call; runs the job; if the job finishes instantly with no side effects, the hypothesis is right (send was async and fire-and-forget). Then fix: hook up the result to a queue or log.

> "The slow endpoint got worse after the cache refactor. I think the cache is returning the wrong data. Let me force a cache miss and see if latency jumps back to normal."

Fires. Injects `return None` on cache retrieval; reruns the slow endpoint; if latency spikes, cache was helping (cache key or logic is wrong). If latency stays the same, cache is not the culprit.

> "The test is timing out. I think the lock is deadlocking. Let me remove the lock and see if the test finishes."

Fires. Comments out the lock acquisition; runs the test; if it passes, lock contention is the issue (need to redesign locking). If it still times out, lock is not the problem.

> "I'm not sure what's wrong yet" / "Should I use DevTools or add logging?"

Does not fire: first is not ready (form a hypothesis first), second is tool selection (`debugging-layer-selection`).

## Portability

Works on any code you can edit and run locally or on a test environment. Language, stack, and deployment model agnostic. Requires `git worktree` (standard in modern git) and the ability to reproduce the symptom quickly (within seconds).

## References

- `mutation-patterns.md` — real-world examples of mutations by hypothesis (cache, async, permissions, performance) with expected results.
- `README.md` — where this skill sits relative to debugging-layer-selection, problem-solving-gates, and problem-journal; workflow for live troubleshooting.
