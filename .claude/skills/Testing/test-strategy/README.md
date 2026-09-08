# test-strategy skill

A gated decision for **the test mix of one surface** — which levels exist, what share each
gets, where in the pipeline each runs, whether non-functional testing is in scope, and
whether TDD or BDD fits. Not the coverage percentage, and not the tests themselves. Given
something that needs testing, the skill makes the user state the surface and its seams, the
cost of failure per area, and the pipeline stages that exist before any mix is named, then
writes a test plan and an ADR for the contested calls.

Built from the `Architecture/Testing/` notes — Testing Hierarchy (70/20/10), Testing Stages
Relationship, Unit / Integration vs System Integration / End to End / Smoke / Acceptance
family, Functional and Non-functional Testing, Types of Testing Technique (black/white/grey
box), Data Driven Testing, TDD, BDD, Cucumber vs Gherkin. The cloud-service-emulation and
poorly-testable-artifact notes in `test-levels.md`'s Integration section were added
`2026-09-04` from `Architecture/02. Backing Service Options/Cloud/LocalStack Setup.md`,
`LocalStack Data Persistence.md`, `Containerizing LocalStack Environment.md`, and `Testing
Step Functions.md`.

## Where it sits

```
test-strategy      →  which test levels exist, their effort split, their pipeline stage,
                      non-functional scope, TDD/BDD workflow   (this skill)   → plan + ADR
coverage-policy    →  the coverage % target and whether CI blocks on it     → policy doc
test-practice-gate →  the rep before writing one specific test              → gate, no artifact
```

`test-strategy` and `coverage-policy` are the two halves of "decide how we test": this one
picks *which tests exist and where*, that one sets *how much of the code they must touch*.
They are orthogonal — you can have a tight strategy with a loose coverage number, or vice
versa. Run `test-strategy` first; its plan is `coverage-policy`'s input.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The 7-item gate, challenge-the-framing, output contract. |
| `selection-framework.md` | The 10-step process, worked once the gate is satisfied. |
| `test-levels.md` | Each level — what it buys, what it costs, its failure mode, where it runs — plus the pyramid note and the manual-testing note. |
| `adr-template.md` | The ADR block, for the contested calls only. |

## What it produces

1. A recommendation block in chat (surface, highest failure cost, mix, pipeline placement,
   functional technique + data strategy, non-functional scope, workflow, deferred decisions).
2. A **test plan** at `docs/testing/<slug>.md` — the living document teams work from.
3. An **ADR** at `docs/architecture/decisions/NNN-<slug>.md` for the arguable lines only.

Stops before framework choice, test code, and CI wiring.

## Deliberately out of scope

- Coverage percentage and CI enforcement → `coverage-policy`.
- The rep of writing one specific test → `test-practice-gate`.
- Framework / tool selection (Jest, Playwright, k6, mocking libs) — named, deferred.
- Writing tests, fixtures, or CI config.
- Whether to split into services → `microservices-decision`.
- API protocol / interaction model → `api-interface-style` (this skill's contract-test
  decision consumes that choice).
- CI / E2E infrastructure cost at build volume → `technical-cost-decision`.

## Using it in another repo

Repo-agnostic. Reads `docs/architecture/decisions/` and CI config; writes `docs/testing/`
and `docs/architecture/decisions/`.

```
cp -r .claude/skills/Testing/test-strategy /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `coverage-policy`** — both fire on "how should we test X". The split is
  which-tests-and-where (here) vs what-percentage-and-enforcement (there). Both
  descriptions carry a disclaimer pointing at the other.
- **vs `test-practice-gate`** — that skill gates the rep of writing *one* test ("write
  tests for this function"); this skill decides the *portfolio*. A request naming a
  specific unit under test routes there; a request about the approach for a surface routes
  here.
- **vs `learning-gate`** — the Step 3 "Testing" row defers to `test-practice-gate` for the
  writing rep; strategy questions are an architecture decision and come here (or through
  `problem-solving-gates` Options Generator). Classify intent, then hand off — don't stack
  the learning rep questions on top of this gate.
- **vs `api-interface-style` / `microservices-decision`** — those decide the surfaces and
  their protocols; this skill tests what they produced. Its ADR may reference theirs.
