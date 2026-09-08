# Test Levels

One entry per level: what it is, what it buys, what it costs, its failure mode when over- or under-used, and where it runs. Use this in steps 3–5 of `selection-framework.md` and in "Challenge the framing" in `SKILL.md`.

The levels form a **pyramid**: many cheap fast tests at the bottom, few slow expensive ones at the top. A rough default budget is **70% unit / 20% integration / 10% end-to-end** — a starting point to adjust, not a target to hit.

---

## Unit

**What it is.** Tests one function/class/module in isolation, with its seams stubbed. Milliseconds each, no I/O.

**Buys.** Fast feedback on logic and branches — arithmetic, parsing, state machines, validation, edge cases. Pins behavior so refactors are safe. Localizes a failure to one unit.

**Costs.** Says nothing about whether units work *together*. Over-mocking couples the test to the implementation, so it breaks on refactor and passes on real bugs.

**Failure mode.** A suite of 500 unit tests, all green, while the app is broken because every seam is mocked and no test exercises the real wiring. Or white-box tests asserting on private internals that shatter on every refactor.

**Runs.** Every save (watch mode), every PR. Blocks the PR.

---

## Integration

**What it is.** Tests several units together, or one unit against a real dependency (a test database, a local broker, an HTTP stub server). Seconds each.

**Buys.** Catches what unit tests can't — serialization, transactions, query correctness, connection handling, the actual shape of a third-party response, error propagation across a boundary. On surfaces where the risk lives *between* units (payments, ETL, anything with a DB or external API), this is the load-bearing tier.

**Costs.** Slower; needs a real dependency provisioned and reset between tests. Flakier than unit tests. Harder to pin a failure to a cause.

**Failure mode.** Skipped because "unit tests cover it" on a surface whose bugs are all integration bugs. Or so heavy (full DB seed per test) that the suite takes 20 minutes and people stop running it.

**Cloud-service emulation as the "real dependency."** For a stack built on managed cloud
services (Lambda, IAM, Step Functions, DynamoDB, SQS/SNS), a local emulator (LocalStack is
the common one) fills the same role a test database or local broker fills for other stacks —
a real-enough dependency without a live cloud account or its cost/latency. Two things to get
right: (1) emulator state is ephemeral by default and wiped on restart — deliberately choose
ephemeral-per-run (fine, often preferred, for CI) vs a persisted data directory (needed if a
test suite depends on state surviving across separate local sessions); don't let "why did my
data disappear" become a debugging session. (2) An emulated cloud service is still a step
down from the real one on edge cases (IAM path-constraint enforcement, exact throttling
behavior, and similar provider-specific details are commonly simplified or unenforced) — this
tier catches wiring and logic bugs, not a substitute for hitting the real service at least
once before a first production release of a new integration.

**Layering a poorly-testable artifact (e.g. a Step Functions state machine).** A workflow
defined as JSON/YAML isn't directly unit-testable as code, but the same three-tier split still
applies: **unit** — validate the definition's structure itself (required fields present per
state, every referenced state actually exists, no unreachable/dangling state) without running
anything; **integration** — deploy the definition to the emulator and execute it against a
Task's real (or emulator-backed) dependencies, asserting on the execution result and status;
**system integration / E2E** — the full pipeline against staging. Don't skip the unit tier
because "it's just config" — a syntactically-valid-but-logically-broken state machine (a typo
in a `Next` target, a missing `Catch`) is exactly the class of bug a structural check catches
before a single execution is spent finding it at runtime.

**Runs.** Every PR, usually a separate CI job. Blocks the PR.

---

## System integration

**What it is.** Integration testing one level up: multiple deployed services or subsystems talking to each other, not just one service and its direct dependencies.

**Buys.** Catches cross-service issues — auth propagation, network partitions, version skew, contract drift between teams.

**Costs.** Needs a multi-service environment. Slow, expensive to maintain, ownership is ambiguous when it breaks.

**Failure mode.** Becomes the catch-all "test everything through the whole system" suite — slow, flaky, and blocking, when contract tests would isolate the same risk per pair.

**Runs.** Nightly or pre-release against a staging environment. Alerts rather than blocks.

---

## Contract

**What it is.** Provider and consumer each test against a shared contract (an OpenAPI spec, a Pact file, a `.proto`, a schema). The provider proves it still satisfies the contract; the consumer proves it only relies on what the contract promises.

