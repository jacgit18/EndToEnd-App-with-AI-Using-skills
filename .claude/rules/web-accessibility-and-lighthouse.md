# Web accessibility and Lighthouse

Applies to any web UI built or changed from this repo (portfolio site, `finance-dashboard/`).

## Targets

- **Conformance target: WCAG 2.2 AAA.** Build to it by default: visible focus, 44px
  targets, AAA contrast, reflow at 320px, 200% text scaling, reduced-motion and
  forced-colors support, plain-language supplements.
- **Score target: 100 in all four Lighthouse categories** (Performance, Accessibility,
  Best Practices, SEO), on mobile and desktop, on every route. Treat anything below 100 as
  a defect to fix or explain, not a pass.

## Claims

- **A Lighthouse or axe score is regression evidence, not conformance.** Never write
  "AAA compliant" or "conformant" from a score of 100. Automated tools cover only a
  fraction of the criteria.
- Claim conformance only after the manual review is done and recorded: screen readers
  (NVDA/Firefox, VoiceOver/Safari), 200% and 400% zoom, forced colors, reading level and
  unusual words, third-party destinations, and a retest of the deployed HTTPS site.
- Anything not yet manually verified goes in a "Manual review still required" list in the
  project's accessibility record, never silently dropped.

## Measuring

- Measure the **production build** (`npm run build`, then the preview server), never the
  dev server. Dev-server runs include hot reload and unminified modules and score far lower
  (56 and 19s LCP in one recorded case).
- Record the Lighthouse version, browser, form factor and throttling with every result.
  Results apply to that build and environment only; local loopback is not the live site.
- Run the browser tests and the audit after any UI change. A fractional pass count (e.g.
  Agentic Browsing 2/3) fails even when the numeric score reads 100, because zero-weight
  audits such as `llms.txt` drop out of the number.

## Build to these from the first commit

- One `<main>` and one `<h1>` per page; sections `<h2>`; every control has a real label
  (`aria-label` at minimum; a placeholder is not a label); data-table action columns get
  screen-reader header text.
- Text colours at 7:1 on the background. Inline chart text and lines use `currentColor`.
- 44px minimum for buttons, inputs, selects, links and checkbox labels; a 3px `:focus-visible` ring.
- Form rows wrap; wide tables sit in a named, focusable scroll box so the page never scrolls sideways at 320px.
- Serve with compression and `immutable` caching on fingerprinted assets; add `robots.txt` and a meta description.
- Keep tiny CSS inline (a separate file is a render-blocking request).
- A structure test per page; run axe (AAA tags, 1280px and 320px, every state) and Lighthouse on every route.

## Keep the score on every UI change (standing requirement)

Hitting 100 once is not the job; keeping it is. For any project with a web UI:

- Install the runner: `plugins/testing-skills/skills/web-vitals-audit/lighthouse.mjs` copied to `scripts/lighthouse.mjs`
  (production build, mobile and desktop, first visit; `--check` fails under the floors; `--tab=`, `--runs=3`, `--url=`).
  Set its `FLOORS` to the project's current scores on day one, raise them whenever a change earns it, never lower them silently.
- The project's CLAUDE.md says: before a PR that changes UI, styles, fonts, images or the bundle, run it and put the before and
  after in the PR description; a score under the floors is a regression to fix; a change that has to cost points says so in the PR.
  Add a "Lighthouse run" line to the PR template's checks.
- Build by these (each was a real loss of points): nothing arrives after load and moves the page (late banners, notices and images
  float over the page or reserve their space); measured fallback fonts, and preload only the title font; the first screen's bundle
  stays small (sheets and tabs lazy, heavy libraries behind `import()`, and a failed lazy download maps to a reload prompt); small
  CSS inline, component CSS in its own file; images with width and height, lazy below the fold; an accessible name contains the
  visible text; only roles the element allows; every colour pair passes in light and dark, native controls (`select`) included.
- When a project is onboarded, write its baseline (scores, FCP, LCP, TBT, CLS) and "room to improve" list into its design-system
  doc, so the next change starts from a number.

## Where the detail lives

Fixing a score below target, or auditing login-gated pages and the proxy: `web-vitals-audit` (`measurement.md`, last section). Keep per-project results and the manual
checklist in `.claude/records/<project>-accessibility.md` (outside `rules/` on purpose: files in `rules/` load into every session, a results record should not). This file holds only the standing policy.
