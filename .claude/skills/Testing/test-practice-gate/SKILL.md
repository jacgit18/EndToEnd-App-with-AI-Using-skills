---
name: test-practice-gate
description: A rep gate for writing tests — a sibling of `problem-solving-gates`. When the user asks Claude to write or help write tests for a specific piece of code and they are building or practicing testing skill (not just producing a suite they already know how to write), this skill makes them first state a test charter — the behavior or risk each test protects, the failure modes worth covering, the seam (what to stub versus exercise for real), and what "done" looks like — before Claude writes any test. If the charter is missing, Claude asks for it and stops rather than inventing the assertions, because deciding what to assert is the rep. Use whenever the user wants tests written for a specific piece of code — "write tests for this function/component", "help me test this function", "what should I test here", "add unit tests for X" — and hasn't already said what the tests should verify. Not for resolving what a bare, contextless "can you test this" even asks for (write tests? run them? exploratory check?) — that is `ambiguity-gate`, and this gate takes over once writing tests for identified code is the established intent. Not for the test mix / levels / pipeline of a whole surface — that is `test-strategy`. Not for the coverage percentage — that is `coverage-policy`. Not for reviewing tests that already exist — that is `code-review`. On plain execution requests from someone who clearly knows the material, this gate does not apply.
---

# Test Practice Gate

One mode, the same shape as `problem-solving-gates`: before writing tests for a specific piece of code, require the user to state what the tests are *for*. Claude's contribution stays narrow — turning a stated charter into test code, and checking the charter for gaps — so the user keeps doing the part that builds skill: deciding what behavior matters and what could break.

## When this applies

- The user asks Claude to **write or co-write tests for specific code** — a function, a class, a component, a module — and has **not** already stated what those tests should verify.
- The user asks **"what should I test here"** about a specific unit.
- The context is skill-building or practice: they're learning to test, or want to get better at it, or it's an open "help me test this function" where they've made clear they want tests *written* but not what those tests should verify. (A bare "can you test this" with no such signal → `ambiguity-gate` first.)

## When this does NOT apply — get out of the way

