# Dependency selection: library or build (applies to every project)

Before adding a package or service, decide whether the job needs one. Every dependency is a standing cost (upgrades, advisories, breaking majors, transitive packages and licenses, bundle weight, an absent maintainer); every line you own is one too (bugs, edge cases, tests). Pick the smaller cost for this job.

## The ladder: take the first rung that does the job

0. Don't build it (speculative need: `FEATURE-PLAN.md` Inbox).
1. Platform or standard library (`Intl`, `fetch`, `URL`, `crypto`, native HTML elements, CSS; Python `datetime`/`zoneinfo`, `csv`, `decimal`, `secrets`).
2. A dependency already in the tree (the framework's own feature).
3. Write it: a small owned module (about 150 lines or fewer) with tests.
4. Copy it in: a small, finished, permissively licensed function, with source link and license header.
5. A small focused library (one job, few transitive deps).
6. A large library or framework (shapes how code is written).
7. A managed service (price it with `technical-cost-decision`).

Climb only when the rung below falls short on a named need.

- **The user named a package** ("add lodash for debounce"): say the lower rung in one line, then do what was asked unless it is a never-build case going the other way.
- **The pick shapes a subsystem** (ORM, cache, observability stack, auth model): the ladder only rules out rungs 0 to 3; the choice goes to that area's skill (`data-access-layer`, `caching-strategy`, `observability-strategy`, `access-control-modeling`).

## Never build

Cryptography and password hashing, authentication and sessions, sanitising or parsing untrusted formats (HTML, XML, YAML, Markdown, CSV with quoting), time-zone math, money arithmetic (no floats), database drivers and migrations, Unicode handling, accessible complex widgets (native element first), protocol clients. Use the platform or a vetted library.

## When a library wins

- Vet it at the right depth: `tech-decision-walkthrough/library-vetting.md` (one line for a util; maintenance, weight, transitive deps, license, security patch speed and exit cost for anything bigger).
- Wrap structural and load-bearing libraries behind one seam module so a swap touches one file; don't let their types spread.
- Lockfile committed, `npm audit` / `pip-audit` in CI, heavy front-end libraries lazy-loaded.

## Record it

- PR body: the package delta (direct and transitive count before and after) and the rung below that fell short.
- Structural or load-bearing pick: ADR in `DECISIONS.md` with a revisit trigger; the new technology and lock-in in the feature's `FEATURE-PLAN.md` row.
- Built to avoid a dependency: a header comment naming the library it replaces and when to switch.

Options per functionality (dates, money, HTTP, validation, forms, state, charts, tables, UI widgets, CSV, auth, email, payments, search, jobs, caching, logging, config, flags, i18n) with a default lean: `/home/jac/Pictures/EndToEnd-App-with-AI-Using-skills/.claude/skills/tech-decision-walkthrough/build-vs-library.md`. Read it when choosing how to get a capability.

Enforcer: advisory; the PR-body package delta is the check a reviewer reads. Add a lockfile-diff reminder to a project's PR template when the rule is missed twice (`rule-enforcers.md`).
