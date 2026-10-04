---
name: pwa-adoption
description: Gated decision for making a web app installable/offline-capable: service-worker caching, offline scope, update lifecycle, manifest/install criteria, push. Use when "should we make this a PWA", "add offline support", "do we need a service worker". Not `caching-strategy` (server-side cache), `deployment-strategy` (rollout), `resilience-strategy` (overload), or Lighthouse scores (`web-vitals-audit`).
---

# PWA Adoption

Take a web app and decide whether it should become a Progressive Web App — installable, and
offline-capable to some degree — and if so, what the service worker caches and how, what
happens with no network, how a new version reaches an open tab without breaking it mid-use,
and whether push notifications are worth the plumbing. A service worker is a second,
browser-resident cache layer sitting in front of everything the page fetches, including your
own API, with its own staleness and versioning problems — not free complexity to bolt on
because "PWAs are best practice." The skill makes the user name the actual driver and the
offline/write scope before any caching strategy or manifest field is decided, recommends one
design, and writes an ADR.

## When to use

- The user asks **whether to make the app a PWA**, or adopt one piece standalone: "add a
  service worker", "make it installable", "add an app icon to the home screen", "does this
  need a manifest".
- The user wants **offline support**: "it should still work with no signal", "cache the app
  so it opens on a train", "what happens if the API is unreachable".
- The user wants **push notifications** on the web app.
- The user reports a **PWA defect**: users stuck on a stale version after a deploy, the
  install prompt never shows, offline doesn't actually work, iOS behaves differently from
  Android/desktop.
- The user proposes a PWA design and wants it pressure-tested ("cache everything with a
  service worker and skipWaiting on activate").

## Out of scope — hand these off

- **How browser e2e tests run around a service worker** (block it, or a spec of its own) → `browser-test-tooling`.
- **Server-side cache** (Redis, CDN, reverse proxy, DB query cache) → `caching-strategy`.
  How a service worker reads that skill's `Cache-Control`/`ETag` headers is here; keep freshness rules consistent.
- **Rollout mechanism for a new deploy** (blue-green, canary, rollback trigger) →
  `deployment-strategy`. This skill owns the narrower, adjacent problem of how an
  already-installed service worker notices and activates a new build.
- **Request-path overload protection** on a reachable-but-struggling backend (rate limits,
  circuit breakers, retries, graceful degradation) → `resilience-strategy`. This skill's
  offline fallback is for genuinely no network, a different condition.
- **Whether an API should push at all, and the wire protocol** (SSE/WebSocket/webhook vs
  polling) → `api-interface-style`. Once web push to this PWA is the chosen mechanism, the
  subscription/VAPID/service-worker plumbing is here.
- **How app code reads/writes the database** → `data-access-layer`. Caching a response
  client-side for offline reads is this skill; how the server built it is not.
- **Native app store packaging** (Capacitor/Cordova/React Native) — out of scope entirely.
- **Push content, cadence, opt-in copy** — product decision, not this skill's plumbing.
- **General instrumentation, SLOs, and alerting** once this skill's own PWA metrics (install
  rate, offline-session count, update-success rate) are named → `observability-strategy` for
  turning them into dashboards/alerts/retention policy.
- **Implementation** — the service worker file, a build-tool plugin (Workbox,
  `vite-plugin-pwa`), the manifest JSON. The skill stops at the ADR.

---

## The gate

**Facts you may surface from the repo / infra** (state for confirmation): current state
(manifest? registered service worker? HTTPS?); app shape (static shell + API-driven data vs
server-rendered; how many route classes — static assets, API GETs, navigation, auth,
mutations); target platforms (Chrome/Edge/Android have full support incl.
`beforeinstallprompt` and background sync; iOS Safari has none of those, push only from
16.4+, and evicts storage after ~7 days of inactivity — a different platform, not a smaller
version of the same one).

**Judgment calls that must come from the user.** If any is missing, name it and stop:

1. **The driver** — install convenience, a concrete offline scenario (name it), or
   re-engagement via push. "Best practice", "basically free with the framework", "the
   competitor has one" is not a driver — it's a reason to ask whether a manifest with *no*
   service worker (installable, no caching risk) already satisfies it.
2. **Offline scope, per feature area** — unavailable, read-only-from-cache (staleness shown
   to the user), or read/write with a sync queue. Read/write offline needs an idempotent
   replay (see `test-case-discovery`'s concurrency category). For a finance app: an
   offline-queued financial write (a transfer, a submitted payment) is a different risk
   class from a queued local-preference write — the user must say which each mutation is.
3. **Staleness tolerance per data class** — same shape as `caching-strategy`'s question, at
   the browser layer: how old may a cached read be, and what breaks if it's wrong (a stale
   balance shown as current is not cosmetic).
