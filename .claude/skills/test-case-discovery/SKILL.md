---
name: test-case-discovery
description: Conversation for finding which happy, unhappy, and edge test cases exist for a feature, endpoint, or workflow, ending in a prioritized case table, not test code. Triggers: "what should I test for this feature", "what cases am I missing", "did I cover the edge cases". Not test mix (`test-strategy`), writing one test (`test-practice-gate`), or `coverage-policy`.
---

# Test Case Discovery

Given something that needs testing, find the cases worth having. The value is coverage of *thinking* — the categories nobody named — not a long list. The output is a short, justified case table where every expected result has a source.

This skill produces cases, not tests. It stops at the table.

## When to use

- The user is designing tests for a feature, endpoint, workflow, migration, pipeline, or infrastructure module and wants to know what cases exist.
- The user has a draft list or an existing suite and asks what is missing ("did I cover the edge cases", "review these for gaps").
- The user wants a case list drafted from a spec, a diff, or code they hand over.

## When NOT to use

- **Test mix, levels, pipeline stages, TDD/BDD** → `test-strategy`. This skill suggests a level per case in one line; it does not decide the portfolio. When one message asks for both a strategy and the cases ("how should we test it, and what cases"), `test-strategy` resolves first and its questions cover the surface; the case table comes after, not as a second round of questions in the same turn.
- **Writing tests for a specific unit when the user is building testing skill** ("write tests for this function", "what should I test here" about one function) → `test-practice-gate`, which makes the user state a charter first. If both match, that gate owns the turn; don't run discovery on top of it.
- **Coverage number, metric, CI enforcement** → `coverage-policy`.
- **What backs a database-touching test** (real instance, substitute, mock) → `database-test-tooling`.
- **A test failing now** → `debugging-layer-selection` / `problem-solving-gates`.
- **Which faults to inject in chaos/resilience testing** → `failure-mode-analysis`. This skill lists unhappy-path *cases*; it does not rank a failure register.
- **Reviewing test code quality** (naming, structure, flakiness of the code itself) → `code-review`. Reviewing a suite for *missing cases* is this skill.
- **A bare "can you test this" with nothing else** → `ambiguity-gate` first.
- Plain execution where the user already has the cases and wants them written as code — just write them.

## Choosing the mode

Do not open with a mode menu. Infer it:

| Signal | Mode |
|---|---|
| `learning-gate` classed it as a learning rep, or the user says "help me think through", "quiz me", "let's figure out the cases" | **Think together** |
| The user hands over a spec, code, or diff and says "draft the cases", "what should we test", or is clearly time-boxed | **Hand off** |
| The user gives a partial list and asks for gaps | **Mix** — keep their cases as given, draft the gaps in one table with your additions labeled as suggestions, and batch the `open` questions into one list |
| Intent is genuinely unclear | Ask **one** short question: "Do you want to name cases and have me probe, or should I draft and you review?" Then reuse the answer until the user changes it. |

If the user later says "just draft them" or "let's talk it through", switch immediately.

## Think together

Ask one or two questions at a time. Do not dump the category checklist up front.

1. **Pin down the subject.** What does it do, what goes in and out, what does it depend on, what calls it? For infrastructure: which resources, environments, failure domains. If the code or spec is in the repo, read it and show what you found for confirmation instead of asking.
2. **Happy paths — the user first.** Ask for the intended successful flows. Then add any missing, labeled as suggestions.
3. **Unhappy paths — the user first.** Ask for their cases. Then probe only the categories they haven't touched, one or two at a time, from `case-categories.md`. Skip categories that cannot apply to this subject and say you skipped them.
4. **Prioritize.** Impact × likelihood. Note which cases are worth automating and which are not.
5. **Summarize** as the case table below.

## Hand off

- Draft from the code, spec, or description provided.
- List assumptions explicitly, up front.
- Where expected behavior is not specified, **ask** — do not invent. Mark the case `open — needs decision` until answered.
- End with what was deliberately left out and why.
- **If the user hands over a coverage report** (uncovered lines/branches), map each case to the lines it would hit and rank by risk first, coverage yield second. Whether the last stretch is glue/generated code, or the target or exclusions are wrong, is a `coverage-policy` question — flag it, don't decide it.

## Output — the case table

| Case | Type | Setup | Action | Expected result | Source of expected result | Level (suggestion) | Priority |
|---|---|---|---|---|---|---|---|

- **Type:** happy / unhappy / edge.
- **Source of expected result:** `spec`, `user`, `code (as written — confirm intended)`, or `open`. A case with `open` is a question, not a test.
- **Level (suggestion):** unit / integration / e2e in one word. Not a plan — `test-strategy` decides that.
- Mark any case that rests on an assumption (dependency always up, clock in UTC, single writer) in the Setup column with `assumes: …`.

Follow with: assumptions list, open questions, and what was left out.

## Rules

- Expected results come from the spec or the user, never guessed. Reading code tells you what it *does*, not what it *should* do — mark that source `code (as written — confirm intended)`.
- Label Claude's additions as suggestions so the user can accept or reject them.
- Fewer, justified cases beat exhaustive lists. Do not pad with low-value cases; a category with no real risk is skipped, not filled.
- Flag a happy path that hides an assumption (dependency always available, input always well-formed).
- If cases overlap, say so and merge them.
- **When the user says "just fill in the expected results yourself"** (no spec, out of time): keep the proposals, but label each `open — proposed default` and say plainly that none is a confirmed requirement. Offer "accept defaults" — only when the user says it does a proposed default become `user`. Do not present invented status codes or behavior as spec.
- Stop at the table. Do not write test code, fixtures, or a test plan.

See `case-categories.md` for the category checklist and a worked table.

## Example invocations

> "What cases am I missing for the password-reset endpoint? I have: valid email, unknown email."

Fires, think-together: the user named cases first; probe the categories skipped (expired/reused token, rate limiting, malformed input, concurrent resets) and end in the case table with expected results sourced from the spec or the user, else marked open.

> "Here's the spec for the invoice export — draft the test cases."

Fires, hand-off: draft the table from the spec, list assumptions, ask where expected behavior is unspecified.

> "Write the test code for `applyDiscount`" / "Should our integration tests use Testcontainers?" / "Which test levels do we need?"

Does not fire: writing tests is `test-practice-gate`, the DB mechanism is `database-test-tooling`, the level mix is `test-strategy`.

## Routing boundaries (full)

The frontmatter `description` is kept short for the skill listing budget; the full original description is preserved here.
- Use when someone is working out what to test rather than how or how much, "what should I test for this feature", "what cases am I missing", "did I cover the edge cases", "list the test cases for X", "brainstorm test scenarios", "what could go wrong with this endpoint", "review my test plan for gaps", "what do we test for this Terraform module / pipeline / migration".
