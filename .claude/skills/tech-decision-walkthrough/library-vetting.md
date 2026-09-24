# Library vetting

The axes and checks for a decision whose shape is **"which library / package do we pull in
for X"** — a validation library, an HTTP client, a date library, a state manager, a CLI
parser, a chart library. It is the axes-library entry `decision-loop.md` doesn't have: the
generic entries there (runtime, framework, datastore, data-access, …) cover the load-bearing
choices, and their axes are about *fit*. Pulling a dependency into the tree adds a second set
of axes about *what you now carry* — maintenance, weight, license, security, exit cost — that
an improvised axis list routinely skips.

Use this when a decision in the walkthrough is a dependency pick. It does **not** replace the
`decision-loop.md` entries for the datastore, the web framework, or the data-access layer —
those are their own decisions with their own axes; this feeds them a supply-chain read when
the candidate *is* a library (an ORM, a framework), and stands alone for the mid-size picks
that have no dedicated entry.

## Depth control (same spirit as SKILL.md Step 3)

| Class | Example | Treatment |
|---|---|---|
| **Routine** | a small single-purpose util — `slugify`, `ms`, a debounce | One line: license is compatible · published within ~12 months · no open critical advisory · downloads not near-zero. No table. Batch several into one note. |
| **Structural** | the library shapes a subsystem — validation, HTTP client, router, state | Full loop. Pick the 3–4 axes below that discriminate here, score them, inline ADR with a one-line vetting snapshot in Consequences. |
| **Load-bearing** | ORM, the core framework, a crypto / auth library, anything ripping it out means a migration | Full loop **and** run the specialist `decision-loop.md` entry (data-access layer, etc.); supply-chain risk is its own paragraph in the ADR, not a footnote. |

Don't run the full table on a routine pick — that's the "walking a `.prettierrc`"
anti-pattern in a new costume.

## The axes

Name 2–4 that actually discriminate for *this* pick (SKILL.md Step 2.4 rules apply — cut any
axis where the candidates score the same). The field:

- **Fit & ergonomics** — does it do the actual job, and does its API match how the codebase
  already works. A library you fight on every call loses here even if it's healthy.
- **Type quality** (typed languages) — first-party types vs. a separate `@types` package vs.
  none; for TS specifically, inference quality, not just "has types".
- **Weight** — install size, and for anything shipped to a browser the minified+gzipped
  bundle cost and whether it tree-shakes. Plus **transitive dependency count and depth** —
  how many packages and maintainers you're actually trusting, not just the one on the tin.
- **Maintenance health** — release cadence, date of the last commit, open-issue and open-PR
  age, and **bus factor**: how many people actually merge. A single-maintainer package is
  not disqualifying, but it's a named risk with a revisit trigger.
- **Adoption** — download trend and dependent count; is it the ecosystem's default for this
  job or a challenger. Adoption is a proxy for "problems are already on Stack Overflow" and
  for survival odds.
- **API stability** — semver track record, how often majors land, whether majors ship a
  migration guide / codemod, deprecation history. Churn is a recurring tax you're signing up
  for.
- **License** — permissive (MIT / Apache-2.0 / BSD / ISC) vs. copyleft (GPL / AGPL / LGPL)
  vs. source-available or commercial. Check the **transitive** licenses too, not just the
  top-level one. AGPL in a dependency of a product you distribute or host is a real
  constraint; flag it, don't wave it through.
- **Security posture** — known advisories and, more telling, how fast past ones were patched;
  whether releases are published with 2FA / provenance. One old CVE that was fixed in two
  days is a *good* sign.
- **Exit cost** — if this turns out wrong in a year, how hard is it to remove. A thin wrapper
  you could swap behind your own interface is low-risk; a library whose types and idioms
  spread through every module is high lock-in and the axis should say so.

## How to check each signal

Commands below are npm; the equivalents follow.

| Signal | Where to look |
|---|---|
| Last publish, release cadence | `npm view <pkg> time` · the repo's Releases page |
| Direct + transitive deps | `npm view <pkg> dependencies` · `npm ls <pkg>` · `npx howfat <pkg>` |
| Bundle size, tree-shaking | bundlephobia.com · pkg-size.dev |
| Downloads, trend, compare candidates | npmjs.com page · npmtrends.com (side-by-side) |
| Bus factor, issue/PR backlog | GitHub → Insights → Contributors & Pulse · open issue/PR counts + oldest-first sort |
| Dependency graph, licenses, OpenSSF Scorecard, advisories — one page | **deps.dev/npm/\<pkg\>** |
| Known vulnerabilities + patch latency | osv.dev · GitHub Advisory Database · `npm audit` once installed |
| License (top-level + transitive) | `npm view <pkg> license` · `npx license-checker --summary` |
| Maintainer count, 2FA, signed releases, branch protection | OpenSSF Scorecard (via deps.dev) |
| Breaking-change frequency, migration guides | CHANGELOG.md · Releases · a `docs/migration` or `UPGRADING.md` |

**Other ecosystems:**

- **Python** — `pip show <pkg>` · PyPI page · `pipdeptree` · deps.dev/pypi/\<pkg\> ·
  snyk.io/advisor/python/\<pkg\> (health score) · `pip-audit`.
- **Rust** — crates.io · lib.rs (better health signals) · `cargo tree` · `cargo audit` ·
  deps.dev/cargo.
- **Go** — pkg.go.dev (imported-by count) · `go mod graph` · `govulncheck` · deps.dev/go.

deps.dev covers npm, PyPI, Cargo, Go, and Maven in one view — start there, then go to the
repo for the human signals (who's merging, how they treat issues).

## Folding into the loop

- **Step 4 (axes)** — list the 2–4 from the field above, named before scoring like any other
  decision.
- **Step 5 (score)** — the winner still has to lose an axis out loud. "Zod wins fit and
  types; it loses **weight** (larger than Valibot, doesn't tree-shake well) and **bus
  factor** (effectively one maintainer)."
- **Step 8 (ADR)** — the `Alternatives considered` lines cite the axis lost on, as usual.
  Add one line to `Consequences`: a vetting snapshot plus a revisit trigger.

  ```
  ## Consequences
  Zod — 0 runtime deps, MIT, ~8.9 kB gz, releases roughly monthly, one primary maintainer.
  Revisit if: maintainer activity stalls > 6 months, or bundle size becomes a measured
  problem (then Valibot, same schema model, tree-shakes).
  ```

## Anti-patterns (extends `decision-loop.md`)

| Anti-pattern | Looks like | Fix |
|---|---|---|
| **Popularity as the whole case** | "It has 40M downloads, ship it" | Downloads is one axis; it says nothing about license, weight, or churn |
| **Top-level license only** | Cleared MIT on the package, missed an AGPL three levels down | `license-checker --summary` on the resolved tree |
| **CVE count as the signal** | Rejecting a library for one patched 2019 advisory | Patch *latency* is the signal; a fast fix is reassuring |
| **Bus factor unnamed** | Recommending a solo-maintainer lib with no revisit trigger | Name it in Step 5, add the trigger to the ADR |
| **Vetting a routine pick to death** | Full axis table for a `debounce` | Depth control — one line, batch it |
