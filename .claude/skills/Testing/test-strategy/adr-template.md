# ADR Template

Copy the block below to `docs/architecture/decisions/NNN-<slug>.md`. `NNN` = next integer after the highest existing ADR (zero-padded to 3), `<slug>` = short kebab-case topic (e.g. `payments-test-strategy`, `no-e2e-suite`, `bdd-tooling-rejected`). Write an ADR only for the **contested calls** — the choices a future reader would otherwise question. The full mix lives in the test plan at `docs/testing/<slug>.md`; the ADR records why the non-obvious lines are what they are. Fill every field. No `TBD` in Context or Decision.

---

```markdown
# NNN. <Short title of the decision>

- **Status:** Accepted
- **Date:** <YYYY-MM-DD>
- **Deciders:** <who approved this>

## Context

<What surface this covers and its seams. The gate answers, stated plainly:
where the expensive failures are; who depends on this interface staying
stable; the pipeline stages that exist; the non-functional numbers (or the
explicit "none specified"); change rate and lifetime; who maintains the
suite and the CI time budget.
2–5 short paragraphs or a tight bullet list — enough that a reader with no
memory of the conversation understands the situation.>

## Decision

- **Test mix:** unit <~%> / integration <~%> / contract <yes|no> / E2E <~%, which journeys> / smoke <yes|no>
- **Departure from 70/20/10:** <one line — why this surface's shape justifies it>
- **Pipeline placement:** <level → stage, and any new stage the plan requires>
- **Functional technique:** <black-box | white-box | grey-box> ; **data:** <fixtures | data-driven>
- **Non-functional in scope:** <each type with a threshold, or "none — accepted">
- **Workflow:** <TDD | test-after | BDD with Gherkin> — <the reason, incl. who reads .feature files>

## Consequences

**Accepted costs**
- <concrete cost 1 — e.g. "integration bugs in the tax API seam won't surface until staging">
- <concrete cost 2>

**Rejected alternatives**
- <e.g. "full E2E suite">: <one line on why not, tied to a gate answer>
- <e.g. "BDD/Cucumber">: <one line on why not>

**Deferred (not decided here)**
- Coverage percentage and CI enforcement → `coverage-policy`
- Framework / tool choice → <needed; owner / when>
- CI / E2E infrastructure cost sizing → <`technical-cost-decision`, or "not needed">

**Revisit when**
- <the condition that would reopen this — e.g. "a second consumer takes a dependency on this interface", "a latency SLA is introduced", "the surface stops being a prototype", "the E2E suite's flake rate crosses the point where it's ignored">
```

---

## Notes

- One ADR per contested decision, not one per surface. "No E2E suite" and "BDD rejected" on the same service can be one ADR or two — group them if the reasoning is shared.
- The test *plan* (`docs/testing/<slug>.md`) is the living document teams work from. The ADR is the frozen record of why the arguable lines are what they are.
- ADRs are append-only. To change a past decision, write a new ADR that references and supersedes it, and set the old one's Status to `Superseded by NNN`.
- The "Revisit when" line is the point of the document — it tells a future reader whether the choice still holds.