4. **Update tolerance** — force every open tab onto a new version immediately
   (`skipWaiting`/`clients.claim`, which can interrupt in-flight state), or let a tab keep
   running the old version until closed? Name which change classes (display bug vs security
   fix vs pricing-logic fix) justify forcing it.
5. **Push, if wanted** — trigger, sender, and a plan for VAPID keys and
   subscription/unsubscribe handling. Don't bundle it in by default.
6. **Operational capacity** — who owns version bumps and can ship a kill-switch (an
   empty/pass-through service worker that unregisters itself) if one ships broken.

"Let's make it a PWA" with 1–6 absent is not valid input. **Pressure does not open the
gate** — a service worker caching the wrong things, or an update lifecycle that strands
users on a broken version, is worse than no PWA: unlike a normal bug, it can survive
redeploys until the user manually clears storage.

---

## Challenge a proposed approach

Test against `service-worker-strategies.md` / `manifest-and-installability.md`:

- **"cache everything"** — including auth and mutation endpoints? Those want network-only.
- **"skipWaiting + clients.claim on every deploy"** — does the app tolerate a mid-session
  reload with in-flight requests or unsaved state (item 4)?
- **"stale-while-revalidate for the API"** — tolerable for every data class (item 3), or
  does one need network-first with a short timeout instead?
- **"writes queue and sync later"** — per mutation type (item 2): financial? Is replay
  idempotent? What does the user see while queued?
- **"it'll just work on iPhone too"** — no `beforeinstallprompt`, no background sync, push
  only 16.4+, cache eviction after ~7 days idle. If iOS is targeted, it needs its own
  fallback, not the same design ported over.
- **"just a service worker, no manifest"** — installability and offline caching are
  separate; confirm which one is actually wanted.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

**A defect report** (stuck version, no offline, install prompt missing) means one already
exists — read the existing caching strategy, update code, and manifest first, state what you
found, and treat 1–7 below as auditing it against the gate rather than a fresh design.

1. **Confirm the driver survives without a service worker.** A manifest alone (icons,
   `start_url`, `display: standalone`) gives install/home-screen behavior with none of the
   caching or update-lifecycle risk. If that's the whole ask, stop there.
2. **Classify every route class** into a strategy from `service-worker-strategies.md`:
   static assets (cache-first, content-hashed so a deploy is a cache-miss by construction),
   navigation (network-first + cached offline-fallback page), API GETs (per staleness class:
   network-first / stale-while-revalidate / cache-then-network), auth and mutations
   (network-only).
3. **Design offline scope** per feature area (item 2): visible "offline — showing cached
   data from Xm ago" for reads, a background-sync queue with idempotent replay for writes,
   or an explicit unavailable message. Never silently fail a write.
4. **Set the update lifecycle** (item 4): immediate (forced/prompted reload) vs deferred
   (new worker waits for all tabs to close). Version the cache name so `activate` deletes
   stale caches.
5. **Decide push** (item 5), or explicitly skip it.
6. **Fill the manifest** from `manifest-and-installability.md`, naming the install path per
   platform including the iOS fallback if targeted.
7. **Name the kill-switch** and the metrics and revisit trigger, then recommend and record.

Reference files:

- `service-worker-strategies.md` — caching strategies per route class, precache vs
  runtime-cache, cache versioning/cleanup, the update-lifecycle trade-off and the
  "new version available" prompt alternative, background sync + idempotency, web-push
  mechanics.
- `manifest-and-installability.md` — manifest fields, icon sizes incl. maskable, per-platform
  install criteria (Chrome/Edge heuristics + `beforeinstallprompt`, iOS's manual add-to-home-
  screen with no prompt event), the HTTPS requirement, iOS storage eviction, Lighthouse/
  DevTools auditing.

---

## Output

**1. In chat, a recommendation block:**

