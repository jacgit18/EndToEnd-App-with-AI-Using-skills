# Service Worker Strategies

Worked once the gate in `SKILL.md` is satisfied. Covers caching strategy per route class,
cache versioning, the update-lifecycle trade-off, background sync, and web push mechanics.

## Caching strategies, and which route class each fits

| Strategy | How it works | Fits |
|---|---|---|
| **Cache-first** | Serve from cache if present; only hit network on a cache miss. | Static, content-hashed build assets (JS/CSS/fonts/images) that never change under a fixed URL — a new deploy ships a new hash, so this is safe by construction. |
| **Network-first** | Try the network; on failure (offline, timeout), fall back to cache. | Navigation/HTML requests (so a logged-in user always gets the current shell when online) and any API GET whose staleness budget is short. Set an explicit timeout (e.g. 3–5s) rather than waiting on a hung connection before falling back. |
| **Stale-while-revalidate** | Serve from cache immediately, then fetch in the background and update the cache for next time. | API GETs whose staleness tolerance is "a bit old is fine" (item 3 in the gate) — the user sees something instantly, and the next open is fresher. Never for a value where "the version I last saw" being wrong causes a real cost. |
| **Cache-then-network** (a variant surfaced to the app, not just the SW) | Return the cached response immediately *and* let the page re-render when the network response lands, showing both a fast paint and a freshness signal. | Read views that should visibly label "cached" vs "live" data, e.g. an account summary opened offline. |
| **Network-only** | Never touch the cache. | Auth/session endpoints, and every write/mutation endpoint. Caching a login check or a POST is the most common PWA caching bug — it silently serves a stale auth decision or drops a write into the cache instead of sending it. |
| **Cache-only** | Serve only from a precache, never hit network. | Rare — an offline-fallback page/asset that is deliberately never revalidated. |

## Precache vs runtime cache

- **Precache** — assets listed at build time and fetched into the cache during the service
  worker's `install` event (the app shell: HTML shell, critical CSS/JS, the offline-fallback
  page). Guarantees they're present before the app is ever used offline.
- **Runtime cache** — populated as requests happen, per the strategy table above. Everything
  that isn't known at build time (API responses, user-specific data) is runtime-cached.

## Cache versioning and cleanup

- Name caches with a version segment (`app-shell-v3`, `api-cache-v3`) tied to the build.
- In the `activate` event, enumerate existing cache names and delete any that don't match
  the current version — otherwise every deploy leaves the previous version's cache
  resident, growing storage use with no benefit.
- Content-hashed filenames for static assets make cache-first safe without a version bump
  on the entry itself; the version segment is still needed so `activate` knows what to
  delete.

## The update-lifecycle trade-off

A new service worker installs alongside the currently active one and stays **waiting** until
every tab controlled by the old worker closes — this is the safe default; it never swaps
code out from under an open, in-progress session.

- **`skipWaiting()`** in the new worker's `install` handler skips that wait and activates
  immediately. Combined with **`clients.claim()`** in `activate`, every open tab is taken
  over by the new worker right away — including mid-request. This is what "immediate" update
  tolerance (gate item 4) requires, but it needs the app to either tolerate a silent
  mid-session swap or to explicitly detect the `controllerchange` event and prompt/force a
  reload so the page's in-memory JS matches the new worker.
- **Deferred** (no `skipWaiting`) means a tab keeps running the old code — and the old
  cached assets — until the user closes and reopens it. Safer for in-flight state, but a
  shipped fix (including a security fix) doesn't reach an already-open tab until then. Pair
  this with a visible "update available — refresh" banner triggered by listening for the
  new worker entering the `waiting` state, so the user has a way to opt in early.
- Whichever is chosen, **do not silently reload a tab with an unsaved form or an in-flight
  financial submission** — check for that state before forcing a reload, or defer until the
  action completes.

## Background sync for offline writes

- A write made offline is stored locally (IndexedDB, or the Background Sync API's
  registered tag where supported — Chrome/Edge/Android only, not iOS Safari) and replayed
  when connectivity returns.
- **Idempotency is mandatory, not optional.** A flaky reconnect can trigger a sync attempt
  more than once for the same queued write; the server side must accept a client-generated
  idempotency key (or the write's own natural key) and treat a duplicate as a no-op, not a
  second effect. Without this, "offline writes sync" quietly becomes "offline writes
  sometimes duplicate."
- Show the user the queued state explicitly (a pending-sync indicator), and what happens if
  a queued write is later rejected by the server (validation failure, conflict) — a silent
  drop is not acceptable for a write the user believed had succeeded.
- iOS Safari has no Background Sync API: queue in IndexedDB and flush on next foreground
  load (`visibilitychange` / app open) instead of relying on a background trigger.

## Web push mechanics

1. **Permission** — request `Notification.requestPermission()` only on a clear user action
   (a toggle, "enable notifications"), never on page load; an unprompted browser permission
   dialog on first visit is the single most common reason users deny it permanently.
2. **Subscription** — `pushManager.subscribe()` with the app's VAPID public key produces a
   subscription object (endpoint + keys) sent to the backend and stored against the user.
3. **Sending** — the backend uses the VAPID private key to sign and send a payload to the
   subscription's push service (browser-vendor-operated; the app never talks to the device
   directly).
4. **Receiving** — the service worker's `push` event handler reads the payload and calls
   `registration.showNotification(...)`; a `notificationclick` handler defines what happens
   when the user taps it (usually focus-or-open a specific URL).
5. **Lifecycle** — a subscription can expire or be revoked by the browser; handle the
   `pushsubscriptionchange` event to re-subscribe, and prune dead subscriptions server-side
   on a send failure rather than retrying indefinitely.
6. iOS Safari supports web push only from iOS 16.4+, and only for a PWA that has been added
   to the home screen (not from a regular Safari tab) — a materially narrower path than
   Chrome/Edge/Android.
