# Build or library

## Contents

- [The option ladder](#the-option-ladder)
- [Never build these](#never-build-these)
- [Build it yourself when](#build-it-yourself-when)
- [Options by functionality](#options-by-functionality)
- [Keeping the exit cheap](#keeping-the-exit-cheap)
- [Recording the call](#recording-the-call)
- [Anti-patterns](#anti-patterns)

Whether a package is safe to install at all (typosquats, malware, install scripts, owner approval) is `dependency-security.md`; run it on every pick, whatever the rung.

The question *before* `library-vetting.md`: does this job need a dependency at all, or does the
platform already do it, or is it small enough to own? `library-vetting.md` picks *which* package
once a package is the answer; this file decides whether it is. The standing rule is
`.claude/rules/dependency-selection.md`; this is its reference.

Every dependency is a standing cost even when it is free: upgrades, advisories, breaking majors,
transitive packages and licenses, bundle weight, and the day its maintainer stops. Every
line you write yourself is also a standing cost: bugs, edge cases, tests and docs that are now
yours. The choice is which cost is smaller for *this* job, not "libraries bad" or "never
reinvent".

## The option ladder

Take the first rung that does the job well. Climb only when the rung below falls short on a
named need.

| Rung | Option | Typical cost | Fits when |
|---|---|---|---|
| 0 | **Don't build it** — cut or defer the feature | none | the need is speculative (`feature-planning.md` Inbox) |
| 1 | **Platform / standard library** — browser APIs, `Intl`, `fetch`, `URL`, `crypto.subtle`, CSS; Python stdlib (`datetime`/`zoneinfo`, `csv`, `decimal`, `json`, `secrets`, `hashlib`, `pathlib`) | none added | the built-in covers the cases you have |
| 2 | **A dependency already in the tree** — the framework's own feature, or a package you already ship | none added | it does the job without contortion |
| 3 | **Write it** — a small module you own, with tests | your time + upkeep | under ~150 lines, a well-understood problem, no security or standards edge (see the never-build list) |
| 4 | **Copy it in (vendor)** — paste a small, stable, permissively licensed function with its license header and source link | you own its upkeep | the library is mostly unused weight around one function, and it is done (no churn) |
| 5 | **Small focused library** — one job, few or zero transitive deps | a vetted dep | the problem has edge cases you'd rather not learn (dates, parsing, a11y widgets) |
| 6 | **Large library or framework** — shapes how code is written | high lock-in | it replaces a lot of your code and is the ecosystem default |
| 7 | **Managed service / SaaS** — someone else runs it | recurring bill, data leaves the machine, vendor exit | running it yourself is the bigger risk (email delivery, payments, bank links); price it with `technical-cost-decision` |

Rungs 5–7 then go through `library-vetting.md` (structural or load-bearing depth) or
`technical-cost-decision` (rung 7).

## Never build these

Use a well-known library (or the platform) even when it looks small. The failure is silent and
the cost is a breach, data loss or wrong money:

- **Cryptography** — hashing passwords (argon2 / bcrypt / scrypt via a library), encryption,
  signing, random tokens (platform CSPRNG: `crypto.getRandomValues`, Python `secrets`), JWT
  verification.
- **Authentication and sessions** — login, OAuth/OIDC flows, session fixation, CSRF tokens. Use
  the framework's auth or a vetted library or service. Roles and permissions after login are
  `access-control-modeling`; it does not cover authentication.
- **Parsing untrusted or standardised formats** — HTML sanitisation (DOMPurify, bleach/nh3), XML,
  YAML, Markdown-to-HTML, CSV with quoting and encodings, email addresses beyond a sanity check,
  URLs (`URL`, `urllib.parse`), multipart uploads.
- **Dates, times and time zones** — DST, leap years, zone rules. `Intl` / `zoneinfo` /
  `Temporal` (where supported, else a polyfill) first, then a date library.
- **Money and decimals** — never floats. `Decimal` in Python, integer minor units or a decimal
  library in JS; currency formatting via `Intl.NumberFormat`.
- **Database drivers, connection pooling, migrations** — the ORM or migration tool, not
  hand-rolled schema scripts.
- **Unicode and text** — normalisation, collation, grapheme counting, slugs in non-Latin
  scripts (`Intl.Segmenter`, `unicodedata`).
- **Accessible complex widgets** — combobox, date picker, modal focus trap, menu. Native element
  first (`<dialog>`, `<select>`, `<input type=date>`); otherwise a headless accessible library.
- **Protocol clients** — TLS, HTTP/2, SMTP, WebSocket framing.

## Build it yourself when

All of these hold:

- the job is small and well understood (a debounce, a `groupBy`, a retry with backoff, a
  formatter for your own data, a tiny event emitter);
- it is not on the never-build list;
- the library would bring more code, transitive packages or bundle weight than it saves;
- you will write tests for it, as for any other code you own;
- the platform does not already do it (check rung 1 first: `structuredClone`, `Array.prototype.
  toSorted`, `Object.groupBy`, `Intl.RelativeTimeFormat`, `AbortSignal.timeout`, `itertools`,
  `functools.cache`, `dataclasses`).

## Options by functionality

Lean = the default first look for a small-to-medium web app (React/TS front end, Python back
end). It is a starting point, not a verdict: walk the ladder when the case differs.

| Functionality | Platform / stdlib | Build it? | Library (when to reach for one) | Service | Lean |
|---|---|---|---|---|---|
| Utility helpers (debounce, groupBy, chunk, deep clone) | `structuredClone`, `Object.groupBy`, `itertools` | yes, a few lines each | lodash-es per-function import only if many are needed | — | build / platform |
| Date and time display | `Intl.DateTimeFormat`, `Intl.RelativeTimeFormat`, `zoneinfo` | formatting only | date-fns / Day.js / Luxon when doing zone math or calendars | — | platform → small lib |
| Money, decimals, currency | `Intl.NumberFormat`, Python `Decimal` | no (never floats) | dinero.js / big.js for JS arithmetic | — | platform + integer minor units |
| HTTP client | `fetch` + `AbortSignal.timeout`; `urllib` | a thin wrapper (base URL, auth header, errors) | ky / axios only for interceptors at scale; `httpx` in Python | — | platform + own wrapper |
| Input validation / schemas | HTML constraint validation; Pydantic (often already in tree) | simple field checks only | Zod / Valibot when types and runtime checks must match | — | lib if shared client+server schema |
| Forms | native form + `FormData` | small forms | React Hook Form for many fields, dynamic arrays | — | native → lib at size |
| State management | React state, context, URL params | yes, start here | Zustand / Redux Toolkit when cross-tree state is real; TanStack Query for server cache | — | built-in first |
| Routing | — | no for SPAs beyond two screens | the framework's router or React Router | — | framework |
| Data fetching and cache | `fetch` | a hook for one or two endpoints | TanStack Query / SWR for caching, retries, invalidation | — | lib once caching matters |
| Charts | SVG + CSS | sparklines, simple bars | a chart lib (Recharts, visx, uPlot) for axes, zoom, many series; lazy-load it | — | build small, lib for real charts |
| Tables | `<table>` + CSS | sort/filter on small data | TanStack Table for virtualisation, column state | — | native → headless lib |
| UI components | native elements, CSS | buttons, cards, layout | headless accessible lib (Radix, React Aria) for complex widgets | — | native + headless lib |
| Styling | CSS, custom properties, `@layer` | yes | CSS framework only if the team already uses one | — | plain CSS |
| Icons | inline SVG | yes, a sprite or a few components | an icon set with per-icon imports | — | inline SVG |
| CSV / spreadsheet import | Python `csv`; JS none robust | no for real-world files | PapaParse (JS); pandas only if already in tree | — | stdlib (Py) / lib (JS) |
| Markdown / rich text | — | no (sanitisation) | marked/markdown-it + DOMPurify; a rich-text editor lib | — | lib |
| Auth, sessions, passwords | `crypto.subtle`, `secrets` | **never** | framework auth, argon2-cffi or pwdlib (not passlib: unmaintained), an OIDC lib | Auth0 / Clerk / Supabase Auth | framework / lib; service if SSO needed |
| Email sending | `smtplib` | no | provider SDK | Postmark / SES / Resend | service (deliverability) |
| Payments | — | **never** | provider SDK | Stripe etc. | service |
| Bank / brokerage data | — | **never** scrape | provider SDK | Plaid etc. | service |
| Search | SQL `LIKE`, Postgres full-text | yes on Postgres | — | Algolia, or Meilisearch (also self-hostable), at scale | Postgres FTS |
| Background jobs | `asyncio`, cron, FastAPI `BackgroundTasks` | simple scheduled jobs | Celery / RQ / Arq when retries and durability matter | SQS etc. | built-in → queue lib |
| Caching | `functools.cache`, HTTP cache headers | in-process memo | Redis client when shared across processes | managed Redis | built-in (`caching-strategy`) |
| Logging / metrics | `logging`, `console` | structured log helper | structlog, OpenTelemetry SDK | Sentry / Grafana Cloud | stdlib → OTel (`observability-strategy`) |
| Config and env | `os.environ`, `import.meta.env` | a typed loader | pydantic-settings | secrets manager | small own loader (`config-and-secrets-management`) |
| Feature flags | config constant, env var | yes, a typed object | OpenFeature / Unleash at scale | LaunchDarkly | build |
| i18n | `Intl.*` | one language: none | i18next / FormatJS for plurals and many locales | — | platform → lib |
| PDF / image generation | canvas, `<img>` | no | a PDF or image lib | — | lib |
| Testing | `node:test`, `unittest` | no | Vitest / pytest / Playwright (`test-strategy`, `browser-test-tooling`) | — | the project's runner |
| Build tooling | — | no | Vite / esbuild / uv | — | ecosystem default |

## Keeping the exit cheap

Whatever rung wins:

- **Wrap structural and load-bearing libraries behind your own seam** — one module
  (`lib/http.ts`, `app/clock.py`) that the rest of the code imports. Swapping the library then
  touches one file. This is the same seam idea as `parallel-agent-structure.md` rule 5.
- **Do not let a library's types spread** through every module; convert at the seam.
- **Pin and lock** — lockfile committed, dependency update bot or a monthly update slot, `npm
  audit` / `pip-audit` in CI.
- **Lazy-load heavy front-end libraries** (`import()`) so they stay off the first screen
  (`web-accessibility-and-lighthouse.md`).
- **Count before adding** — the direct and transitive package delta goes in the PR body
  (`npm ls --all | wc -l` or `uv tree` before and after).

## Recording the call

- Routine (rung 1–3, or a vetted rung-5 util): one line in the PR body — what was chosen and the
  rung below that fell short.
- Structural or load-bearing (rung 5–7 that shapes a subsystem): an ADR in `DECISIONS.md` with
  the ladder walk, the `library-vetting.md` snapshot, the seam, and a revisit trigger. Note the
  new technology and lock-in in the feature's `FEATURE-PLAN.md` row.
- Built in-house to avoid a dependency: say so in the module's header comment, with the library
  it replaces and the condition that would switch to it ("move to date-fns if we need zone math").

## Anti-patterns

| Anti-pattern | Looks like | Fix |
|---|---|---|
| **npm-install reflex** | A 40-package dependency for a 5-line helper | Walk rungs 1–3 first |
| **Not-invented-here** | Hand-rolled password hashing, CSV parser or date math | Never-build list; use the library |
| **Platform blind spot** | A library for what `Intl`, `fetch` or `zoneinfo` already do | Check rung 1 every time |
| **Unwrapped load-bearing lib** | Library types imported in 60 files | Seam module; convert at the edge |
| **Vendored and forgotten** | Copied code with no source link or license | Header with source, version and license |
| **Build with no tests** | "It's only 80 lines" | Owned code gets tests like any other |
| **Dependency added silently** | New package with no PR note | Package delta and the reason in the PR body |
