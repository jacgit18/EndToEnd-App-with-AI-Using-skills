# Diagnostic Injection

**Group:** Testing  
**Type:** Procedure (not a gate)  
**Live troubleshooting, hypothesis-driven mutation testing**

## How it fits

### Upstream

- **`debugging-layer-selection`** helps you pick a tool (DevTools, logs, profiler). Use that to narrow the layer; when you've formed a hypothesis about the layer, come back here to test it quickly.
- **`problem-solving-gates`** (Rubber Duck mode) helps you reason through a symptom and form hypotheses. Use that first to get to a clear hypothesis; come here to test it without reasoning in circles.

### Downstream

- **`problem-journal`** records bugs you find and root causes. Use it to track the debugging journey (hypothesis → injection → result → insight).
- **When you find the bug:** form a test case (`test-case-discovery`) or a fix and test it.

### No overlap

- **`bug-hunt-drill`** is for practice exercises with injected bugs; this is real troubleshooting.
- **`repo-reality-audit`** checks if the build/tests run; this skill assumes they do and you can reproduce the symptom.
- **`test-case-discovery`** finds cases to test; this skill uses mutation to narrow an issue.

## Skill gates in the Testing group

| Skill | Type | Purpose | Gate |
|-------|------|---------|------|
| `bug-hunt-drill` | Procedure | Practice finding injected bugs (interview prep, skill-building). | None; pure exercise. |
| `debugging-layer-selection` | Procedure | Which tool to use (DevTools, logging, tracer, profiler). | None; routing only. |
| `diagnostic-injection` | Procedure | Test a hypothesis by injecting a mutation (narrow real issues). | None; narrowing only. |
| `test-case-discovery` | Procedure | What test cases exist for a feature. | None; drafting only. |
| `test-strategy` | Gate | Test mix, levels, pipeline stages, TDD/BDD. | Needs prior decision (if any). |
| `test-practice-gate` | Gate | Before writing tests, state a charter (risk, seams, done criteria). | Requires a charter. |
| `coverage-policy` | Gate | Coverage numbers, metrics, CI enforcement. | Needs target % and risk. |
| `database-test-tooling` | Gate | What backs a DB-touching test (Testcontainers, mock, real DB). | Needs test context. |
| `repo-reality-audit` | Procedure | Does the build/test suite actually run, docs match code. | None; audit only. |
| `web-vitals-audit` | Procedure | Poor Lighthouse/CWV number: diagnose and fix. | None; troubleshooting only. |

## Workflow

Typical flow for live troubleshooting:

1. **Reproduce the symptom:** You have a live issue (slow endpoint, wrong data, crash).
2. **Tool selection:** Use `debugging-layer-selection` to pick where to look (DevTools, logs, debugger).
3. **Form a hypothesis:** Use `problem-solving-gates` Rubber Duck to reason through what's wrong.
4. **Test the hypothesis:** Use `diagnostic-injection` to inject a mutation and see if the symptom changes. Repeat if needed.
5. **Root cause:** Once you've narrowed to the right layer and cause, either:
   - Fix it directly and commit.
   - Write a test case (`test-case-discovery`) to catch this class of bug in the future.
6. **Record:** Use `problem-journal` to log the debugging journey (hypothesis → injection → result → fix).

## When diagnostic injection is overkill

- **Simple bugs:** If you can see the bug by reading the code, don't inject. Just fix it.
- **No symptom:** If you can't reliably trigger the issue, mutation testing won't help. Go back to `problem-solving-gates` or `debugging-layer-selection`.
- **Already narrowed:** If you've already pinpointed the exact line (via a debugger or logs), fix it directly.

## Constraints & safety

- **Never push a diagnostic branch.** The mutation is local and temporary.
- **Use `git worktree`:** Keeps the mutation isolated and makes cleanup easy.
- **Mutations are minimal:** One-line changes or early returns, not partial refactoring.
- **The mutation is not the fix.** Testing `return None` on cache retrieval is not the same as fixing the cache key. The real fix addresses the root cause.

## Why this skill exists

- **Debugging can be slow.** Redeploys, log searches, reasoning in circles.
- **Mutations are fast.** Injecting a return early or skipping a line takes seconds. No rebuild, no redeploy, no wait.
- **Hypothesis testing narrows fast.** A changed symptom is strong evidence; an unchanged symptom rules things out.
- **Interleaves with reasoning.** Form a hypothesis (Rubber Duck), test it (injection), refine and repeat.

## Examples

> "The payment endpoint is slow. I think it's the database query. Let me mock the query and see if the endpoint gets fast."

Injects `return []` to skip the database call; reruns the endpoint; if it's now fast, the query is the bottleneck. If it's still slow, look elsewhere.

> "Transactions are inconsistent by timezone. I think the conversion is wrong. Let me skip the conversion and see what happens."

Injects UTC directly (skipping conversion); runs a transaction from a different timezone; if it now works, conversion is wrong. If it's still inconsistent, the issue is elsewhere.

> "The job says it's done but the side effects never happen. I think the async task isn't being awaited."

Injects `return` to skip the await; runs the job; if it returns instantly, the await was missing. If it still takes time, the work is happening elsewhere.

> "I've been debugging this for an hour. What's wrong with my code?"

Does not fire: this is `problem-solving-gates` Rubber Duck first. Once you have a hypothesis, come back here to test it.
