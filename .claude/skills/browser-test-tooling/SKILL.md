---
name: browser-test-tooling
description: Gated decision for what a browser/UI end-to-end test runs against and how it stays deterministic: runner, prod build vs dev server, clock/storage controls, retry and wait policy. Triggers: "Playwright or Cypress", "our e2e tests are flaky", "set up e2e for this app", or a runner already decided. Not test mix — `test-strategy`. Not cases — `test-case-discovery`. Not one failing spec — `problem-solving-gates`.
---

# Browser Test Tooling

`test-strategy` decides *that* an end-to-end tier exists and which journeys it covers; it defers "Playwright vs Cypress" and similar tool picks. This skill is that later step for the browser seam: given a settled UI test tier, what does it run against, what is pinned so it tells the truth, and what does CI do when it fails.

## Step 1 — Place the request

| What's being asked | What it actually is | Owned by |
|---|---|---|
| Runner choice, what the app under test is, what is made deterministic, retry/wait/CI policy for browser tests | Browser-test mechanism | This skill |
| Whether e2e tests should exist at all, how many, which journeys, unit-vs-e2e split | Test level mix | `test-strategy` — settle first |
| Which cases/journeys to cover ("what am I missing") | Case list | `test-case-discovery` |
| Writing one specific test, or stating its charter | Test rep | `test-practice-gate` |
| What backs a database-touching test | DB seam | `database-test-tooling` |
| A Lighthouse/CWV number | Page-quality evidence | `web-vitals-audit` |
| An axe scan inside the e2e suite: its tags, and whether a pass means conformance | Browser-test config | This skill (Step 3 row); the repo's accessibility policy if it has one (see Portability) |
| Service-worker design (offline scope, caching, update lifecycle) | PWA decision | `pwa-adoption` — this skill only keeps tests honest around it; if that is the only question, answer it here and do not run `pwa-adoption`'s gate |
| Whether a coverage % blocks CI | Coverage policy | `coverage-policy` |
| Whether an agent drives a browser (e.g. Playwright MCP) as a live tool | Agent tooling | `api-tooling-selection` |
| One failing spec ("this test times out on CI") with a trace pasted | Live debugging | `problem-solving-gates` Rubber Duck; a network-layer symptom → `debugging-layer-selection`. A pasted trace still gets the Rubber Duck first (ask for their hypothesis). Many flaky specs across runs is this skill |

Hand off on any row not marked "This skill"; do not recommend a runner for a question that is really test mix or case discovery.

## Step 2 — Gate: name these before recommending

- **What is under test: the production build or a dev server?** Dev servers add hot reload and unminified modules, so timing and bundling differ from what ships. Default to the production build served by the preview server; accept a dev server only with a stated reason.
- **What nondeterminism does the app read?** Name each: wall clock and timezone, `localStorage`/cookies/IndexedDB, service workers, network (real backend, mocked, recorded), randomness, animations, viewport. Each is either pinned or knowingly left live.
- **Who owns the data state at test start?** Seeded per test through a fixture, shared and reset, or whatever the last run left. Parallel workers sharing one origin's storage need an answer here.
- **What does CI do on failure?** Retries (how many), traces/screenshots/video kept when, report uploaded, `.only` blocked. Name whether a test that passed on retry is counted as green or flagged flaky.
- **How does a test wait?** Web-first assertions on a visible element or state, versus fixed sleeps or `networkidle`. Name the signal the page gives that it is ready.
- **Cross-browser and viewport scope.** One engine at one viewport, or a matrix. A matrix multiplies run time; tie it to `test-strategy`'s CI budget.

**Already decided is not answered.** A runner or dev server the user has chosen, or "don't ask questions", does not skip the gate: give the config with the dev-server cost stated and ask only the decisive unanswered items.

**Proceed on stated facts.** Facts the user already gave (symptoms, config, build target) count as answered. If they point at likely sources, give a provisional Step 3 recommendation for those now and ask only the unanswered gate items that would change it (at most three, most decisive first: build target, clock/storage ownership, wait signal). Do not return a bare question list. A dev server needs a stated reason such as dev-only env or a proxy; "it was the default" is not one. Worker count and `fullyParallel` belong under data ownership: parallel workers sharing state is a gate answer, not an afterthought.

A bare "what is Playwright" is a definitional question: answer it, do not gate it.

## Step 3 — Recommendation

| Situation | Recommendation |
|---|---|
| New suite, no runner yet | Pick on the gate answers, not preference: Playwright when multi-browser, parallelism and built-in tracing matter; Cypress when its in-browser debugging loop is what the team values and one engine suffices; the choice is rarely decisive, so name the one gate answer that tipped it. |
| App has a build step | Run against the production build and preview server. Say what that costs (build time before the first test) and who reuses a running server locally. |
| Tests depend on date/time | Install a fake clock at a fixed instant and pin the timezone; pick an instant that exercises the boundary the logic cares about (week start, month end) rather than "now". |
| Tests depend on persisted state | Seed storage in a fixture before first load; one fixture, shared by all specs, so the starting state is written down once. |
| Service worker present but not under test | Block it in config so cached assets cannot mask a change; test it deliberately in its own spec if it matters (`pwa-adoption` owns the design). |
| Flaky suite | Find the nondeterminism source from the gate list before adding retries. A retry budget of 1 on CI is acceptable only if retried passes are reported as flaky, not green. |
| Accessibility scan inside e2e | Keep it, scoped to the tags the target needs, and treat a pass as regression evidence, not conformance. |

Concrete config keys and runner differences are in `tool-landscape.md`; read it once a runner is chosen.

## Red flags — not done

- Recommended a runner before the dev-server-vs-production-build question was answered
- Added retries or longer timeouts to a flaky suite without naming the nondeterminism source
- Left the clock, timezone or storage state unpinned for tests whose logic reads them, without saying so
- Recommended fixed sleeps or `networkidle` as the readiness signal without naming the cost
- Treated a passing axe scan as accessibility conformance
- Answered test-mix or case-discovery questions as if they were this skill's call

## Examples

- **Fires:** "Our Playwright suite passes locally and flakes on CI — what do we change?" Gate on build target, clock/storage pinning, wait signal and retry policy before touching timeouts.
- **Does not fire:** "Which flows should our e2e suite cover?" → `test-case-discovery`. "Should we have e2e tests at all?" → `test-strategy`. "This one spec fails with a timeout, why?" → `problem-solving-gates`.

## Portability

Needs no repo setup; produces no files. If the repo keeps an accessibility/Lighthouse policy (here, `.claude/rules/web-accessibility-and-lighthouse.md`), its targets apply; without one, an axe pass is still regression evidence, never conformance.

Depends on: `test-strategy`, `test-case-discovery`, `test-practice-gate`, `database-test-tooling`, `web-vitals-audit`, `pwa-adoption`, `coverage-policy`, `api-tooling-selection`, `problem-solving-gates`, `debugging-layer-selection`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: no `test-strategy` and the e2e tier isn't settled → say whether an e2e tier should exist is the prior decision and stop at a runner shortlist; no `problem-solving-gates` and one spec fails with a trace → ask for the user's hypothesis about that failure before changing config; no `pwa-adoption` → block the service worker in tests and say its design is a separate decision.

## Routing boundaries (full)

- Use when someone asks "Playwright or Cypress", "our e2e tests are flaky", "how do I set up e2e for this app", "should e2e run against the dev server", "how do I freeze the date in browser tests", "should CI retry failed e2e tests", or proposes a browser-test setup and wants it checked.
