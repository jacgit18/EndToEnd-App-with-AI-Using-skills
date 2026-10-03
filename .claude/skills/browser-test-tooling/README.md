# browser-test-tooling skill

A gated decision (not a procedure) for what a browser/UI end-to-end test runs against and
how it stays deterministic: runner, production build vs dev server, pinned clock/timezone/
storage/service-worker/network, wait strategy, retry policy, and CI artifacts.

`test-strategy` decides *that* an e2e tier exists and defers "Playwright vs Cypress". This
skill is that later choice for the browser seam, the way `database-test-tooling` is for the
database seam.

## Where it sits

```
test-strategy            →  whether the e2e tier exists, which journeys, how much effort
test-case-discovery      →  which cases/journeys exist
browser-test-tooling     →  what a browser test runs against and how it stays deterministic  (this skill)
database-test-tooling    →  the same question for the database seam
test-practice-gate       →  one test's charter (its seam list names the clock/storage)
web-vitals-audit         →  a Lighthouse/CWV number; axe-vs-conformance policy lives in the rules file
coverage-policy          →  the % target
```

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Step 1 places the request, Step 2 gates on build target / nondeterminism / data state / CI failure policy / waiting / matrix, Step 3 recommends. |
| `tool-landscape.md` | Runner options, determinism controls, wait and CI settings, axe tag notes. |

## What it produces

A short recommendation in chat: runner (with the gate answer that tipped it), build target,
what is pinned and what is knowingly live, wait signal, retry/artifact policy. It does not
write config or tests.

## Deliberately out of scope

- Test mix and which journeys → `test-strategy`. Cases → `test-case-discovery`. One test's
  charter → `test-practice-gate`.
- DB-touching tests → `database-test-tooling`.
- Lighthouse/CWV scores → `web-vitals-audit`; service-worker design → `pwa-adoption`.
- Agents driving a browser as a live tool → `api-tooling-selection`.

## Dependencies

Needs no repo setup. The siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Installed in other projects via the `testing-skills` plugin
described in `plugins/README.md`.

## Interaction with sibling skills

- **vs `test-strategy`** — that skill decides whether an e2e tier exists and which journeys it
  covers; this one decides what it runs against and how it stays deterministic. Settle the
  tier first.
- **vs `test-case-discovery`** — which journeys/cases to cover is there.
- **vs `problem-solving-gates`** — one failing spec with a trace is a Rubber Duck rep; a suite
  flaking across runs is here.
- **vs `pwa-adoption`** — service-worker design is there; keeping tests honest around a
  service worker is here.
- **vs `web-vitals-audit`** — a Lighthouse/CWV number is there; an axe scan inside e2e is here.

Re-check overlap after any trigger-description change here.