```
Driver:               <install convenience / offline-with-no-signal / re-engagement via push>
Manifest-only ruled out: <yes/no — would a manifest with no service worker satisfy the driver>
Route classes:         <static | navigation | API GET (per staleness class) | auth | mutations>
Caching strategy:      <cache-first | network-first | stale-while-revalidate | cache-then-network | network-only> per class, with why
Offline scope:         <per feature area: unavailable | read-only-from-cache | read/write with sync queue (idempotent)>
Update lifecycle:      <immediate (skipWaiting/clients.claim + prompt) | deferred>, cache versioning: <scheme>
Manifest:              <name, short_name, start_url, display, theme/background color, icon set incl. maskable>
Platform coverage:     <Chrome/Edge/Android: full | iOS Safari: manual add-to-home-screen, no push <16.4, storage eviction ~7d idle>
Push notifications:    <not wanted | trigger, sender, VAPID/subscription plan>
Kill-switch:           <how a bad service-worker version gets unregistered fleet-wide>
Metrics:               <install rate, offline-session count, update-success rate, push opt-out rate>
Agent-drivable:        <can an agent inspect service-worker/cache state directly — Chrome DevTools Application panel via browser automation, Lighthouse PWA audit — or only via a real browser session>
Tradeoffs accepted:    <2–4 concrete costs: staleness window, update-lifecycle risk, iOS gap, new client-side failure surface>
Not chosen because:    <one line per rejected strategy/scope>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using
`database-architecture`'s `adr-template.md` (same directory and numbering). Fill "Revisit
when" with a concrete trigger — "iOS becomes required and needs its fallback built", "a
mutation moves from local-preference to financial and the sync-queue risk changes", "push
adoption is near zero and the plumbing isn't earning its keep."

Then stop. Implementation is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — driver named, offline scope decided per feature area
with write cases called out, staleness and update tolerance stated, platforms named — and
wants a review or tie-break rather than a Socratic pass, they say so and you give a direct
recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Field techs use the dashboard on job sites with spotty signal. They need to see the
> customer's last-known account status and log a completed job even with no bars, syncing
> when back online. Mostly Android tablets, some iPhones. Job-logging bugs need to reach
> them fast; cosmetic fixes can wait."

Gate satisfied — driver is offline-with-no-signal (item 1), concrete. Account status:
cache-then-network read, staleness "minutes, labeled as of last sync". Job-logging: write,
background-sync queue, idempotent on job ID. Update lifecycle split by change class (item
4): job-logging fixes force `skipWaiting` + prompt, cosmetic fixes wait for tab close. iOS
named as a target: no background sync there, so the write queue needs an IndexedDB-plus-
foreground-flush fallback instead, and install is manual Add to Home Screen. Kill-switch: an
empty pass-through worker reserved for emergency eviction. Write the ADR; revisit when iOS
gets background-sync support, or job-logging volume makes queue depth worth alerting on.

> "Let's make the app a PWA, it's basically free with Vite's plugin."

Gate not satisfied — no driver beyond "easy to add" (item 1), no offline scope (item 2), no
update tolerance (item 4). Name what's missing, note that a wrong caching strategy can
strand a user on a stale, broken version until they manually clear site data, and ask what's
actually driving it. Do not recommend a design yet.

> "Our dashboard is slow — can we cache the API responses at the edge so it's faster for
> everyone?"

Does not fire: a server-side cache benefiting every user identically, not a per-browser
offline/installability decision — `caching-strategy` owns it. "Can it also work with no
signal" in the same conversation would be this skill.

---

## Portability

Needs no repo setup. Writes an ADR to `docs/architecture/decisions/` by default (follow the repo's own convention if it has one), in `database-architecture`'s ADR format; if `database-architecture` isn't installed, use this skeleton: title `NNN. <decision>`; Status and Date; **Context** (the gate answers, plainly); **Decision** (the recommendation block); **Consequences** (accepted costs, rejected alternatives); **Revisit when** (a concrete trigger).

Depends on: `caching-strategy`, `deployment-strategy`, `resilience-strategy`, `web-vitals-audit`, `browser-test-tooling`, `api-interface-style`, `data-access-layer`, `observability-strategy`, `test-case-discovery`, `database-architecture`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: no `caching-strategy` → design only the service-worker cache and name any server-side cache as a separate decision; no `deployment-strategy` → the service-worker update lifecycle is still covered here, the server rollout is not; no `web-vitals-audit` → for a poor Lighthouse number, measure the production build with the service worker bypassed first.

## Routing boundaries (full)

- Use when someone says "should we make this a PWA", "add offline support", "make it
  installable", "do we need a service worker", "add push notifications to the web app", "add
  an app icon to the home screen", "the app should still work with no signal", "why isn't
  the install prompt showing", "users are stuck on an old version after we deployed",
  "should the service worker cache everything", or proposes a service-worker/manifest design
  and wants it checked. See "Out of scope" above for the sibling carve-outs
  (`caching-strategy`, `deployment-strategy`, `resilience-strategy`, `api-interface-style`,
  `data-access-layer`) — not repeated here. A poor Lighthouse number is `web-vitals-audit` (SW bypassed).
