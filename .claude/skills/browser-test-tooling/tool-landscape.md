# Tool landscape

Concrete options for the browser seam, kept out of `SKILL.md` so the entry point stays
runner-agnostic. Use after Step 3 has named the choice; this changes nothing about the decision.

## Runners

- **Playwright (`@playwright/test`)** — Chromium/Firefox/WebKit, parallel by file, built-in
  trace viewer, `webServer` config block to build and serve the app, `page.clock` for time.
- **Cypress** — single in-browser runner with a strong interactive debugging UI; historically
  one browser tab per test and a different parallelism story (paid dashboard for some modes).
- **Selenium/WebDriver** — only when an existing grid or language binding forces it.
- **Playwright's raw library API** (no test runner) — for scripts like screenshot generation;
  it has none of the retry, fixture or reporter behaviour of the test runner.

## Determinism controls (Playwright names; other runners have equivalents)

| Source | Control |
|---|---|
| Wall clock | `page.clock.install({ time })` before navigation; pick a boundary-exercising instant |
| Timezone / locale | `timezoneId`, `locale` in config `use` |
| Storage | `page.addInitScript` to seed `localStorage` before first load, or `storageState` |
| Service worker | `serviceWorkers: 'block'` in config |
| Network | `page.route` to stub, or leave live and say so |
| Animation | `reducedMotion: 'reduce'`, or disable CSS animation in a test stylesheet |
| Viewport | `viewport` in config; a mobile project doubles the run |

## Waiting

Prefer web-first assertions (`await expect(locator).toBeVisible()`), which retry until a
timeout. `waitForLoadState('networkidle')` is discouraged by Playwright's own docs because it
guesses at readiness from traffic; keep it only when no visible ready signal exists, and say so.

## CI

- `forbidOnly` so a stray `.only` fails the build.
- `retries` on CI only; report retried passes as flaky (the HTML reporter does) rather than counting them as clean.
- `trace: 'on-first-retry'` or `'retain-on-failure'` keeps artifact size down; upload the report and results directory on failure.
- `webServer.reuseExistingServer: !process.env.CI` lets local runs reuse a running server while CI always starts clean.
- Browser install (`npx playwright install --with-deps`) is a per-run cost; cache or pin the image if CI time is tight.

## Accessibility scans in e2e

`@axe-core/playwright` with `.withTags([...])`. Tag sets cover the A/AA levels (include
`wcag22aa` for 2.2 and `best-practice` as needed); AAA success criteria are mostly outside
what axe can check, so they stay on a manual-review list. A clean scan is regression evidence only.
