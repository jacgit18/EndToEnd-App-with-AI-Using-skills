# Screen addresses: every screen has one, and the address is not security (applies to every project, 2026-10-31)

Found on iron-log (audit `Projects/iron-log/audits/2026-10-31-navigation-and-url-audit.md`): six tabs were kept in app state and every screen inside them was local state, so the address never changed. Back left the app, a reload lost the screen, nothing could be linked. A single-page app does not get addresses for free; each new screen has to be given one.

## The rule

1. **Every new screen, section, tab or drill-in gets an address in the same PR** (`#/progress/trends`, or `/progress/trends` on a path-routed app). A screen is anything a person can be "in": a tab, a segmented view, a page opened from a list or tile, a form page. A pop-up sheet or dialog is not a screen but it still adds one history entry, so Back closes it.
2. **Swap or push, by meaning.** A tab or a segmented control swaps the address (`replaceState`), so Back does not walk through every switch. Opening a page from a list or tile pushes one entry, so Back goes up one screen. A reload or pasted address reopens the screen; where a screen needs a record that is not in the address, it opens the list above it.
3. **One table, pure and tested.** The known addresses live in one list with a pure parser (iron-log: `src/lib/route.ts`), a unit test that every address round-trips, an unknown address falls back to the nearest screen above it (never an error page), and every address matches `^[a-z]+(/[a-z]+)*$`. Adding a screen means adding a row; a screen with no row is not done. The browser side (history, `popstate`, `hashchange`) is one hook; screens do not call `pushState` themselves.
4. **Back is part of done.** The feature's e2e checks the address after opening the screen, `goBack()` returns to the screen above (not out of the app), and a reload reopens it. Skip links and in-page anchors must not change the route (`preventDefault` and focus the target).
5. **Prefer hash routes** for a signed-in app served as a static shell: no server, service-worker or CDN change, nothing reaches the server or its logs, works in an installed PWA. Use path routes when pages must be crawled or shared publicly; then every path is also a server route and the security points below apply on the server.

## Security: what an address is and is not

- **An address is a bookmark, never a permission.** It only says which screen to draw. The server decides access on every data request (session, role, plan), whatever the address says. A hidden or admin screen is still protected by its server route and its UI feature check; typing its address must show nothing the person could not already see.
- **Never put sensitive or personal data in an address**: no emails, names, tokens, session or reset codes, API keys, health or money values, or another person's id. Addresses end up in browser history, the Referer header, server and proxy logs, analytics, screenshots and shared links. Screen names only; if a record must be named, use an opaque id of the viewer's own row and still check ownership on the server.
- **Treat the address as untrusted input.** Look it up in the allowlist table; never inject it into HTML (`dangerouslySetInnerHTML`, `innerHTML`), `eval`, a database query or a file path. Never redirect to a URL taken from the address (open redirect); a "return to" screen must be a table entry, not a free URL.
- **Sign-in and deep links:** an address for a screen that needs sign-in sends a signed-out person to sign-in, then back to that screen from the table; it never shows the screen's data first and never keeps tokens in the address. Sign-out clears in-memory data and the page states a person can reach with Back (no-store cache headers on API responses; do not rely on the browser cache).
- **Path routes only:** each path is authorised on the server like an API route; answer a missing or forbidden screen identically (404) so paths cannot be enumerated; serve the app shell for unknown paths without leaking whether a screen exists; keep API paths and file-serving paths out of the app's route table; set `Cache-Control: no-store` on authenticated pages.
- **Admin or paid screens:** the address does not hide them (security through obscurity). The UI check and the server check are the control; the route table may list them.
- **Do not log full addresses** with a person's history in analytics; log the screen name only, and only if the product has an opt-in for usage counts.

## Where it applies

- New project: Stage 0 of `new-project-order.md` includes a route table and the Back behaviour for the first screens.
- New feature that adds a screen, tab, view or drill-in: the brief's Done when has a line for it (address, Back, reload, no personal data); the project's `ux/` flow or screen spec lists the address.
- Existing project without addresses: run the navigation audit (iron-log's audit is the model: list every screen, how each is reached, what Back and reload do), then one brief.

## Enforcers

- iron-log: `src/lib/route.test.ts` (round trip, fallback, screen-names-only) and `e2e/navigation.spec.js` (address, Back, reload, sheets); the "a screen needs a row" check is advisory (code review) until a screen ships without one twice (`rule-enforcers.md`).
- Other projects: copy the route test and the navigation spec pattern when a router is added; until then the rule is advisory.

Related: `definition-of-done.md` (add-on row for a new screen), `new-project-order.md`, `feature-delivery.md` (brief question bank), `evidence-labels.md` (Back on a phone is `not run` until tried), ADR 088 in iron-log.
