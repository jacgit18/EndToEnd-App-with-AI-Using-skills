# Selection Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the test plan and the ADR's Context and Decision.

## 1. Map the surface and its seams

One sentence for the surface, then a list of seams. A seam is any boundary the surface crosses: a database, another service, a third-party API, the filesystem, the clock, a message broker, the UI.

- "The pricing module. Seams: the `products` table (read), the tax API (HTTP), the system clock."
- "The checkout flow. Seams: the browser, our API, the orders DB, the payments service."

Each seam is a candidate for either a mock/stub (isolate and go fast) or a real integration test (exercise the wiring). Step 3 decides which.

If the surface turns out to be several independent things with different consumers and failure profiles, stop and split — each gets its own pass and its own plan.

## 2. Rate the failure risk per area

For each part of the surface, write `cost of failure × likelihood of failure`. Use the user's gate answer for cost; use churn, complexity, and history for likelihood.

| Area | Cost if it breaks | Likelihood | Priority |
|---|---|---|---|
| idempotency / dedup logic | double-charge — severe | high (complex, changes often) | **1** |
| Stripe integration | dropped payment — severe | medium (external, stable API) | **2** |
| response formatting | cosmetic | low | 4 |

The priority column is where effort goes. A cheap-failure, low-churn area gets a token test or none — say so explicitly.

## 3. Classify what each level buys here

For each level in `test-levels.md`, write one line: does it protect a priority-1/2 area on *this* surface, and at what cost?

- **Unit** — protects the idempotency logic (pure, branch-heavy). Cheap, fast, runs on every save.
- **Integration** — protects the Stripe seam and the DB transaction. The double-charge risk lives *between* units, so this is load-bearing here.
- **Contract** — the orders service depends on our gRPC interface; a contract test is its guard against our accidental breaking change.
- **E2E** — would cover checkout end to end, but no infra exists and contract + integration already cover the risk. Buys little here.
- **Smoke** — one call after deploy to confirm the service is up and wired. Cheap insurance.

If a level buys nothing on this surface, say so and leave it out. Completeness is not the goal.

## 4. Assign the effort budget

Start from the pyramid — **~70% unit, ~20% integration, ~10% E2E** — then adjust for what step 2 and 3 found:

- Risk concentrated in wiring (external APIs, transactions, serialization) → shift toward integration. A payments or ETL surface might be 50/40/10.
- A pure-logic library with no seams → closer to 90/10/0, no E2E at all.
- A UI-heavy surface with real user-journey risk → more E2E than the default, but name the exact journeys, not "the app."
- A stable published contract → contract tests become their own slice, carved out of integration.

Write the final split as percentages or rough counts, with one sentence on why it departs from 70/20/10.

## 5. Place each level in a real pipeline stage

Use the stages the user named in gate item 4. Every level needs a home; a test that runs nowhere is not in the plan.

| Level | Stage | Blocks the stage? |
|---|---|---|
| unit + integration | PR CI | yes |
| contract | PR CI (both provider and consumer) | yes |
| E2E (the 3 named journeys) | nightly | alerts, does not block |
| smoke | post-deploy (**new stage to add**) | yes — auto-rollback on fail |
| load test | nightly against threshold | alerts |

If a needed stage does not exist (no post-deploy step for smoke tests), name it as a pipeline change the plan depends on.

## 6. Functional technique and data strategy

- **Black / white / grey box** — black-box (through the public interface, no knowledge of internals) is the default and survives refactors; white-box (asserting on internal branches) is for coverage-driven unit tests of complex logic; grey-box (public interface but seeded internal state) suits integration tests. State which and why.
- **Data strategy** — fixed fixtures for a handful of representative cases, or **data-driven** (one test body, a table of input→expected rows) where the same logic must hold across many inputs and edge cases (boundaries, invalid input, nulls). Name which, and where the test data comes from (inline, factory, seeded DB, anonymized prod sample).

## 7. Non-functional scope

From gate item 5. For each of performance, load, security: either a line with a threshold and where it runs, or an explicit "out of scope — accepted."

- "Load: nightly k6 run, fail if p95 > 400ms at 50 rps."
- "Security: PCI self-assessment checklist each release; no automated security tests. Accepted."
- "Performance micro-benchmarks: out of scope — no latency-sensitive hot path. Accepted."
- "Fault-injection / chaos: inject the top 6 rows of the `failure-mode-analysis` register (tax-API timeout, poison SQS message, mid-handler crash, ...) in a staging soak, weekly. Accepted for the rest." — the *target list* is `failure-mode-analysis`'s output; this step decides the level, environment, and cadence for it. Without a register, "chaos: out of scope — accepted, run FMEA first" is the honest line.

"Not mentioned" is not an answer; "accepted, not testing" is.

## 8. TDD / BDD workflow

Separate from the mix. Answer two questions:

- **TDD (test-first) or test-after?** TDD suits complex logic with a clear spec and unclear implementation; test-after is fine for straightforward glue and exploratory work. This is a team-workflow line, not a per-test rule.
- **Does BDD/Gherkin earn its keep?** Only if a non-developer (product owner, QA, business analyst) will actually read and ideally co-write the `.feature` files. If tests are written and read only by developers, Gherkin + Cucumber is indirection with no collaboration payoff — use plain tests with sentence-style names. Say which, and if BDD: who the non-dev reader is.

## 9. List what you are deferring

- **Coverage percentage and CI enforcement** → `coverage-policy`. This plan says which tests exist; it does not set a number.
- **Framework / tool choice** — runner, assertion library, E2E driver, load tool. Needed; note it.
- **CI-cost sizing** — if the E2E/load infrastructure or the build-minute volume is large enough to matter → `technical-cost-decision`.
- **Writing the tests and fixtures** — the implementer starts this explicitly.

The implementer must not treat "strategy chosen" as "testing done" — this list is what is left.

## 10. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the test plan to `docs/testing/<slug>.md` and, for the contested calls only, the ADR from `adr-template.md` to `docs/architecture/decisions/NNN-<slug>.md`.
