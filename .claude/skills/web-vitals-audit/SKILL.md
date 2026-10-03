---
name: web-vitals-audit
description: Procedure for a poor Lighthouse or Core Web Vitals number, or an axe/accessibility audit of a site: reproduce cold (first visit, throttling verified, several widths), find layout shift element by element, rank fixes by cost. Triggers: "my Lighthouse score is low", "fix our CLS", "audit this site's accessibility", "run axe on every page". Not backend slowness (`problem-solving-gates`), service workers (`pwa-adoption`), a network symptom (`debugging-layer-selection`), or axe inside e2e (`browser-test-tooling`).
---

# Web Vitals Audit

A **procedure, not a gate.** The user already has a number — a Lighthouse score, a field
Core Web Vitals report (Search Console, CrUX, RUM), or a visible symptom ("the header jumps
on load"). This skill reproduces that number under conditions that can actually show the
problem, finds the cause element by element, and ranks fixes by what they cost.

**Coverage is uneven, on purpose.** The measurement discipline (Step 2) and the layout-shift
method (Step 3) come from a real fix (CLS 0.246 → 0.001, score 0.24 → passing) and are tested.
LCP, INP and bundle-size guidance (Step 4) is thinner — say so when the problem lives there.

## Step 1 — State the number and the target

Ask if unstated, in one message:

1. **The URL** (or how to serve the build locally) and **the number** — which metric, what
   value, from where (Lighthouse lab run, PageSpeed Insights, field data).
2. **Form factor** — mobile, desktop, or both. Lighthouse's headline score is mobile by default.
3. **What "fixed" means** — a score threshold, a metric passing (CLS < 0.1, LCP < 2.5 s,
   INP < 200 ms at p75), or "it stops jumping".

If the user names no threshold, the default target is the repo's standing policy if it has
one (here, `.claude/rules/web-accessibility-and-lighthouse.md`: 100 in every Lighthouse
category on mobile and desktop); with none, propose the Core Web Vitals "good" thresholds
above and confirm. A 100 is regression evidence, never a WCAG AAA conformance claim.

No number and no symptom ("make the site faster") is not this skill yet — ask which page and
what is slow, or route to `problem-solving-gates` Optimization if it is not a page-load metric.

## Step 2 — Reproduce it cold before changing anything

Re-run the measurement and get the reported number back. **A fix you cannot measure before
and after is a guess.** Repeat visits hide almost every page-load problem, so check each:

(Login-gated pages, proxy headers, accessibility beyond the Lighthouse number: `measurement.md`, last section.)

- **First visit.** Service worker bypassed, cache disabled, fresh profile. A PWA's warm runs
  look perfect and prove nothing about a first visit.
- **Throttling actually applied.** A sub-second load on "Slow 4G" means throttling did not
  happen. Prefer `--throttling-method=devtools` (it really delays requests, so late fonts and
  images show their true effect) over the default simulated throttling when chasing shifts.
- **Several widths.** Phone (~375 px), the awkward middle (~900–1000 px, where headers wrap),
  desktop. A shift that only exists at one width is still a shift.
- **Same number as the report.** For a lab report (Lighthouse, PageSpeed lab section), match
  it; if the cold run does not, the two disagree on conditions — find out which before
  diagnosing. **Field data cannot be matched**: it is a 28-day p75 over real devices. Reproduce
  the *direction* (the lab run also shows the shift or slow paint), diagnose from the lab run,
  and say the field number only confirms a fix after its window rolls over.

Commands, headless Chromium reuse, and the throttling sanity check are in `measurement.md`.

## Step 3 — Find the cause of layout shift element by element

Only when CLS (or a visible jump) is part of the problem. Name the elements that move — never
"fonts, probably".

1. **Record shifts.** A `PerformanceObserver` on `layout-shift` lists every shift with its
   value and the nodes that moved. Treat `hadRecentInput: true` entries with suspicion when
   nothing was tapped.
2. **Lay the page out twice and diff element heights** — once with web-font requests blocked,
   once loaded. Any element whose height differs is a future shift; this points straight at
   text that wraps onto an extra line when the font swaps.
3. **Separate font swaps from the app's own rendering** — trace frames alongside
   `document.fonts.status`. A shift while fonts are already `loaded` is the app (a loading
   frame, status text changing height, content inserted above).

Snippets for all three are in `cls-diagnosis.md`.

## Step 4 — Rank fixes, cheapest first

Map each named cause to a fix and state the cost. Preferred order from the tested case:

| Cause | Fix | Cost |
|---|---|---|
| Fallback font wider/taller than the web font | `@font-face` fallback with `local()` + `size-adjust` + `ascent-override`/`descent-override` **measured** per weight | None — no download, no paint delay |
| Changing text in a wrapping container | Fixed-size slot for the changing text | None |
| App renders a placeholder frame before local data | Read synchronous local data before first render | Small refactor |
| One critical font late | Preload **that one** font file | First-paint time — preloading every weight cost ~250 ms for no gain |

Rule of thumb: **make the fallback occupy the same space rather than rushing the web font.**
Measure the size adjustments against the app's own text (`cls-diagnosis.md`); never copy
another project's percentages.

For LCP, INP or unused JavaScript: name the Lighthouse audit that dominates, fix only that,
and say this skill's guidance there is untested. Do layout shift first if it is a large share
of the score — splitting bundles moves little while the page still jumps.

## Step 5 — Re-measure and report

Re-run the exact Step 2 conditions. Report before → after per metric and per width, which
fix moved which number, and what you deliberately left alone (see below). If a deploy is
involved, the final measurement is on the live URL, not the local build. A score that wobbles by a point on an unchanged build is noise: repeat three times before calling a regression or a fix.

## What not to change

Say these out loud when they come up rather than doing them by reflex:

- **Virtualization** for a page of a few thousand elements with bounded lists.
- **`font-display: swap`** when it is already there — the fix is the fallback metrics.
- **Host headers you cannot control** (e.g. GitHub Pages' cache lifetime); a service worker
  already covers repeat visits — `pwa-adoption` owns its design.
- **Bundle splitting before CLS is fixed.**

## Escape hatch

If the user only wants the measurement, stop after Step 2 with the reproduced numbers. If no
browser can run in this environment, give the exact commands from `measurement.md` for them
to run and diagnose from the JSON they paste back.

If `learning-gate` classified the request as **learning** (they want to be able to do this
themselves), keep the steps but hand them the work: they run the Step 3 observer and height
diff and name the shifting elements; Claude checks the reading and explains, rather than
running the diagnosis for them.

## Example invocations

> "Lighthouse gives our landing page 0.31 on mobile, CLS is 0.27. Can you fix it?"

Applies. Step 1 is already answered except the target; reproduce cold at three widths, then
Step 3.

> "Search Console says our product pages fail CLS on mobile."

Applies — field data. Reproduce the direction in a lab run (Step 2's field-data branch).

> "The header jumps when the page loads, only on my phone."

Applies — a visible symptom is enough; Step 3 at phone width.

> "Our `/api/orders` endpoint takes 2 s. How do I speed it up?"

Does not apply — server-side slowness; `problem-solving-gates` Optimization (needs a profile).

> "Should we add a service worker so the app works offline?"

Does not apply — `pwa-adoption`.

> "The page loads but the fetch to `/api/user` fails with a CORS error."

Does not apply — a functional network symptom; `debugging-layer-selection`.

## Portability

Needs Node (`npx lighthouse`) and a Chromium; Playwright is optional but makes the height-diff and multi-width runs scriptable. Produces no files.

Depends on: `problem-solving-gates`, `pwa-adoption`, `debugging-layer-selection`, `browser-test-tooling`, `caching-strategy`, `observability-strategy`, `reliability-math`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: no `problem-solving-gates` and the slowness is server-side → ask for a server timing measurement before changing frontend code; no `pwa-adoption` → service-worker design is a separate decision, say so; no `debugging-layer-selection` and the symptom is a failing or hanging request → that is a network question, not a vitals one.

## Routing boundaries (full)

- Use when a web page has a measured or visible page-load problem: a Lighthouse / PageSpeed
  score, a failing Core Web Vital, or content that jumps as it loads.
- NOT `problem-solving-gates` Optimization — server, query or code-path speed with a profile.
  "Make the site faster" with no page metric starts there or with Step 1's question.
- NOT `pwa-adoption` — whether and how to add a service worker. This skill bypasses the
  service worker to measure first visits; it does not redesign caching.
- NOT `debugging-layer-selection` — a live functional symptom (request failing, connection
  dropping) that needs an observation layer picked.
- NOT `reliability-math` / `observability-strategy` — server telemetry and what to instrument
  long-term. Setting up field RUM for web vitals is `observability-strategy`'s call.
- NOT `caching-strategy` — a server-side cache.
- Accessibility findings from the same Lighthouse run (e.g. label-in-name, WCAG 2.5.3) are
  real bugs — report them, but they are not this skill's subject.
