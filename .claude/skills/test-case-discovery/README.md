# test-case-discovery skill

A conversation for finding **which test cases exist** — happy paths, unhappy paths, edge cases — for a feature, endpoint, workflow, or infrastructure module. Ends in a prioritized case table, not in test code. Two modes: **think together** (user names cases first, Claude probes the categories they skipped) and **hand off** (Claude drafts from code or a spec, lists assumptions, asks where expected behavior is unspecified).

Not a pure gate: think-together withholds Claude's cases until the user has offered theirs, but hand-off drafts immediately. The hard rule is that an expected result is never guessed — it comes from the spec or the user, or the case is marked `open`.

## Where it sits

```
test-strategy         →  the mix / levels / pipeline for a surface        → plan + ADR
test-case-discovery   →  which cases exist for a behavior                 → case table   (this skill)
test-practice-gate    →  the rep before writing one test: state the charter
coverage-policy       →  the coverage % target and enforcement
database-test-tooling →  what backs a DB-touching test
learning-gate         →  classifies intent; sets think-together vs hand-off default
```

Discovery answers "what cases", strategy answers "what levels and how much", the practice gate answers "did you decide what this one test protects", coverage answers "how much code must they touch".

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. When it applies / doesn't, mode selection, both flows, the case-table format, the rules. |
| `case-categories.md` | The unhappy-path category checklist, hidden-assumption list, expected-result source labels, and a worked password-reset table. |

## What it produces

A case table: case | type | setup | action | expected result | source of expected result | level (suggestion) | priority — plus assumptions, open questions, and what was left out. No test code, fixtures, or plan.

## When it does NOT apply

- Test mix / levels / pipeline → `test-strategy`.
- Writing tests for a specific unit while building the skill → `test-practice-gate`.
- Coverage number → `coverage-policy`.
- DB test setup → `database-test-tooling`.
- A failing test → `debugging-layer-selection` / `problem-solving-gates`.
- Fault-injection target list → `failure-mode-analysis`.
- Test code quality → `code-review`.

## Using it in another repo

Repo-agnostic, produces no files.

```
cp -r .claude/skills/test-case-discovery /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Boundaries to hold:

- **vs `test-practice-gate`** — the closest overlap. "What should I test here" about one unit from someone practicing → the gate (user states a charter). "What cases am I missing for this feature / endpoint / plan" → here. Never stack the charter questions on the discovery probes. When a stated charter's failure-mode list is thin, the gate's gap-check may point here for a wider sweep only if the user asks for it.
- **vs `test-strategy`** — this skill's level column is a one-word suggestion; strategy owns levels and the pipeline. When one message asks for both, strategy resolves first and the case table follows, not a second round of questions in the same turn. (Interaction test S3 caught this: without the rule, both skills' questions stacked and had to be merged by judgment.)
- **vs `learning-gate`** — learning-gate's intent classification picks the default mode. Don't add its rep questions on top of the think-together questions.
- **vs `failure-mode-analysis`** — that skill ranks faults for injection; this one lists unhappy-path cases. A failure register can feed discovery's dependency-failure category.
- **vs `ambiguity-gate`** — a contextless "can you test this" goes there first.
