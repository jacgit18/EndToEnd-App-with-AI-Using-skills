# Frontend integration technique

Reference for the "once the split is justified, the remaining decision is integration technique" step in `SKILL.md`'s "Frontend decomposition" section. This is the *how*; `SKILL.md` decides the *whether*.

## Server-side composition

A server assembles the page from the independently-built pieces before sending HTML to the browser (each micro-frontend renders server-side, or contributes a fragment that's stitched together at the edge/origin).

**Fits:** content-heavy pages where first-paint and SEO matter more than rich client-side interactivity; teams already running server-rendered stacks.

**Cost:** each piece needs a server-side rendering story, not just a client bundle; composing at request time adds a hop and a place for one slow piece to delay the whole page.

## Client-side composition

Pieces are loaded and mounted dynamically in the browser. Module Federation (Webpack) lets independently-built and independently-deployed bundles share dependencies and be composed at runtime without a build-time dependency between them; Single-SPA orchestrates multiple framework apps (React, Angular, Vue side by side) mounted into different regions of one page.

**Fits:** the common case for genuinely independent frontend teams shipping on their own schedule, especially across different frameworks.

**Cost:** shared-dependency versioning (Module Federation can share a library version across pieces, but a mismatch surfaces at runtime, not build time — a version-skew failure mode, same shape as the repo-split version-skew tradeoff on the backend side); a slow or broken piece can degrade the page it's mounted into; more JavaScript shipped overall unless dependency sharing is configured carefully.

## Edge-side composition

Pieces are combined at the CDN or edge layer (edge-side includes, edge functions assembling a response) before reaching the browser.

**Fits:** globally-distributed, latency-sensitive pages where composing at the origin server would add unacceptable round-trip time.

**Cost:** the least mature tooling of the three, and debugging a composition failure means reasoning about edge infrastructure most teams don't otherwise operate.

## Picking one

The same three-tool checklist that makes a one-repo backend layout not hurt (affected-graph CI, `CODEOWNERS`, a directory layout matching the boundaries — see the backend `repo-layout.md`) applies unchanged to a frontend monorepo hosting multiple micro-frontends. The integration technique above is orthogonal to that: it answers "how does the browser end up with one composed page," not "how is the source code organized." A team can use client-side composition (Module Federation) whether the pieces live in one repo or several — repo layout and runtime-composition technique are two separate axes, decided independently.