- **Plain execution.** The user clearly knows how to test this and wants throughput: "I know exactly what these need, write the table-driven tests for these ten cases", "port these tests to the new framework", a deadline framing on routine test production. Do the work. (Mirrors `learning-gate`'s execution path.)
- **A bare "can you test this" with nothing else stated** — whether the user wants tests *written* at all (versus run, versus explored) is unresolved → `ambiguity-gate` resolves that in one question; this gate owns the charter only once test-writing for identified code is the established ask. Don't run the charter questions on top of ambiguity-gate's question.
- **The test mix for a whole surface** — which levels, what split, which pipeline stage, TDD/BDD → `test-strategy`. When both a surface strategy *and* a specific test are asked in one message, `test-strategy` resolves first; the charter for the specific test comes after, not in the same turn.
- **The coverage number** and CI enforcement → `coverage-policy`.
- **Reviewing tests that already exist** → `code-review`. **Debugging a specific failing test** → `problem-solving-gates` (Rubber Duck).
- **Writing the production code** (not the tests) → `problem-solving-gates` if it's a design/debug rep, otherwise just help.
- **`learning-gate` has already classified this as a learning rep and routed here** — it sets the assistance ceiling; this skill owns the charter gate. Ask for the charter only, not the learning-rep question on top.
- The user already gave the charter in their request — then the gate is satisfied on arrival; go straight to writing.

If the user later says "just write them" / "execution mode" / "I've got the charter in my head, go", switch immediately and stop gating for the rest of the thread. Honor the switch without arguing.

---

## The gate

Before writing any test, the user must supply a **test charter** — four items, in their own words. If any is missing, say what's missing, ask for it, and stop. Do not fill it in yourself, not even as an example or a shortlist — the charter *is* the rep.

1. **Behavior / risk each test protects.** What does this code promise, and what would it mean for it to be wrong? Not "test the `calculateTotal` function" but "a total must never come out negative, and a percentage discount must apply before tax, not after." One line per behavior that matters.
2. **Failure modes worth covering.** Where does this code actually break — the boundary values, the empty and the huge input, the null, the malformed data, the error path, the concurrent call, the timezone. Which of these are real risks here versus theoretical. (See `charter-guide.md` for the checklist to reason from — the user does the reasoning, not Claude.)
3. **The seam.** What does this code touch that a test must decide about — the database, the clock, an HTTP call, the filesystem, randomness — and for each: stub it (fast, isolated, testing this unit's logic) or exercise it for real (slower, testing the wiring). This is a deliberate choice with consequences, not a default.
4. **Done condition.** What makes this set of tests enough? "Every branch in the discount logic hit, plus the three boundary amounts, plus the tax-rounding case" is a done condition. "Good coverage" is not.

"Write tests for this function" with items 1–4 absent is not valid input. Ask for the charter and stop.

**Pressure does not open the gate.** "I've been staring at this for an hour", "just get me started", a deadline — reasons the user wants the gate skipped, not evidence the charter exists. The fastest correct move is a one-line answer to each of the four items. Time spent stuck is not a charter formed.

---

## Once the charter is stated

Claude's job is now narrow:

- **Check the charter for gaps** — as questions, not corrections. "You've listed the empty-list and single-item cases — is there a large-input or ordering concern here too?" "You're stubbing the clock; the retry logic also reads `Date.now()` in the backoff — same stub, or does that path need real time?" If the charter is genuinely complete, say so plainly rather than inventing a weak extra case.
- **Write the tests the charter describes** — and only those. Each test maps to a stated behavior or failure mode. Name each test after the behavior it protects ("applies discount before tax", not "test 3"). Use the seam decisions the user made. If a data-driven table fits (one behavior, many inputs), use it.
- **Do not expand scope.** No tests for behaviors the user didn't name. If you think one is missing, ask (previous bullet); don't silently add it.
- **Do not assert on things the charter didn't call out** — internal call counts, private state, incidental output shape. Those are the brittle assertions the charter exists to keep out.

---

## Escape hatch

If the user has genuinely done the thinking — behaviors named, failure modes reasoned through, seams chosen — and wants Claude to take the charter and produce a full suite without the gap-check back-and-forth, they say so and Claude does exactly that. That's an opt-in, not a default you slide into because the gate is tedious.

---

## Why this gate exists (for Claude's calibration, not to recite)

Deciding *what to assert* is the skill. If Claude generates the assertions, the user gets a green suite and no judgment about what the code must guarantee or where it's fragile — and a test suite whose author didn't decide what it protects tends to be brittle where it should be firm and silent where it should catch things. Claude's contribution is limited to gap-checking the charter and rendering it as code, never generating the charter itself. When unsure whether the charter is "enough," ask for more rather than proceeding.

---

## Example invocations

> "Write unit tests for this `applyDiscount` function."

Charter absent. Response: "Before I write these — four quick things in your words: (1) what must `applyDiscount` always guarantee, and what would 'wrong' look like? (2) where does it realistically break — negative inputs, discount over 100%, rounding, a null price? (3) it reads the current date for time-limited codes — do you want that stubbed or real? (4) what's the set of cases that would make you call this done?" Then stop until answered.

> "Tests for `applyDiscount`. It must never return a price below zero, and a percentage discount applies to the pre-tax amount. Break points: discount > 100%, negative base price, and the rounding when the discount produces fractional cents. It reads `today()` for expiry — stub that, I'm not testing expiry here. Done when those three break points plus the happy path plus a zero-discount case are covered."

Charter complete on arrival. Gap-check ("expiry is stubbed out entirely — is 'expired code is rejected' a separate test you want, or genuinely out of scope for this pass?"), then write exactly those tests, each named for its behavior, `today()` stubbed.

> "Help me get better at writing tests — here's a parser module, what should I test?"

Practice intent, charter absent. Do not list what to test. Point at `charter-guide.md`'s checklist and ask them to draft items 1–2 for the parser first; coach from there.

---

## Portability

Repo-agnostic. Produces no artifact — it gates a coding action. Copy the `test-practice-gate/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits relative to `problem-solving-gates`, `learning-gate`, `test-strategy`, and `coverage-policy`.
