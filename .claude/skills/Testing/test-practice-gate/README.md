# test-practice-gate skill

A rep gate for **writing tests** — the test-domain sibling of `problem-solving-gates`. When
someone asks Claude to write tests for a specific piece of code *and* they're building or
practicing testing skill, this skill makes them state a **test charter** first — the
behavior each test protects, the failure modes worth covering, the seam (stub vs real), and
the done condition — before Claude writes anything. Deciding what to assert is the rep; if
Claude supplies it, the rep doesn't happen.

Built from the `Architecture/Testing/` notes — Test Setup (define scope and objective,
mock/stub the right seams), Stubbing (isolation vs coupling), Test Cases Guideline (avoid
over-specificity, cover the variability), Causes of Test Failure (bad mock data, wrong
permissions, flaky environment — what a charter's seam decision guards against), Data Driven
Testing, Testing Lifecycle Hooks, Design patterns in testing (AAA).

## Where it sits

```
problem-solving-gates  →  reps for debugging / architecture / understanding   (production-code thinking)
test-practice-gate      →  the rep before writing one test: state the charter   (this skill)
test-strategy           →  the test portfolio for a whole surface              → plan + ADR
coverage-policy         →  the coverage % target and enforcement               → policy doc
learning-gate           →  classifies intent; its Step 3 "Testing" row defers here
```

`problem-solving-gates` explicitly excludes "writing new code from scratch." Test code is
that gap — this skill covers it, with the same shape: a precondition the user's own work
must satisfy, and a deliberately narrow contribution from Claude once it's met.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. When it applies / doesn't, the 4-item charter gate, the narrow post-charter job. |
| `charter-guide.md` | The checklists the **user** reasons from to build a charter — invariants, the failure-mode table, the seam trade-off table, what counts as a done condition. Claude gap-checks against it; never generates from it. |
| `examples/example-charter-required.md` | Charter absent → asked for → satisfied → tests written to it. |
| `examples/example-gate-does-not-apply.md` | Execution intent (framework port) — gate stays out of the way; plus the counter-example where it fires. |

## What it produces

No artifact. It gates a coding action — the output is test code written *to a
user-authored charter*, or a request for that charter.

## When it does NOT apply

- Plain execution — the user knows what these tests cover and wants throughput.
- Test mix / levels / pipeline for a surface → `test-strategy`.
- Coverage number and CI enforcement → `coverage-policy`.
- Reviewing tests that already exist → `code-review`.
- The charter was already in the request → gate satisfied on arrival, write the tests.

## Using it in another repo

Repo-agnostic, produces no files.

```
cp -r .claude/skills/Testing/test-practice-gate /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `problem-solving-gates`** — that skill's three modes are debugging, architecture, and
  understanding *production* code; it excludes writing code. This is the writing-tests case
  it doesn't cover. No overlap in triggers if both descriptions stay precise.
- **vs `learning-gate`** — Step 3's "Testing" row points here for the writing rep. When both
  match, `learning-gate` classifies intent and sets the ceiling; this skill owns the charter
  gate. Don't stack the learning-rep questions on top of the charter questions.
- **vs `test-strategy`** — that skill decides the portfolio for a surface; this gates
  writing one test within it. "How should we test this service" → there. "Write tests for
  this function" → here.
- **vs `coverage-policy`** — "get this file to 90%" that's really "write these tests" routes
  here; the number itself is that skill.
