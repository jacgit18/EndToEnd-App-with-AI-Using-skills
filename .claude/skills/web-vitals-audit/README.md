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
- Accessibility audits — reported if Lighthouse surfaces them, not pursued.

## Using it in another repo

Repo-agnostic. Needs Node (`npx lighthouse`) and a Chromium; Playwright is optional but makes
the height-diff and multi-width runs scriptable.

```
cp -r .claude/skills/web-vitals-audit /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Tested via `skill-interaction-testing` at build time — see the build commit and project memory
for scenarios and fixes.
