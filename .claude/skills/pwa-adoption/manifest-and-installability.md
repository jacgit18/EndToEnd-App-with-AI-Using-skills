# Manifest and Installability

Worked once the gate in `SKILL.md` is satisfied and, per step 1 of the process, the driver
survives past "would a manifest alone satisfy it."

## Manifest fields

Required for the app to be considered installable by Chrome/Edge/Android:

| Field | What it does |
|---|---|
| `name` | Full app name, shown on the install prompt and splash screen. |
| `short_name` | Shown under the home-screen icon where space is tight. |
| `start_url` | The URL launched when opened from the home screen — usually `/` or a
  dashboard route; include a query param (`?source=pwa`) if you want to distinguish
  installed launches in analytics. |
| `display` | `standalone` (no browser chrome — the normal PWA choice) or `fullscreen`;
  `browser` opts out of the app-like frame entirely. |
| `icons` | At least a 192×192 and a 512×512 PNG. Include one marked `"purpose": "maskable"`
  with safe-zone padding (icon content within the inner ~80% of the canvas) — Android
  applies a mask shape and will crop a non-maskable icon awkwardly. |

Recommended:

- `theme_color` — the browser UI (status bar, task switcher) color.
- `background_color` — shown on the splash screen before the app's own CSS loads.
- `scope` — the URL range the PWA is considered to control; defaults to `start_url`'s
  directory.
- `description`, `orientation`, `shortcuts` (jump-list-style quick actions from a long-press
  on the icon).

## Per-platform install criteria

**Chrome / Edge (desktop and Android)** — installability is criteria-based: served over
HTTPS, a valid manifest with the required fields above, a registered service worker (even a
minimal one — Chrome requires *a* service worker to fire `fetch`, not necessarily one that
does meaningful caching), and enough engagement (the browser's own heuristic, not something
the app controls directly). Once met, the browser fires a `beforeinstallprompt` event that
the app can capture and defer, showing its own "Install" UI at a moment of its choosing
instead of the browser's default mini-infobar. Calling `.prompt()` on the saved event shows
the native install dialog.

**iOS Safari** — has no `beforeinstallprompt` event and no programmatic install prompt at
all. The only path is the user manually choosing Share → "Add to Home Screen." The app
cannot detect or trigger this — the only lever is instructing the user (an in-app banner
explaining the manual steps, shown once, dismissible). iOS reads a narrower set of
`<meta>` tags for its home-screen behavior in addition to (or instead of) the manifest:
`apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, and
`apple-touch-icon` links for the icon (a maskable manifest icon is not guaranteed to be used
the same way). Splash screens on iOS are configured via a set of exact-pixel-size
`apple-touch-startup-image` link tags per device, not the manifest's `background_color`.

**Desktop (Chrome/Edge)** — installs as a windowed app; `display: standalone` or
`window-controls-overlay` (lets the app draw into the title-bar area) are the relevant
`display` values.

## HTTPS requirement

Service workers and the install criteria both require HTTPS (or `localhost` for local
development) — there is no way around this for a real deployment. If the app is currently
plain HTTP, that's a prerequisite to name before any of the rest applies.

## iOS storage eviction

iOS Safari (and installed iOS PWAs) can evict a site's Cache Storage and IndexedDB data
after roughly a week of no interaction (Safari's Intelligent Tracking Prevention storage
policy) — a materially shorter and less predictable retention window than
Chrome/Edge/Android, which don't apply the same eviction. Any offline-scope design (gate item
2) that assumes cached data survives for a stated period must treat iOS as the binding
constraint if iOS is a target platform, not an average across platforms.

## Auditing

- **Lighthouse's PWA audit** (Chrome DevTools → Lighthouse, or `lighthouse --preset=pwa`)
  checks the installability criteria, manifest validity, and basic offline behavior (does
  the start URL respond with a 200 when offline) mechanically — run it after implementation,
  not as a substitute for the gate's design decisions.
- **Chrome DevTools → Application panel** — inspect the registered service worker's state
  (installing/waiting/active), force an update, unregister it, inspect Cache Storage
  contents and IndexedDB, and simulate offline via the Network panel's throttling dropdown.
  This is the primary tool for debugging a PWA defect (stuck version, missing offline
  fallback, wrong cache contents) and is scriptable via browser-automation tooling for an
  agent to inspect directly, unlike a production issue that only reproduces on a real device.
