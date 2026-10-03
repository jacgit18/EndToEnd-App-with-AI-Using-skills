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

## Other routes: found 2026-10-03, fixed in the same pass

First run (prod build, real Caddy, fixture API): `/` Lighthouse accessibility 85, `/accounts` 95 mobile; axe found 3 to 5 violations per route; every route's page was 369 to 819 px wide at 320px.

| Found | Fix |
|---|---|
| `/`: date input, account select, amount and description had no real label (amount and description had only a placeholder) | `aria-label` on each |
| `/`: "connected" text seagreen at 4.24:1 (fails AA). Error text crimson at 4.99:1 (passes AA, fails AAA) | `#1b5e20` (7.9:1) and `#a00000` (8.4:1), defined once in `src/a11y.tsx`. Chart bar fills keep their colours (graphics, 3:1) and every value is also text |
| Empty actions column header on `/`, accounts, categories, budgets | `VisuallyHidden` "Actions" text |
| No `<main>` / `<h1>` on accounts, categories, budgets, import; import's `h3` sections | `<main>`, `<h1>`, sections `<h2>` |
| 320px reflow: forms did not wrap, wide tables stretched the page | `flexWrap` on form rows; every table inside `ScrollTable` (a named, keyboard-focusable scroll box) |
| Touch targets under 44px (buttons, inputs, selects, links, checkboxes) | 44px minimum in a small inline `<style>` in `index.html` (a separate CSS file cost 0.3 s of mobile LCP on `/dashboard`, so it is inlined). Checkboxes: the wrapping label is the 44px target |

Tests: `src/a11y.test.tsx` renders each page and checks one `main`, one `h1`, every control has an accessible name, no empty table header, plus the helpers. Mutations tried: removing the Date label, the Description label, the Account label, the `h1`, the "Actions" text, `main` to `section`, an emptied `th`, and the scroll box's `position`. All caught (the first run missed the Date label because date inputs have no testing-library role; the test now checks the DOM directly).

Final measurement, same setup, after the fixes:

| Check | Result |
|---|---|
| Lighthouse, 7 routes (`/`, `/dashboard`, `/accounts`, `/categories`, `/budgets`, `/import`, `/login`), mobile and desktop | 100 / 100 / 100 / 100 on all 14 runs. LCP 1.2 to 1.6 s mobile, 0.4 s desktop. Mobile Performance moved between 99 and 100 in earlier runs; see "Run-to-run variation" |
| axe (WCAG 2.0 to 2.2 A/AA/AAA tags + best practice), 1280px and 320px, all 7 routes | 0 violations on all 14 |
| Page width at 320px | 320px on all routes |
| Interactive controls under 44px | none on any route (measured, not just axe's 24px check) |

**Run-to-run variation.** Lighthouse mobile Performance moved between 99 and 100 on identical builds (simulated throttling). One real regression appeared and was fixed: a separate stylesheet made `/dashboard` score 99 on three runs in a row (LCP 1.9 s); inlining it restored 100 (LCP 1.6 s, two repeat runs).

**Not covered by this run.** Pages were measured in their loaded, default state only: the account and category edit rows, the Import page after a file is chosen, and error messages were not audited. The fixture API is not real data. Deploy status: see TODO.md.

## Not measured yet

- Edit states (account and category edit rows), the Import page after a file is chosen, and error states.
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
