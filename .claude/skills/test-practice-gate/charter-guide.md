# Charter Guide

The checklists the **user** reasons from when writing the test charter in `SKILL.md`. Claude uses this to gap-check a stated charter — never to produce one.

---

## Item 1 — behavior / risk each test protects

A behavior is a promise the code makes, stated so that "violated" is obvious. Prompts to find them:

- What does the function's name claim it does? Does it fully do that?
- What must **always** be true of the output regardless of input (an invariant)? "Never negative." "Sum of parts equals the total." "Output is sorted." "Idempotent — calling twice is the same as once."
- What's the ordering or precedence that matters? (discount before tax; validation before persistence)
- What must **not** happen? (no partial write on failure; no PII in the log line; no mutation of the input argument)
- What does a caller depend on that isn't the return value? (a row committed, an event emitted, a cache invalidated)

Each of these is one line in the charter and, later, one named test.

## Item 2 — failure modes worth covering

Walk the checklist, then keep only the ones that are real risks for *this* code:

| Category | Look for |
|---|---|
| **Boundaries** | 0, 1, n-1, n, n+1; empty string / list / map; the max size; just over the limit |
| **Nullish & missing** | null, undefined, absent optional field, empty vs whitespace |
| **Malformed input** | wrong type, wrong shape, extra fields, wrong encoding, injection-shaped strings |
| **Numeric** | negative, zero, very large, floating-point rounding, division by zero, overflow |
| **Time** | timezone, DST transition, leap year/second, clock skew, "now" changing mid-operation, expiry exactly at the boundary |
| **Error paths** | the dependency throws, times out, returns an error status, returns a 200 with an error body |
| **State & order** | called twice, called out of order, called concurrently, stale state from a previous call |
| **Collections** | duplicates, unsorted input, mixed types, one element, huge element |

A charter that lists only happy-path cases is incomplete — say so. A charter that lists every row above for trivial code is over-scoped — also say so.

## Item 3 — the seam

For each thing the code under test touches, the user picks stub or real, knowing the trade:

| Seam | Stub it when… | Exercise it for real when… |
|---|---|---|
| **Database** | testing this unit's logic, not the query | the query/transaction/constraint *is* what could break |
| **Clock / `now()`** | behavior depends on a specific time or elapsed interval | almost never — time is the classic thing to control |
| **HTTP / another service** | testing how this code handles known responses | testing the actual request shape or the integration contract |
| **Filesystem** | the file content is incidental setup | path handling, permissions, or partial-write behavior is the risk |
| **Randomness / UUID** | the output must be deterministic to assert on | testing distribution or uniqueness properties |
| **Environment / config** | isolating from the machine | testing config parsing itself |

Over-stubbing couples the test to the implementation and it passes while the real thing is broken. Under-stubbing makes the test slow and flaky and vague about what failed. The charter records the choice so it's deliberate.

## Item 4 — done condition

A done condition is a finite, checkable list. Good shapes:

- "Every branch in the discount logic, plus the three boundary amounts, plus the fractional-cent rounding case."
- "Each of the four error responses from the payment API mapped to the right domain error, plus one success."
- "The parser round-trips these six representative documents and rejects these four malformed ones with a specific message."

Not done conditions: "good coverage", "enough tests", "the important cases" (which ones?). If the user offers one of those, ask them to enumerate.

The done condition is also the stopping rule — it's what tells Claude which tests *not* to write.
