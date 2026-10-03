# Accessibility and Lighthouse record

Policy lives in `.claude/rules/web-accessibility-and-lighthouse.md` (target: WCAG 2.2 AAA, Lighthouse 100 in all four categories). This file holds the results and what is still unverified. **Nothing here is a conformance claim.**

## Automated results (regression evidence only)

Run 2026-10-03 against the **production build** (`npm run build`) served by the real `caddy:2-alpine` image with `Caddyfile.prod`, on a local loopback port.

| Item | Value |
|---|---|
| Lighthouse | 12.8.2, `--headless=new`, simulated throttling (mobile preset and `--preset=desktop`) |
| Browser | Playwright Chromium 153 on Linux |
| axe | `@axe-core/playwright`, tags wcag2a/2aa/21a/21aa/22aa/2aaa + best-practice |
| API behind the page | **A fixture stub, not the real backend** (the real API needs the owner's login). Fixture: 3 categories, 3 recent rows, 6 trend points. Real data volumes could change Performance. |

| Route | Form factor | Perf | A11y | Best Practices | SEO | Notes |
|---|---|---|---|---|---|---|
| `/dashboard` | mobile | 100 | 100 | 100 | 100 | LCP 1.6 s, CLS 0, TBT 40 ms |
| `/dashboard` | desktop | 100 | 100 | 100 | 100 | LCP 0.4 s, CLS 0, TBT 0 ms |
| `/login` | mobile | 100 | 100 | 100 | 100 | desktop not run |

axe on `/dashboard` at 1280px and 320px: **0 violations** (including the AAA tag set, so `color-contrast-enhanced` passed). Horizontal scroll width equals viewport width at both sizes.

Lighthouse's own "Agentic Browsing" category (and the `llms.txt` audit) did not appear in this Lighthouse version's output, so the fractional-pass rule in the policy could not be checked. Re-check when the tool adds it.

### Defects found and fixed in this pass

| Found by | Defect | Fix |
|---|---|---|
| Lighthouse | No text compression (`uses-text-compression`) | `encode zstd gzip` in `Caddyfile.prod` |
| Lighthouse | No cache headers on fingerprinted assets | `Cache-Control: public, max-age=31536000, immutable` on `/assets/*` in `Caddyfile.prod` |
| Lighthouse | No meta description; no `robots.txt` (SPA fallback served HTML for it) | `<meta name="description">` in `index.html`; `frontend/public/robots.txt` (allow all) |
| axe | No `main` landmark, no `h1` on `/dashboard` | `<main>` and `<h1>` in `DashboardPage.tsx` |
| axe | Heading order jump after adding the `h1` | Section headings `h3` to `h2` |
| axe (320px) | Page scrolled sideways (399 px wide): tile row did not wrap | `flexWrap: "wrap"` on the tile row |

A test pins the landmark and heading structure (`DashboardPage.test.tsx`); reverting one heading level is caught.

**Deployed to prod 2026-10-03.** Header changes confirmed on the local prod stack (gzip, immutable cache on `/assets/*`, `robots.txt`, meta description). Lighthouse was not re-run against the deployed HTTPS URL.

### Left as is, with reasons

- `unused-javascript` (about 42 KiB) and `network-dependency-tree-insight`: informational, score is 100 anyway.
- `robots.txt` allows all crawlers. Every data route is behind login, so there is nothing to index; blocking crawlers would make Lighthouse's `is-crawlable` fail. Revisit if the owner prefers `Disallow: /` over the SEO score.

## Other routes (run 2026-10-03, after the deploy; NOT yet fixed)

Same setup as above (prod build, real Caddy with `Caddyfile.prod`, fixture API with 1 account, 3 categories, 2 budgets, 3 transactions, 1 import batch). Lighthouse mobile / desktop; axe at 1280px and 320px.

| Route | Lighthouse mobile (P/A/BP/SEO) | desktop | axe 1280px | axe 320px |
|---|---|---|---|---|
| `/` Transactions | 100 / **85** / 100 / 100 | 100 / **85** / 100 / 100 | 4 violations | 4 violations, **page 819 px wide** |
| `/accounts` | 100 / **95** / 100 / 100 | 100 / 100 / 100 / 100 | 4 | 5, page 585 px wide |
| `/categories` | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 | 4 | 5, page 382 px wide |
| `/budgets` | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 | 4 | 4, page 369 px wide |
| `/import` | 100 / 100 / 100 / 100 | 100 / 100 / 100 / 100 | 3 | 3, page 533 px wide |

Findings, all still open:

- **Transactions `/`** (serious): the date filter input and the account `<select>` have no label (`label`, `select-name`, both critical); the "Backend: connected" text is seagreen `#2e8b57` on white at 4.24:1, below even AA 4.5:1 (`color-contrast`); one table header cell is empty (`empty-table-header`).
- **Reflow at 320px fails on every route** (page is 369 to 819 px wide): fails the reflow criterion. Tables and forms need to wrap or scroll inside their own container.
- **Landmarks and headings:** `/accounts`, `/categories`, `/budgets`, `/import` have no `<main>` and no `<h1>` (same fix as `/dashboard`), plus `region`.
- **Empty table header** on accounts, categories and budgets (an actions column with no accessible text).
- **Target size** below 24px on `/accounts` (2 nodes) and `/categories` (6 nodes) at 320px. The AAA target is 44px, so more would fail under a manual check.
- Lighthouse scores of 100 on four routes hide these: its audit only counts the subset it weighs. axe is the better signal here.

## Not measured yet

- The deployed HTTPS site (Cloudflare tunnel). Local loopback is not the live site.
- Authenticated pages with real data and real volumes.

## Manual review still required

- [ ] Screen reader pass: NVDA with Firefox, VoiceOver with Safari. Check that the chart tables are announced in a sensible order and that the SVG charts do not add noise.
- [ ] 200% text scaling and 400% zoom.
- [ ] Forced colors (Windows High Contrast): the over-budget red tick and the green/red trend bars carry meaning; the text tables already repeat every value, confirm the tick/bar distinction is not lost.
- [ ] Reduced motion (the app has no animation today; re-check when any is added).
- [ ] 44px target size on the month picker, nav links, and buttons (axe does not cover the AAA target-size criterion fully).
- [ ] Reading level and unusual words (labels such as "Uncategorized", "Net").
- [ ] Third-party destinations: none loaded by the page (no external fonts or scripts); confirm on the deployed site.
- [ ] Retest on the deployed HTTPS site after the next deploy.
