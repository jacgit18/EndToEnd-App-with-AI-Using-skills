# Policy Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the policy document.

## 1. Segment the codebase

Split the scope into segments that deserve different policies. The axes, in priority order: **business criticality**, **change frequency**, **complexity**, **expected lifespan** (from `Code Coverage Best Practices.md`).

| Segment | Criticality | Churn | Verdict |
|---|---|---|---|
| `core/billing` | money path — a bug costs revenue | weekly | highest bar |
| `src/ui` | ordinary app code | moderate | reference bar |
| `src/experiments` | short-lived spikes | high, then deleted | low / none |
| `gen/`, `vendor/` | not our code | n/a | excluded |

If the whole scope is genuinely uniform, one segment is fine — but say so deliberately, don't skip the step.

## 2. Pick the metric per segment

From `coverage-metrics.md`:

- **Statement / line** — the floor. Cheap, universal, coarse. Fine as the only metric for ordinary application code.
- **Branch** — for decision-heavy logic (nested conditionals, error handling, business-rule variants). Statement coverage can hit 100% while half the branches never execute; branch coverage is what forces the `else` and the `catch` to be exercised. Use it on the critical, complex segments.
- **Function** — coarse "was this ever called" check. Useful as a secondary signal to catch entire modules with zero tests; weak on its own.

State the metric per segment. It is normal for the critical segment to carry branch coverage and the rest to carry statement.

## 3. Set the target per segment

Anchor to the reference band from `Code Coverage Best Practices.md` (Google's guideline): **60% acceptable, 75% commendable, 90% exemplary.** Then adjust:

- Critical + high churn → aim at the commendable-to-exemplary end (80–90%), on **branch** coverage.
- Ordinary code → 70–80% statement is a healthy, non-gamed target.
- Stable, rarely-touched, low-risk → the reference band's floor or no target; do not spend effort holding a number on frozen code.
- Short-lived → no target.

Two rules from the note:
- **Do not chase the top.** Moving a segment from 90%→95% is low value. Moving one from 30%→70% is high value. Point the target at the low segments.
- **The number is not the point — what's uncovered is.** The target exists to surface the untested lines for a human to judge as acceptable risk or not, ideally in code review.

Write each target with one sentence on why it isn't just "the average," tied to a gate answer.

## 4. Define exclusions

Coverage measured over the wrong files produces a meaningless number. Exclude, with globs:

- Generated code (`**/*.pb.go`, `**/generated/**`, GraphQL/ORM codegen output).
- Vendored / third-party copied into the tree.
- Database migrations (run once, tested by running).
- Type-only files, interface/DTO declarations with no logic.
- Bootstrap / `main` / wiring entry points that only compose other (tested) code.
- Test files themselves, fixtures, mocks.

Everything not excluded is fair game for the target. Record the exclusion list explicitly so the number is honest.

## 5. Choose the enforcement mode and gate basis

**Mode** — from gate item 4:

- **Block merge** — CI fails, the PR can't land. Use when the team wants a hard floor and won't game it. A drop that violates the agreed standard blocks (this is the legitimate use from the note).
- **Report only** — CI posts the number and the diff, code review decides. Use when a hard gate has bred assertion-free tests before, or the team isn't ready.

**Basis** — what the gate measures:

| Basis | Catches | Misses / risk |
|---|---|---|
| **Overall coverage** | whole-codebase decay below a floor | a well-tested PR that adds a big generated file passes; an untested change hides under the average; punishes legacy inheritors |
| **New-code coverage** | untested lines in *this* change | says nothing about the existing body of untested code |
| **Coverage delta** | any PR that drops the number | noisy on tiny denominators; can block for legitimate reasons (deleting a well-tested module) |

The usual good answer: **gate on new-code coverage**, plus a **delta rule** that total may not fall more than a small tolerance. Reserve an overall-coverage gate for a mature codebase already above target. Never a flat "X% overall" gate on a codebase that's below it — that just punishes whoever's holding it.

Write the rule precisely enough to implement: e.g. *"New or modified lines in a PR must reach 80% branch coverage in `core/**`, 75% statement elsewhere. Total repo coverage may not decrease by more than 0.5 percentage points. `gen/**` and `vendor/**` excluded from all measurement."*

## 6. Write the legacy ratchet

If a segment's current coverage is below its target (gate item 3 and 5):

- **Do not** mandate a big-bang backfill unless the user said it's on the table — it's rarely realistic and produces low-value tests.
- Apply the **boy-scout rule**: any file you touch must come out at or above the target; frequently-changing code gets covered fastest because it's touched most.
- Set a **rising floor**: the enforced overall minimum for the segment steps up on a schedule (e.g. 44% now → 55% in Q2 → 70% in Q4), so the number can only move one way, without demanding it all at once.
- Name who reviews progress and when.

## 7. Name the quality check

Coverage is a coverage metric, not a test-quality metric. If gate item 3 showed real defects slipping through *covered* code, or the team has gamed a gate before, name **mutation testing** on the critical segment as the tool that actually measures whether tests catch bugs. Its adoption is a separate decision — flag it, don't design it here.

## 8. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write `docs/testing/coverage-policy.md` (or `docs/testing/<module>-coverage.md`). Add an ADR only if the enforcement decision was contested.
