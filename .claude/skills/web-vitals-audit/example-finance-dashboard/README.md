# Worked example: the finance-dashboard accessibility audit (2026-10-03)

The scripts that produced `.claude/records/finance-dashboard-accessibility.md`, saved so the next project does not rebuild them. **Examples, not a tool**: routes, labels, button names, fixture JSON and the API paths are this app's. Copy the folder, edit those, keep the method (`../measurement.md`, last section).

Needs: Node, a Chromium (Playwright's), `npm i lighthouse @axe-core/playwright playwright-core` in a scratch folder, Docker (for the proxy step), `CHROME_PATH` set.

| File | What it does |
|---|---|
| `fixture-server.mjs` | Serves the production build with the proxy's headers and returns fixture JSON for the app's GET routes, so login-gated pages render without a login. `DIST=... node fixture-server.mjs` (port 4173) |
| `axe-routes.mjs` | axe (A/AA/AAA + best-practice tags) on every route at 1280px and 320px, plus `scrollWidth` against the viewport (reflow) |
| `target-size.mjs` | Measures every link, button, select, input and checkbox label against 44px |
| `page-states.mjs` | Forces edit rows, error responses, empty and result states with `page.route()` and runs axe on each |
| `keyboard-zoom-forced-colors.mjs` | Third-party origins, Tab reachability and focus ring, 200% text, forced-colors screenshot, visible text for the reading-level check |
| `keyboard-ring-check.mjs` | The re-check after the focus-ring fix (counts every Tab stop, three presses per date field) |

The proxy step (a throwaway Caddy container with the project's real Caddyfile, upstream rewritten to the fixture server, config mounted from under `$HOME`) is described in `../measurement.md`.
