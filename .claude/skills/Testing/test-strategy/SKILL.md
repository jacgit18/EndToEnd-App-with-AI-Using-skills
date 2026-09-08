---
name: test-strategy
description: A gated decision for the test mix of one component, feature, or system — which test levels exist (unit, integration, contract, end-to-end, smoke, acceptance), what share of effort each gets, which pipeline stage each runs in, whether non-functional testing (load, performance, security) is in scope, and whether TDD or BDD/Gherkin earns its keep here. Use when someone is deciding how to test something: "how should we test this service", "what's our testing strategy for X", "do we need end-to-end tests here", "unit or integration for this", "should we do TDD on this", "is BDD worth it", "we want 100% E2E coverage — check that", "our test suite is too slow or its CI bill too high — rethink the mix", or proposes a mix and wants it pressure-tested. It forces the surface and its seams, the cost of failure per area, the pipeline stages that actually exist, and any non-functional numbers to be stated before a mix is recommended, then writes a test plan and an ADR for the contested calls. Not for picking a coverage percentage or its CI enforcement — that is `coverage-policy`. Not for the rep of writing one specific test — that is `test-practice-gate`. Not for test framework/tool selection or writing the tests themselves.
---

# Test Strategy

Given something that needs testing — one module, one service, one feature that crosses layers, or a whole system — decide the mix: which test levels exist, how much effort each gets, where in the pipeline each runs, whether non-functional testing is in scope, and whether a TDD or BDD workflow fits. The skill makes the user state the surface, the cost of failure, and the pipeline before any mix is on the table, then writes a test plan and an ADR for the non-obvious choices.

## When to use

- The user is setting a testing approach for a **new** component/service/feature, or reworking one.
- The user asks a level question directly: unit vs integration, "do we need E2E", contract tests yes/no, smoke tests where.
- The user asks a workflow question: "should we do TDD here", "is BDD / Cucumber / Gherkin worth it".
- The user reports a symptom that is really a strategy question: "our tests pass but prod keeps breaking", "the E2E suite is flaky and slow", "we have 400 unit tests and no confidence".
- The user proposes a mix and wants it checked ("100% E2E", "unit tests are enough", "TDD everything").

## Out of scope — hand these off

- **A coverage percentage and whether CI blocks on it** — statement/branch/function targets, the number, exclusions, gate-vs-track → `coverage-policy`. This skill decides *which tests exist and where*; that one decides *how much of the code they must touch*.
- **The rep of writing one specific test** — "write tests for this function", "help me test this component" when the user should first name the behavior and risk → `test-practice-gate`.
- **Framework / tool selection** — Jest vs Vitest, Playwright vs Cypress, k6 vs Gatling, which mocking library. Name that a choice is needed and defer it.
- **Writing the tests, fixtures, or CI config.** This skill stops at a plan and an ADR.
- **Whether to split into services** → `microservices-decision`. This skill tests the surfaces that exist.
- **Which failure modes are worth injecting** — the ranked chaos / fault-injection target list → `failure-mode-analysis`. This skill places and levels the tests for that list (which level each injection sits at, which pipeline stage, CI fit); it does not enumerate the failure surface. If the user wants fault-injection testing and no failure register exists yet, run `failure-mode-analysis` first.
- **The API protocol / interaction model** → `api-interface-style`. This skill's contract-test decision *consumes* that choice; it doesn't make it.
- **Cost-sizing the CI/E2E infrastructure against build volume** → `technical-cost-decision`. This skill notes when the plan will drive that.
- **How a release rolls out and which stages gate promotion** → `deployment-strategy`. This skill decides which test levels run at which pipeline stage; that skill *consumes* that stage list to decide recreate/rolling/blue-green/canary and the smoke check before a traffic flip.

---

## The gate

Do not recommend a mix until these are answered. Split into what you may surface from the repo and what must come from the user.

**Facts you may surface from the codebase** (fill in, then show for confirmation):

