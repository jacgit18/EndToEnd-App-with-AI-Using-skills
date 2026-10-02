# Hint Protocol

## Philosophy

The point of hints is **narrowing by layer**, not giving away the fix. A good hint cuts the search space in half; a bad hint is either "the file is `auth.py`" (too much) or "keep looking" (nothing).

## Hint flow

1. **You get the bug count and symptom(s).** *"There are 2 bugs. Symptom: the endpoint times out on large datasets, but works on small ones."*
2. **You hunt independently** for a time (no fixed limit). Use any method: code review, logging, debugger, running tests, git blame.
3. **When stuck, ask for a hint.** *"I can't find where the performance drops. Hint?"*
4. **You get one structured hint** that narrows the layer: *"The bug is not in the API handler. Look at the data layer."*
5. **You continue with the narrowed search.** If you find it, great. If you're still stuck, you can ask the question again and get the answer.

## Hint levels

Hints work by narrowing vertically (which layer) or horizontally (which part of a layer). Give **one** per request, unless the user asks multiple questions.

| Level | Example | When to use |
|-------|---------|------------|
| **Layer** | *"The bug is not in the frontend. Look server-side."* | First hint; widest scope. |
| **Module / file** | *"Look in `database.py`, not the ORM models."* | Second hint if the layer is still too broad. |
| **Function** | *"The bug is in the `get_user_by_id` function."* | Third hint; narrows to code you can reason about. |
| **Specific line** | *"Line 42: the variable name is wrong."* | Last hint before giving the answer. |
| **The answer** | *"The fix: change `quantity * qty` to `price * qty`."* | Only after two hints and an explicit *"I give up"* or *"Just tell me."* |

## Example session

User: *"Set up a debugging exercise with 2 medium-difficulty bugs in finance-dashboard backend."*

[Skill injects bugs and shows symptoms]

User: *"There are 2 bugs. Symptom: the withdrawal endpoint returns 200 but the balance doesn't change. Symptom 2: the job logs 'completed' but transfers never appear in the ledger."*

User: *"I'm going to hunt. Running tests now."* [User runs tests; one passes, one fails with a cryptic error] *"The withdrawal test passes but the job test times out. Where should I look?"*

Hint 1: *"The first bug is in the withdrawal handler. The second is in the async job layer."*

User: *"Found it! Line 28: we have `db.add()` but forgot `db.commit()`. The first bug."*

User: *"Still stuck on the job. It times out but doesn't error. I added logging — nothing prints after the job starts."*

Hint 2: *"The job starts but never completes. Is the async context correct?"*

User: *"Oh! We created the coroutine but didn't await it. Found it."*

[End of drill; user records findings to problem-journal]

## Framing hints

Each hint should:
- **Not name the fix.** Hint at scope, not solution.
- **Point to the method.** *"Try running the test with `-vv` to see the full traceback"* or *"Add logging at this boundary"* helps the user tool up.
- **Respect the user's progress.** If they've narrowed to one file, narrow further (to a function, or a class). Don't send them backwards to a broader search.

## Escape hatch: "Just tell me"

If the user says *"I give up"* or *"Just tell me the answer"*, they get:
1. The file and line(s).
2. The bug (original vs. buggy code).
3. The root cause (in one sentence).
4. Nothing more — no lecture on why they missed it.

Record this to `problem-journal` as a miss. The value is in the reflection, not the speed.

## Ambiguous or degenerate cases

**Symptom is not visible yet:**
User: *"I can't reproduce the symptom. Help?"*

This is not a hint request; they haven't started hunting. Re-explain how to trigger it or ask how far they've gotten. If they're trying the right steps and still can't see the bug, *then* a hint is that it's a silent failure (no error message, just wrong output).

**Too many hints at once:**
User: *"Hints for both bugs?"*

Give one hint per bug, narrowing each independently. The bugs may be in different layers; treat each as its own hunt.

**The user finds a bug but it's not one of the injected ones:**
Praise it as a real improvement (potential drive-by fix), then redirect: *"That's a real bug — add it to your backlog. Now, the injected bugs: symptom is X. Still hunting?"*
