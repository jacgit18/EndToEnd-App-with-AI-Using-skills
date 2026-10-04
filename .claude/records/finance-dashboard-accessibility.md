# Accessibility and Lighthouse record: finance-dashboard

Results and open manual-review items for `finance-dashboard/`. Lives here, not in the project, so the lessons can feed the skills and rules; it is not auto-loaded. Policy lives in `.claude/rules/web-accessibility-and-lighthouse.md` (target: WCAG 2.2 AAA, Lighthouse 100 in all four categories). This file holds the results and what is still unverified. **Nothing here is a conformance claim.**

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

**Not covered by this run.** Pages were measured in their loaded, default state only: the account and category edit rows, the Import page after a file is chosen, and error messages were not audited. The fixture API is not real data. Deploy status: see ~/Documents/TODO.md.

## States and manual-review items run by script (2026-10-03, second pass)

Same setup (prod build, real Caddy, fixture API; Playwright intercepts requests to force error and result states).

**Other page states, axe at 1280px and 320px, with scrollWidth equal to the viewport:** account edit row, account create error, bad starting balance, show-archived; category edit row, create error; budgets copy-forward error and cleared month; home create error and backend-unreachable; dashboard API error, cleared month, empty month; login wrong password; Import after choosing a file, with columns chosen, in account-column mode (after picking the column), the success result panel (with a rejected row listed) and the error result. **0 violations in all of them.**

| Manual-review item | Result |
|---|---|
| 200% text scaling | `html { font-size: 200% }` at 1280px and 640px on all 7 routes: no sideways scroll, no clipped text boxes, axe clean |
| 400% zoom | Same as 320px width (1280 / 4): all routes and states pass reflow |
| Keyboard | Every focusable element on all 7 routes is reached by Tab, no traps. **Fixed:** date and month inputs showed no focus ring, and the default ring was 1px. Now a 3px `#0b57d0` ring on `:focus-visible` and `input:focus-within` |
| Forced colors / dark scheme (Chromium emulation) | **Defect found and fixed:** chart axis labels, ticks, the zero line and the budget markers were hard-coded dark and vanished on black. Now `svg text { fill: currentColor }` and `svg line, svg path { stroke: currentColor }`. Bars keep their colours, and every charted value is also in the table under the chart. Not tested in real Windows High Contrast |
| Reduced motion | No animation or transition anywhere in the code, so nothing to reduce |
| Target size 44px | Measured on every route: all links, buttons, inputs, selects and checkbox labels are 44px or more |
| Third-party destinations | Every route loads only from its own origin (no fonts, scripts or analytics). Confirm on the deployed site |
| Reading level / unusual words | See below |

Reading-level notes (open, owner decision): the page text is short and plain. The terms an ordinary reader may not know are **Void** (a button; its confirm dialog explains it), **Net**, **Kind** (income or expense), **Archive**, **Skipped duplicates**, **Rejected**, **Starting balance**, and **Uncategorized**. A plain-language supplement (a short help line, or a longer label such as "Net (income minus spending)") would meet WCAG AAA 3.1.3; changing visible labels also changes tests, so it was left for the owner.

## Automated axe in CI (2026-10-03, third pass)

`frontend/e2e/a11y.spec.js` now reruns axe on every PR (ADR-0023): 15 views (7 routes plus
login error, transaction error, dashboard empty month, account edit row, accounts and
categories with archived shown, import preview) × 1440px and 320px × light and dark = 60
scans, same tag set as above, plus a page-width check. Playwright 1.63.0, Chromium (Playwright
build 1243), `@axe-core/playwright` 4.13, production build via `vite preview`, API mocked in the page.

**Defect found and fixed:** voided and reversal transaction rows and archived account and
category rows were dimmed with `opacity: 0.55`. That took their text below 7:1
(`color-contrast-enhanced`) and their buttons below 4.5:1 (`color-contrast`, an AA failure).
The earlier passes missed it because their fixture had no voided rows and no archived
accounts. Now a `#4d4d4d` text colour (8.5:1), `MUTED_ROW` in `src/a11y.tsx`; the
"(voided)"/"(archived)" text carries the state. After the fix: 0 violations in all 60.

## Not measured yet

- The deployed HTTPS site (Cloudflare tunnel). Local loopback is not the live site.
- Authenticated pages with real data and real volumes.

## Manual review still required

- [ ] Screen reader pass: NVDA with Firefox, VoiceOver with Safari. Check that the chart tables are announced in a sensible order and that the SVG charts do not add noise.
- [x] 200% text scaling and 400% zoom (scripted, see above).
- [x] Forced colors, Chromium emulation (see above). [ ] Real Windows High Contrast, by hand.
- [x] Reduced motion: no animation exists. Re-check when any is added.
- [x] 44px target size, measured on every route.
- [ ] Reading level and unusual words: findings above, owner to decide on plain-language supplements.
- [x] Third-party destinations: none on any route locally. [ ] Confirm on the deployed site.
- [ ] Keyboard check by hand (the script covers reachability and ring size, not whether the order feels sensible).
- [ ] Retest on the deployed HTTPS site after the next deploy (this pass's fixes, the focus ring and chart colours, are not deployed yet).
