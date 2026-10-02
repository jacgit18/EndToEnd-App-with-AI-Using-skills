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
  project's `ACCESSIBILITY.md`, never silently dropped.

## Measuring

- Measure the **production build** (`npm run build`, then the preview server), never the
  dev server. Dev-server runs include hot reload and unminified modules and score far lower
  (56 and 19s LCP in one recorded case).
- Record the Lighthouse version, browser, form factor and throttling with every result.
  Results apply to that build and environment only; local loopback is not the live site.
- Run the browser tests and the audit after any UI change. A fractional pass count (e.g.
  Agentic Browsing 2/3) fails even when the numeric score reads 100, because zero-weight
  audits such as `llms.txt` drop out of the number.

## Where the detail lives

Fixing a score below target: `web-vitals-audit`. Keep per-project results and the manual
checklist in that project's `ACCESSIBILITY.md`; this file holds only the standing policy.
