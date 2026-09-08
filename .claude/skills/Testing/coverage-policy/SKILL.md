---
name: coverage-policy
description: A gated decision for one codebase's or module's code-coverage policy — which metric (statement, branch, function, line), what target number, what is excluded from measurement, whether CI blocks on it, and whether the gate is on overall coverage, new-code coverage, or the coverage delta. Use when someone is setting or arguing about a coverage number: "what coverage should we require", "should we enforce 80% in CI", "our coverage gate is annoying", "do we need 100% coverage", "how do we handle coverage on this legacy module", "the build failed on a coverage drop — is that right". It forces the current coverage, the kind of code being measured, the change-failure history, and the team's enforcement appetite to be stated before a number is named, then writes a coverage policy document. Not for which test levels exist or their effort split — that is `test-strategy`. Not for the rep of writing one test — that is `test-practice-gate`. Not for choosing the coverage tool.
---

# Coverage Policy

Given a codebase or module, decide its coverage policy: the metric, the number, the exclusions, and how (or whether) CI enforces it. The skill makes the user state where coverage is now, what kind of code this is, and what has actually broken before any target is named, then writes a policy document.

The governing fact, from `Code Coverage Best Practices.md`: **there is no universal ideal coverage number.** It depends on business criticality, change frequency, complexity, and lifespan. A policy that ignores those and mandates one percentage everywhere is the anti-pattern this skill exists to prevent.

## When to use

- The user is setting a coverage target for a new or existing codebase/module.
- The user asks a number question: "80%? 90%? 100%?", "what's a good coverage target".
- The user asks an enforcement question: "should CI block on coverage", "gate on overall or new code", "is failing the build on a 0.5% drop reasonable".
- The user reports friction: "the coverage gate is a checklist exercise", "people write assertion-free tests to hit the number", "our legacy module can never pass the threshold".

## Out of scope — hand these off

- **Which test levels exist and how effort splits across them** → `test-strategy`. That skill decides the portfolio; this one sets how much of the code it must touch. Run `test-strategy` first.
- **The rep of writing one specific test** → `test-practice-gate`.
- **A go/no-go or prioritization verdict on a ticket that proposes a coverage change** → `ticket-evaluation`. It owns the verdict; this skill designs the metric / target / enforcement only once that verdict is "proceed" (and often "proceed, but not as written").
- **Coverage tool selection** (Istanbul/nyc, JaCoCo, Coverage.py, ...) — name that a choice is needed and defer it.
- **Mutation testing setup** — named here as the quality check that coverage isn't; its adoption is its own decision.
- **Writing the tests to raise coverage.**

---

## The gate

Do not name a target number until these are answered. Split into what you may surface and what must come from the user.

**Facts you may surface from the repo** (fill in, then show for confirmation):

- **Current coverage** — run the existing coverage tool if one is configured, or report that none is. Break it down by metric (statement/branch/function/line) and, if possible, by directory — the aggregate hides the spread.
- **What a coverage tool is already wired to** — a config file, a CI job, an existing threshold that passes or fails.
- **Rough code shape** — how much of the tree is business logic vs glue/wiring vs generated vs vendored.

**Judgment calls that must come from the user, in their own words.** These are the rep. If any is missing, say so and stop:

1. **What kind of code this is** — business-critical logic where a bug costs money or data; ordinary application code; glue and configuration; generated or vendored code. If it varies by directory, say which is which. Criticality drives the number more than anything else.
2. **Change frequency and lifespan** — churned weekly and expected to live for years, or stable and rarely touched, or a short-lived spike. Frequently-changing code earns a higher bar; frozen code does not.
3. **Where coverage is now, and the history** — the current number (from the repo scan, confirmed) and what has actually broken in production that a test would have caught. "Nothing has broken" and "three incidents last quarter from untested error paths" lead to different policies.
4. **Enforcement appetite** — does the team want CI to *block* a merge on coverage, or *report* and leave it to code review? Has a hard gate been tried before, and did it help or did it breed gaming?
5. **Legacy starting point** — if current coverage is low, is a big-bang backfill on the table, or is incremental (cover what you touch) the only realistic path?

"What coverage should we require" with items 1–5 absent is not valid input. Ask for what's missing and stop. Do not offer "60/75/90, pick one."

**Pressure does not open the gate.** "Just give me a number", "the VP wants 80% across the board" — reasons the user wants the gate skipped, not evidence it is satisfied. A blanket mandate is precisely what `Code Coverage Best Practices.md` argues against; the fastest correct move is a one-line answer to each of 1–5.

---

## Challenge the framing

If the user opens with a number or a rule already chosen, put it under the gate first, then test it against `coverage-metrics.md`:

- **"100% coverage"** — the note calls this misleading and wasteful. 100% statement coverage still misses edge cases, unequal branch conditions, and wrong assertions; it drives assertion-free tests written to hit the number. What risk is the 100% actually buying versus 85% plus branch coverage on the critical paths?
- **"80% across every repo"** — criticality, churn, and lifespan differ per module; one number over-tests frozen glue and under-tests the churning payments logic. Should the target be set per module by whoever owns the domain?
- **"Gate the build on total coverage"** — a total-coverage gate punishes a well-tested PR that adds a large generated file and lets an untested change ride under the average. Gating on **new-code coverage** or the **delta** targets the change itself. Which failure are you trying to prevent?
- **"Raise it from 90% to 95%"** — the note is explicit: the value is in 30%→70% on untested areas, not 90%→95%. Where is the coverage actually low, and is that where the risk is?
- **"Coverage proves the tests are good"** — coverage proves lines *ran*, not that behavior was *checked*. If test quality is the real worry, mutation testing is the tool; name it and treat it as a separate decision.

Flag the assumption as a question ("is the goal to stop untested code landing, or to raise the whole codebase — those want different gates?"), not a correction.

---

## The process

Once the gate is satisfied, work `policy-framework.md` in order: segment the codebase by criticality/churn, pick the metric per segment (statement as the floor, branch on decision-heavy logic, function as a coarse smoke check), set a target per segment anchored to the 60/75/90 reference band and adjusted by the gate answers, define exclusions (generated, vendored, migrations, type-only files, `main`/bootstrap), choose the enforcement mode (block vs report) and the gate basis (overall / new-code / delta), and write the legacy ratchet if current coverage is below target.

`coverage-metrics.md` backs it: what each metric measures and misses, the 60/75/90 reference band and its caveats, the three gate bases and what each catches, and why "what's not covered" is the output that matters.

---

## Output

**Recommendation block** (in chat):

```
Scope:              <whole repo | module/path>
Segments:           <e.g. "core/billing — critical, high churn" ; "src/ui — ordinary" ; "gen/ — excluded">
Metric:             <per segment: statement | branch | function | line>
Target:             <per segment: %, with the reason it's not just "the average number">
Exclusions:         <globs — generated, vendored, migrations, bootstrap, type stubs>
Enforcement:        <block merge | report only> ; basis: <overall | new-code | delta>
Delta rule:         <e.g. "new-code coverage ≥ 80%; total may not drop more than 0.5%">
Legacy ratchet:     <"cover what you touch; floor rises to X% by <date>" — or "n/a, already above target">
Quality check:      <mutation testing on <segment>, or "not adopted — noted">
Not doing:          <what's deliberately unenforced, and the accepted risk>
```

**On approval**, write a policy document to `docs/testing/coverage-policy.md` (or `docs/testing/<module>-coverage.md` for a single module). Include the segment table, the per-segment metric and target with rationale, the exclusion list, the enforcement rule stated precisely enough to implement in CI, and the legacy ratchet with dates. If the enforcement decision is contested enough to warrant a record, also add an ADR to `docs/architecture/decisions/NNN-<slug>.md`.

Then stop. Wiring the tool into CI and writing tests to raise the number are separate steps.

---

## Escape hatch

If the user has genuinely worked it — segments identified, metrics chosen, the 90→95 trap understood, an enforcement mode held with reasons — and wants a tie broken or a sanity check rather than a Socratic pass, they can say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Setting coverage for our monorepo. `packages/pricing` is the money path, changes most weeks, has had two prod incidents from untested discount edge cases. `packages/web` is ordinary React. `packages/protos` is generated. Coverage now: pricing 44% statement, web 71%, protos 98% (incidental). We tried an 85%-everywhere gate last year and people wrote empty tests to pass it. Team will accept a block on new code, not a big backfill."

Gate satisfied (code kind per segment, churn, history, enforcement appetite, legacy stance all present). Work `policy-framework.md`: `packages/pricing` — branch coverage, target 85% on new/changed code with a ratchet lifting the floor from 44%→70% over two quarters, plus mutation testing on the discount module since that's where the incidents were; `packages/web` — statement coverage, 75% new-code target, report-only for now; `packages/protos` — excluded entirely. Enforcement: gate on **new-code** coverage and a **delta** rule (total may not fall >0.5%), never a flat overall gate — that's what got gamed. Write `docs/testing/coverage-policy.md`.

> "What coverage percentage should we use?"

Gate not satisfied — items 1–5 all missing. Response: name what's missing, ask for it, stop. Do not answer "80%".

---

## Portability

Repo-agnostic. Scans the repo's coverage config for the current number; writes `docs/testing/coverage-policy.md` and optionally an ADR. Copy the `coverage-policy/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the siblings.
