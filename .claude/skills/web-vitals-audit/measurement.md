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

