# web-vitals-audit skill

A procedure (not a gate) for a web page with a measured or visible page-load problem — a low
Lighthouse score, a failing Core Web Vital, content that jumps as it loads. It reproduces the
number under cold, honestly throttled conditions, finds layout shift element by element, and
ranks fixes by cost.

## Why this exists

Distilled from a real fix on a separate project (a mobile Lighthouse score of 0.24, CLS 0.246
→ 0.001). What carried over to other projects was not the specific numbers but the method:
reproduce before changing, distrust warm and unthrottled runs, diff layouts with fonts blocked
vs loaded, and match fallback-font metrics instead of rushing the web font. No other skill in
the catalog covers front-end page-load metrics; `pwa-adoption` mentions Lighthouse only for
installability.

**Honest coverage:** measurement and CLS are tested; LCP, INP and bundle-size guidance is thin
and the skill says so when the problem lives there. Extend it from the next real case rather
than from general knowledge.

## Where it sits

```
web-vitals-audit          →  page-load metric (Lighthouse / CWV) measured cold, CLS diagnosed,
                             fixes ranked                                       (this skill)
problem-solving-gates     →  Optimization mode: server / query / code speed with a profile
pwa-adoption              →  whether and how to add a service worker; this skill bypasses it
debugging-layer-selection →  live functional symptom → DevTools / backend / packet capture
observability-strategy    →  field RUM and long-term signals for web vitals
reliability-math          →  server telemetry arithmetic
```

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point: Step 1 states number + target, Step 2 reproduces it cold, Step 3 finds shifting elements, Step 4 ranks fixes, Step 5 re-measures. |
| `measurement.md` | Lighthouse CLI commands (reusing Playwright's Chromium), `jq` extraction, first-visit checklist, throttling sanity check, widths. |
| `cls-diagnosis.md` | `PerformanceObserver` shift recorder, fonts-blocked vs loaded height diff, swap-vs-app separation, fallback-font metric measurement + `@font-face` template, single-font preload. |

## Deliberately out of scope

- Server, query or code-path performance → `problem-solving-gates` Optimization.
- Service-worker and offline design → `pwa-adoption`.
- Field monitoring of web vitals → `observability-strategy`.
- Accessibility *conformance* claims. The measuring is in scope (axe with the AAA tag set at 1280px and 320px, target sizes, forced colors; `measurement.md`, last section) and the standing policy is `.claude/rules/web-accessibility-and-lighthouse.md`, but a passing score is never reported as conformance. An axe scan inside an e2e suite is `browser-test-tooling`.

## Dependencies

Needs Node (`npx lighthouse`) and a Chromium; Playwright is optional.
The siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Installed in other projects via the `testing-skills` plugin
described in `plugins/README.md`.

## Interaction with sibling skills

- **vs `problem-solving-gates` (Optimization)** — backend slowness with a measurement in hand
  is there; a page-load metric is here.
- **vs `debugging-layer-selection`** — a failing or hanging request is a network question,
  there.
- **vs `pwa-adoption`** — service-worker design is there.
- **vs `browser-test-tooling`** — an axe scan inside the e2e suite is there.

Re-check overlap after any trigger-description change here.
