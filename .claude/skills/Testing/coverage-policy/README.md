# coverage-policy skill

A gated decision for **one codebase's or module's coverage policy** — the metric, the target
number, the exclusions, and how CI enforces it (block vs report; overall vs new-code vs
delta). Not which tests exist, and not the tests themselves. Given a codebase, the skill
makes the user state where coverage is now, what kind of code it is, and what has actually
broken before any percentage is named, then writes a policy document.

Built from the `Architecture/Testing/` notes — Code Coverage (the four metrics), Code
Coverage Best Practices (no universal ideal, the 60/75/90 band, gate bases, the boy-scout
ratchet, the checklist trap, mutation testing as the quality check), Test Branch Coverage
(covering every conditional path).

## Where it sits

```
test-strategy      →  which test levels exist, their split, their pipeline stage   → plan + ADR
coverage-policy    →  the coverage metric, target, exclusions, CI enforcement       → policy doc  (this skill)
test-practice-gate →  the rep before writing one specific test                      → gate, no artifact
```

`coverage-policy` runs **after** `test-strategy` — the strategy says which tests exist, this
skill sets how much of the code they must touch. The two are orthogonal: a tight strategy
can carry a loose number and vice versa.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The 5-item gate, challenge-the-framing, output contract. |
| `policy-framework.md` | The 8-step process — segment, metric, target, exclusions, enforcement, legacy ratchet. |
| `coverage-metrics.md` | What each metric measures and misses, the 60/75/90 reference band and its caveats, the three gate bases, the checklist trap. |

## What it produces

1. A recommendation block in chat (scope, segments, metric and target per segment,
   exclusions, enforcement mode and basis, delta rule, legacy ratchet, quality check,
   what's deliberately unenforced).
2. A **policy document** at `docs/testing/coverage-policy.md` (or `<module>-coverage.md`).
3. Optionally an ADR at `docs/architecture/decisions/NNN-<slug>.md` if the enforcement
   decision was contested.

Stops before CI wiring and before writing tests to raise the number.

## Deliberately out of scope

- Which test levels exist and their effort split → `test-strategy`.
- The rep of writing one specific test → `test-practice-gate`.
- Coverage tool selection (Istanbul/nyc, JaCoCo, Coverage.py) — named, deferred.
- Mutation testing adoption — named as the quality check coverage isn't; its own decision.
- Writing tests.

## Using it in another repo

Repo-agnostic. Scans the repo's coverage config for the current number; writes
`docs/testing/coverage-policy.md`.

```
cp -r .claude/skills/Testing/coverage-policy /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `test-strategy`** — both fire on "how should we test X". Split: portfolio and
  placement (there) vs percentage and enforcement (here). Both descriptions carry a
  disclaimer pointing at the other; run `test-strategy` first.
- **vs `test-practice-gate`** — that skill gates the act of writing a test; this one sets
  the aggregate target. "Help me get this file to 90%" that's really "write these tests"
  routes there.
- **vs `learning-gate`** — a "what coverage number is good" question from someone learning
  is still this skill's gate, not a stacked learning rep. Classify intent, hand off.
- **vs `technical-cost-decision`** — not related; coverage enforcement carries no recurring
  bill. If mutation testing's CI compute cost becomes the question, that's a cost decision.