**Buys.** The guard for a stable published interface. Catches an accidental breaking change *in the provider's own CI*, before it ships, without standing up both sides together.

**Costs.** A contract artifact to maintain and version. Both sides need the discipline to test against it rather than around it.

**Failure mode.** Not adopted, so the provider ships a breaking change and the consumer finds out in production. Or the contract is written once and never updated, so it tests a fiction.

**Runs.** Provider CI and consumer CI, both blocking. The trigger to use it is gate item 3 — someone depends on this interface staying stable.

---

## End-to-end (E2E)

**What it is.** Drives the whole stack the way a user does — a browser through the UI, or a client through the public API — against a fully deployed environment with real (test) data.

**Buys.** Confidence that a complete user journey works: the critical path from login to a completed order, actually exercised. Catches integration gaps nothing below the top of the pyramid sees.

**Costs.** Slowest tier by far. Flakiest — timing, environment drift, test-data setup. Expensive to write and to keep green. A failure tells you *something* is broken, not *what*.

**Failure mode.** "100% E2E coverage" — hundreds of slow flaky tests re-verifying logic that unit tests already cover, a suite nobody trusts, CI runs measured in hours. The fix is to name the handful of journeys whose failure actually costs money and test only those.

**Runs.** Nightly, or pre-deploy for the named critical journeys only. Usually alerts; blocks only for the few journeys that gate a release.

---

## Smoke

**What it is.** A tiny set of checks that the system starts and its core features respond. Binary: pass means "not obviously broken, proceed"; fail means "stop."

**Buys.** Cheap insurance right after a deploy or before a longer test run — catches a bad config, a missing env var, a service that won't boot, a broken health check.

**Costs.** Almost none. The only risk is scope creep into a full regression suite.

**Failure mode.** Grows until it is a 15-minute suite that no longer serves its "quick go/no-go" purpose. Or it does not exist, so a broken deploy is discovered by users.

**Runs.** Post-deploy (add the stage if there isn't one), and as a pre-flight gate before E2E. Blocks promotion; triggers rollback.

---

## Acceptance / UAT

**What it is.** Verifying the system meets the agreed acceptance criteria, judged from the stakeholder's perspective. Functional acceptance = "does it do what was specified end to end"; user acceptance = real users exercising it in a realistic context. Often partly manual.

**Buys.** Confirms the thing built is the thing wanted — a different question from "is the code correct." Formal sign-off before release.

**Costs.** Needs written acceptance criteria and stakeholder time. Manual portions don't scale and aren't repeatable.

**Failure mode.** Treated as the main safety net, so defects that automated tests should have caught land in a slow manual pass late in the cycle. Or skipped, so the team ships something correct that doesn't match the requirement.

**Runs.** Pre-release, against a release candidate. Glues to `pre-acceptance` (in-house alpha) earlier in the cycle.

---

## Non-functional family

Not a single level — a set of checks on qualities rather than behavior. In scope only when gate item 5 gave numbers.

| Type | Asks | Threshold example |
|---|---|---|
| **Performance** | Is a single operation fast enough? | p95 < 400 ms for `POST /checkout` |
| **Load** | Does it hold up at expected volume? | 50 rps sustained, error rate < 0.1% |
| **Stress** | Where does it break, and does it fail gracefully? | degrades, no data loss, recovers at 3× load |
| **Scalability** | Does adding capacity add throughput? | 2× instances → ≥1.8× throughput |
| **Security** | Known-vulnerability and abuse-case checks | dependency scan clean; authz tests on every endpoint |
| **Benchmark** | Has a hot path regressed vs a baseline? | function X within 10% of last release |

**Costs.** Needs a representative environment and a defined baseline. Results are noisy without a controlled setup.

**Failure mode.** Run once before launch, never again, so a regression six months later ships unnoticed. Or specified with no number ("must be fast"), so the test can't pass or fail.

**Runs.** Nightly or per-release against thresholds; benchmarks on every PR touching a marked hot path. Alerts.

---

## Manual testing still has a place

Automation is the backbone, but keep room for:

- **Exploratory testing** — a person poking at a new feature without a script, finding what nobody thought to specify.
- **One-off acceptance checks** — a stakeholder confirming a UI feels right.
- **Cases automation can't reach yet** — hardware, third-party sandboxes, visual judgment.

Budget it as a named activity, not an afterthought. It does not replace any tier above; it covers the gaps.