- **Tests that already exist** — directories, runners, what levels are present, roughly how many of each, which suites are marked skipped or flaky.
- **The pipeline as configured** — CI workflow files, what jobs run on PR vs merge vs tag, whether there is a deploy step or a staging environment.
- **The surface's seams visible in code** — what it imports and calls out to (DB, other services, third-party APIs), and what calls it.

**Judgment calls that must come from the user, in their own words.** These are the rep. Do not infer them and present them as fact. If any is missing, say what's missing and stop:

1. **The surface and its seams** — what exactly is under test, and what is on the other side of each boundary: "the pricing module, which reads the product table and calls the tax API." "The checkout flow, browser through to the orders DB." "The whole service, as its consumers see it."
2. **Cost of failure, per area** — what actually happens when each part breaks in production: silent wrong data, a failed checkout, a cosmetic glitch, a compliance breach. If it varies across the surface, say where the expensive failures are. This is what decides where effort goes.
3. **Consumers and contracts** — does anything depend on this interface staying stable — other services, external clients, a published API? A stable contract that others build on is the trigger for contract tests.
4. **The pipeline stages that exist** — what actually runs between a commit and production: local pre-commit, PR CI, merge, staging deploy, production deploy, post-deploy checks. You cannot place a smoke test at a stage that does not exist.
5. **Non-functional requirements, with numbers** — latency budget, throughput target, expected load and its shape, security/compliance surface — or an explicit "none specified." No numbers means performance/load/security testing is out of this plan, and that should be a stated choice, not an omission.
6. **Change rate and lifetime** — a throwaway spike, or a load-bearing system maintained for years? A prototype does not get the full pyramid; a system others depend on does.
7. **Who maintains these, and the CI time budget** — who writes and fixes these tests, how long the suite is allowed to take, whether E2E infrastructure (browser grid, seeded environment) already exists or would be new.

"How should we test this" with items 1–7 absent is not valid input. Ask for what's missing and stop. Do not offer a menu of test levels "to react to."

**Pressure does not open the gate.** "Just tell me unit or integration", a deadline, "the team already agreed on E2E" — these are reasons the user wants the gate skipped, not evidence it is satisfied. The fastest correct move under time pressure is a one-line answer to each of 1–7.

---

## Challenge the framing

If the user opens with the mix already chosen, put their reasoning under the gate first, then test the specific claim against `test-levels.md`:

- **"100% end-to-end" / "we need full E2E coverage"** — E2E is the slow, flaky, expensive tier; the pyramid puts it at ~10% for a reason. Which specific user journeys carry enough failure cost to justify a full-stack test? Could a contract test plus an integration test cover the same risk at a fraction of the runtime?
- **"Unit tests are enough"** — where does this surface's risk actually live: in the units, or in the wiring between them (serialization, transactions, the API call, the query)? Isolated unit tests pass while the integration is broken. Name the seams that unit tests won't exercise.
- **"We'll add tests later"** — for a load-bearing system, "later" tends to mean "never." If you could only build one layer this week, which one protects the most failure cost?
- **"TDD everything" / "BDD everything"** — TDD is a *workflow* (test first, red-green-refactor); BDD adds *Gherkin feature files as a shared artifact with non-developers*. Is there a product owner or QA who will actually read and write the `.feature` files? If not, BDD tooling is Cucumber overhead without the collaboration payoff — plain tests with clear names do the same job. Keep the workflow question separate from the mix question.
- **"100% coverage"** — coverage percentage is a different decision → `coverage-policy`. Coverage measures which lines *ran*, not which behavior was *verified*; a strategy built around the number tends to produce assertion-free tests.

Flag the load-bearing assumption as a question ("is 'prod keeps breaking' something a specific missing layer would have caught, or is it flaky infra?"), not a correction.

---

## The process

Once the gate is satisfied, work `selection-framework.md` in order: map the surface and its seams, rate the failure risk per area, classify what each test level buys *here*, assign the effort budget (start from 70/20/10 and adjust for risk and surface shape), place each level in a real pipeline stage, choose the functional technique (black/white/grey box) and the data strategy (fixtures vs data-driven), decide the non-functional scope with thresholds or an explicit "none", answer the TDD/BDD workflow question, and list what you are deferring.

