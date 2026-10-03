# Bug Hunt Drill

**Group:** Testing  
**Type:** Procedure (not a gate)  
**Interview prep, debugging skill-building, scored exercise**

## How it fits

### Upstream

- **`debugging-layer-selection`** helps you choose which tool to use (DevTools, backend observability, logs). Use that first to learn the tool; come back here to repeat and measure.
- **`problem-solving-gates`** (Rubber Duck mode) helps you reason through a *real* bug in your own code synchronously. Drill exercises are written in advance and scored.

### Downstream

- **`problem-journal`** records each bug you find (method, time, root cause, confidence). Use it to debrief and track your debugging patterns.
- **`diagnostic-injection`** uses mutation to test hypotheses on *real issues*. That's active troubleshooting; drills are practice rounds.

### No overlap

- **`test-case-discovery`** finds cases to test; drills find bugs already injected.
- **`repo-reality-audit`** checks if the build/tests run; drills assume they do.
- **`code-review`** reviews your code for bugs; drills present bugs for you to find.

## Skill gates in the Testing group

| Skill | Type | Purpose | Gate |
|-------|------|---------|------|
| `bug-hunt-drill` | Procedure | Practice finding injected bugs (interview prep, skill-building) | None; pure exercise. |
| `debugging-layer-selection` | Procedure | Which tool to use (DevTools, logging, tracer, profiler). | None; routing only. |
| `test-case-discovery` | Procedure | What test cases exist for a feature. | None; drafting only. |
| `test-strategy` | Gate | Test mix, levels, pipeline stages, TDD/BDD. | Needs prior decision (if any). |
| `test-practice-gate` | Gate | Before writing tests, state a charter (risk, seams, done criteria). | Requires a charter. |
| `coverage-policy` | Gate | Coverage numbers, metrics, CI enforcement. | Needs target % and risk. |
| `database-test-tooling` | Gate | What backs a DB-touching test (Testcontainers, mock, real DB). | Needs test context. |
| `repo-reality-audit` | Procedure | Does the build/test suite actually run, docs match code. | None; audit only. |
| `web-vitals-audit` | Procedure | Poor Lighthouse/CWV number: diagnose and fix. | None; troubleshooting only. |

## Workflow

Typical flow for interview prep:

1. **Context:** I have a coding round with a debugging phase.
2. **Tool choice:** Use `debugging-layer-selection` to know which tools you'll need (IDE debugger, browser DevTools, logs, profiler).
3. **Drill setup:** Invoke `bug-hunt-drill` with 2–3 bugs at medium difficulty in a repo you've never read.
4. **Hunt:** You get the symptom and the bug count. Find them using the tools you picked in step 2.
5. **Debrief:** Record findings to `problem-journal` (time, method, root cause). Reflect on what worked and what didn't.
6. **Repeat:** Run another drill targeting your weak points (e.g., async bugs, race conditions, timezone boundaries).

For practicing on your own codebase:

1. **Setup:** Invoke `bug-hunt-drill` with 2–3 bugs in your own project's backend.
2. **Hunt:** Find them. This time you know the codebase, so it's easier — good for a first drill.
3. **Debrief:** Record findings.
4. **Compare:** How much faster than an unfamiliar repo? What methods worked best?

## Constraints & safety

- **Never merge a drill branch.** The exercise is sandboxed; if you push, delete the remote branch immediately.
- **No prod risk.** The worktree is temporary and local. No real data is touched.
- **Tests may still pass.** The bugs are real (logic errors), not syntax errors. Some tests may pass; some bugs leave no traces.
- **Hints narrow, don't solve.** You get one hint per bug: layer, file, or method. After two hints, you can ask for the answer.

## Why this skill exists

- **Debugging is learnable.** Interviews test it; real systems need it. Reps help.
- **Drills are measurable.** You can track time, method, and confidence. Over time, you optimize your approach.
- **Interview realism.** You get an unfamiliar codebase, a symptom, and no answer key. That's the real scenario.

## Examples

> "Set up a debugging exercise with 3 bugs in my project's backend. I want to practice using the debugger, so make the bugs subtle (not typos). Let the tests pass."

Injects 3 medium-hard bugs (missing await, race condition, wrong variable) that the test suite doesn't catch. Gives you the symptom; you hunt using breakpoints and tracing.

> "Give me a bug-hunting drill for interview prep. Use a public repo I've never seen."

Clones a public repo (e.g., a simplified web framework, a CLI tool), injects 2 bugs, describes the symptom, and hands it over.

> "I found the first 2 bugs but got stuck on the third. I've spent 20 minutes narrowing to the async layer. Hint?"

Hint: *"The bug is in how the coroutine is created, not how it's awaited. Look for where the task is scheduled."*

> "I give up on the third one."

Answer: *"File: `jobs.py`, line 87. The bug: `tasks = [process(item) for ...]` creates coroutines but doesn't schedule them. The fix: `tasks = [asyncio.create_task(process(item)) for ...]`. Root cause: coroutines are created lazily; you must explicitly schedule them."*

## Dependencies

Needs `git worktree` and a reproducible symptom or test suite. The siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Project-only: not in any plugin (see `plugins/README.md`).
