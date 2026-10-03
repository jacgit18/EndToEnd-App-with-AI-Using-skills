# Measurement — reproducing the number cold

Reference for `SKILL.md` Step 2 and Step 5.

## Lighthouse from the command line

Lighthouse runs from `npx` and needs a Chromium. If Playwright is installed, reuse its browser
instead of downloading Chrome:

```bash
# Find Playwright's Chromium (path varies by version and OS)
CHROME_PATH=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | tail -1)

# Mobile, real request delays, JSON for before/after diffs
CHROME_PATH="$CHROME_PATH" npx lighthouse "$URL" \
  --form-factor=mobile \
  --throttling-method=devtools \
  --only-categories=performance \
  --output=json --output-path=./lh-mobile-before.json \
  --chrome-flags="--headless=new"

# Desktop needs its own screen emulation as well as the form factor
CHROME_PATH="$CHROME_PATH" npx lighthouse "$URL" --preset=desktop \
  --output=json --output-path=./lh-desktop-before.json --chrome-flags="--headless=new"
```

Pull the numbers that matter out of the JSON:

```bash
jq '{score: .categories.performance.score,
     cls: .audits["cumulative-layout-shift"].numericValue,
     lcp: .audits["largest-contentful-paint"].numericValue,
     tbt: .audits["total-blocking-time"].numericValue,
     shifts: [.audits["layout-shift-elements"].details.items[]?.node.snippet]}' lh-mobile-before.json
```

(`layout-shift-elements` was renamed `layout-shifts` in newer Lighthouse versions — check which
key exists.)

Lighthouse starts each run with a clean profile, so it is a first visit by default. DevTools'
Lighthouse panel and manual DevTools runs are **not** — see below.

## First-visit checklist for manual DevTools runs

- Application → Service workers → **Bypass for network** (or unregister).
- Network → **Disable cache** checked, with DevTools open for the whole load.
- Network throttling set, **and** CPU throttling (4× slowdown approximates mid-range mobile).
- Or use a fresh incognito window / new Playwright context per run.

## Is throttling really applied?

Sanity-check every run against what the throttle allows. Slow 4G is about 400 kbps down with
~2 s round trips; a page with a 150 KB critical path cannot load in 222 ms on it. A number
that is impossible for the stated conditions means the run was not throttled — discard it.

Lighthouse's default `--throttling-method=simulate` runs unthrottled and **estimates** the
throttled timings. That is fine for the score, but a late-arriving font never actually arrives
late, so font-swap shifts can be understated. Use `devtools` when chasing CLS.

## Widths

Run at least three: ~375 px (phone), ~900–1000 px (where a desktop nav starts wrapping), and
1280+ px. With Playwright, loop over `page.setViewportSize({width, height: 900})` and run the
`cls-diagnosis.md` observer at each.

## Beyond one number: pages behind a login, the proxy, and what a 100 hides

From a real audit of a login-gated app (7 routes, mobile and desktop). Reference for `SKILL.md` Steps 2 and 5.

- **Audit login-gated pages without logging in.** Serve the production build through the *real* proxy
  config (for Caddy: run the `caddy` image on a spare port with the project's Caddyfile, `sed` the
  backend upstream to a small stub, mount `dist` read-only). The stub returns fixture JSON for the GET
  routes the pages call (unknown GETs: `[]`). Playwright `page.route()` forces error, empty and
  result states without changing the stub. Say in the report that the data is fixtures. Docker Desktop
  does not share `/tmp`: keep the mounted config under `$HOME`; `--network host` does not reach the host.
- **Audit the proxy, not just the app.** A first run scored SEO 82 and mobile Performance 91 with
  zero application bugs: no compression (`encode zstd gzip`), no `Cache-Control: immutable` on
  fingerprinted `/assets/*`, no `robots.txt` (the SPA fallback served HTML for it), no meta
  description. Check headers with `curl -D- -H 'Accept-Encoding: gzip'` before blaming the code.
- **A Lighthouse 100 is not an axe pass.** Lighthouse's accessibility score counts only the audits it
  weighs. Pages scoring 100 still failed axe (no `main` or `h1`, heading order, unlabeled inputs,
  empty table headers). Run `@axe-core/playwright` with tags `wcag2a, wcag2aa, wcag21a, wcag21aa,
  wcag22aa, wcag2aaa, best-practice` at 1280px **and 320px** on every route and in every state
  (edit rows, error messages, results), and read `document.documentElement.scrollWidth` against the
  viewport (reflow; axe does not check it).
- **Measure target size yourself.** axe checks 24px; AAA asks for 44px. Read `getBoundingClientRect()`
  for every `a, button, select, input` (a checkbox's wrapping label is its target).
- **Check forced colors and a dark scheme with a screenshot.** Playwright `forcedColors: "active"`.
  Hard-coded dark chart text (Visx axes use `#222`/black) vanished on black; `svg text { fill:
  currentColor }` fixed it. Computed styles will not show this; look at the picture.
- **Tell noise from a regression.** Simulated mobile Performance moved 99 to 100 on identical builds.
  Repeat a suspect page three times: a score that stays 99 with LCP 0.3 s worse is real. Here a
  separate 0.4 kB stylesheet (a render-blocking request) did it; inlining the CSS in `index.html`
  restored 100.
- **A screen-reader-only utility needs a positioned scroll ancestor.** An absolutely positioned
  `VisuallyHidden` inside a table's `overflow-x: auto` wrapper still counted toward page width until
  the wrapper had `position: relative`.
- **Pin the structure with a test** per page (one `main`, one `h1`, every control has an accessible
  name via DOM queries because date inputs have no testing-library role, no empty `th`), and try a
  mutation for each rule.

The scripts from this audit are saved, with their app-specific parts marked, in `example-finance-dashboard/`.