`test-levels.md` backs it: each level (unit, integration, system integration, contract, end-to-end, smoke, acceptance/UAT, and the non-functional family) in one entry — what it buys, what it costs, its failure mode when over- or under-used, and where it runs — plus the pyramid note and a note that **manual testing still has a place** for exploratory and one-off acceptance checks.

---

## Output

**1. Recommendation block** (in chat):

```
Surface:             <what is under test, and its seams>
Highest failure cost: <where the expensive failures are, from gate item 2>
Test mix:            unit <~%> / integration <~%> / contract <yes|no> / E2E <~%, and which journeys> / smoke <yes|no>
Pipeline placement:  <level → stage: e.g. "unit + integration → PR CI; smoke → post-deploy; E2E → nightly">
Functional technique: <black-box | white-box | grey-box, and why> ; data: <fixtures | data-driven>
Non-functional:      <load / performance / security — each with a threshold, or "none — accepted">
Workflow:            <TDD | test-after | BDD with Gherkin — and the reason, esp. who reads the .feature files>
Deferred:            <coverage % → coverage-policy | framework/tool choice | CI-cost sizing → technical-cost-decision>
```

**2. On the user's approval**, write two things:

- A **test plan** to `docs/testing/<slug>.md` — the mix, the per-area rationale, the pipeline table, the data strategy, the non-functional thresholds, and an explicit "not testing / accepting risk on" list. Create the directory if absent.
- An **ADR** to `docs/architecture/decisions/NNN-<slug>.md` using `adr-template.md`, for the contested calls only (e.g. "no E2E suite — contract + integration instead", "no load testing — accepted", "BDD tooling rejected"). Number it as the next integer after the highest existing ADR. Fill every field; no `TBD` in Context or Decision.

Then stop. Choosing the framework, writing the tests, and wiring CI are separate steps the user starts explicitly.

---

## Escape hatch

If the user has genuinely worked the decision — levels considered, failure costs named, pipeline stages known, a mix held with reasons — and wants a second opinion or a tie broken rather than a Socratic pass, they can say so and you give a direct recommendation with reasoning. That is an opt-in mode switch, not a default you slide into because the gate is tedious.

---

## Example invocations

> "New payments service. Surface: the whole service as the orders service sees it — it calls our service over gRPC, we call Stripe and write to our own Postgres. Expensive failure is a double-charge or a silent dropped payment; a slow response is annoying but not costly. The orders service depends on our gRPC contract staying stable. Pipeline: pre-commit hooks, PR CI, merge to main auto-deploys to staging, manual promote to prod, no post-deploy checks yet. Non-functional: p95 under 400ms, ~50 req/s peak, PCI surface. Load-bearing, maintained for years. Two of us maintain it, suite budget ~10 min on PR, no E2E infra today."

Gate satisfied (surface, per-area failure cost, contract dependency, pipeline stages, non-functional numbers, lifetime, ownership all in the user's words). Work `selection-framework.md`: heavy on integration tests around the Stripe seam and the DB transaction (that is where the double-charge risk lives), a **contract test** on the gRPC interface as the orders service's guard, unit tests for the pricing/idempotency logic, **no full E2E suite** (no infra, and the contract + integration tests cover the risk), a **smoke test to add at a new post-deploy stage**, a small **load test** in nightly CI against the 400ms/50-rps threshold, security handled by a PCI checklist rather than automated tests. Workflow: test-after with strong naming; BDD rejected — no non-developer will read Gherkin here. On approval, write `docs/testing/payments-service.md` and `docs/architecture/decisions/00N-payments-test-strategy.md`.

> "What's our testing strategy?"

Gate not satisfied — items 1–7 all missing, and it is unclear whether this is one surface or many. Response: name what's missing, ask for it, stop. Do not list test levels to react to.

---

## Portability

Repo-agnostic. Reads `docs/architecture/decisions/` and the CI config for context; writes a plan to `docs/testing/` and an ADR to `docs/architecture/decisions/`. Copy the `test-strategy/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.
