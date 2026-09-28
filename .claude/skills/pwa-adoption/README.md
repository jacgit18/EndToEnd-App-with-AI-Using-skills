# pwa-adoption skill

A gate skill, same shape as `caching-strategy` and `deployment-strategy`. Decides whether a
web app should adopt a Progressive Web App's pieces (manifest/installability, a service
worker, offline scope, push notifications) and, if so, what the service worker's caching
strategy, offline scope, and update lifecycle actually are.

## Where it sits

```
caching-strategy        →  server-side cache in front of a data source           (ADR)
deployment-strategy     →  how a new version of a deployable unit rolls out       (ADR)
resilience-strategy     →  request-path overload/failure protection on a reachable backend
api-interface-style     →  push-vs-poll decision, wire protocol
pwa-adoption            →  installability, offline scope, SW caching + update lifecycle, push plumbing   (ADR)  ← this skill
```

None of these own the browser-resident cache/offline layer of a web app; this skill fills
that gap. It borrows the *shape* of `caching-strategy`'s gate (a real pressure/driver, per-
data-class staleness, a load-bearing-vs-optimization-style split) but the questions are
different because the cache lives in the browser, not in front of a shared data source, and
because "offline" introduces a write-scope question `caching-strategy` never has to ask
(nothing in a server-side cache design lets a client keep *writing* while the source is
unreachable).

## The shape

Refuses to recommend a service-worker strategy, offline scope, or manifest until the user
supplies:

- **the driver** — install convenience, a named offline scenario, or push re-engagement;
  never "PWAs are best practice"
- **offline scope per feature area** — unavailable / read-only-from-cache / read-write with
  a sync queue, with financial vs non-financial mutations called out separately
- **staleness tolerance per data class** — same question as `caching-strategy`, at the
  browser layer
- **update tolerance** — forced immediate update vs deferred-until-tab-close, and which
  change classes justify forcing it
- **target platforms** — iOS Safari is treated as a genuinely different platform (no install
  prompt event, no background sync, push only 16.4+, storage eviction after ~7 days idle),
  not a lesser version of Chrome/Android

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate, challenge-the-proposal, output contract. |
| `service-worker-strategies.md` | Caching strategy per route class, precache vs runtime
  cache, cache versioning/cleanup, the `skipWaiting`/`clients.claim` update-lifecycle
  trade-off, background sync + idempotency, web-push subscription/VAPID/`push`-event
  mechanics. |
| `manifest-and-installability.md` | Manifest fields, icon sizes incl. maskable,
  per-platform install criteria (Chrome/Edge `beforeinstallprompt` vs iOS's manual
  add-to-home-screen with no prompt event), the HTTPS requirement, iOS storage eviction,
  Lighthouse/DevTools auditing. |

## Output

1. A recommendation block in chat (driver, manifest-only-ruled-out check, route classes and
   their caching strategy, offline scope per feature area, update lifecycle, manifest,
   platform coverage, push plan, kill-switch, metrics, tradeoffs).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md` — same directory and numbering.

Stops before implementation (the service worker file, a build-tool plugin, the manifest
JSON).

## Interaction with sibling skills

- **Defers to `caching-strategy`** for any server-side cache; hands back to that skill's
  freshness rules (`Cache-Control`/`ETag`) rather than contradicting them at the SW layer.
- **Defers to `deployment-strategy`** for the rollout mechanism itself; only owns the
  already-installed service worker's own activation/versioning once a build ships. A
  fleet-wide bad-version eviction is this skill's kill-switch mechanism, invoked under a
  `deployment-strategy` rollback call.
- **Defers to `resilience-strategy`** for overload/failure protection on a reachable
  backend; this skill's offline fallback is for no network at all.
- **Defers to `api-interface-style`** for whether an API should push at all and the wire
  protocol; once web push to this PWA is chosen, the subscription plumbing is here.
- **Defers to `data-access-layer`** for how the server itself reads/writes data.
- **Chains to `test-case-discovery`** for the idempotency/concurrency cases a sync-queue
  design implies once built.
- **`learning-gate`** should hand off to this skill on PWA/offline/service-worker design
  questions rather than running its own rep gate (see `learning-gate` Step 3 — Architecture
  decision row and `step3-rows.md`).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `caching-strategy` (browser vs server cache), `deployment-strategy` (rollout vs SW
update lifecycle), `resilience-strategy` (offline vs overload degradation), and
`api-interface-style` (push-vs-poll vs web-push plumbing).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside
`database-architecture` and `caching-strategy`, reusing `database-architecture`'s
`adr-template.md`.

```
cp -r .claude/skills/pwa-adoption /path/to/other-repo/.claude/skills/
```
