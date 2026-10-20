# Feature planning, cost, debt and tiers (applies to every project)

Goal: decide what to build in one planning pass, so features are not invented on the fly, and know up front what each costs, what it adds to technical debt, and which plan it belongs to (free or paid). Output lives in the project's `ROADMAP.md` (ranked list, out of scope) and `FEATURE-PLAN.md` (the full table below), both in `/home/jac/Videos/DevHiveMind/Projects/<project>/`.

## 1. Plan once, then freeze

- **Discovery pass at project start** (and again at each milestone): list every feature wanted for the next stage, using the prompts below. Do not write code during it.
- **Idea inbox.** A new idea mid-build goes into an `Inbox` section of `FEATURE-PLAN.md` with one line, not into code. Review the inbox at a fixed point (end of each milestone or a set weekly slot), then score, tier and rank the keepers.
- **Stage gate.** Work only from features marked `Ready` (cost check passed and `Done when` written). A feature not in the plan needs a plan row first (5 minutes: the fields in section 2).
- **Out of scope list.** Say what you will not build this stage; it stops re-litigating.

Discovery prompts: who uses it and what job are they hiring it for; what do competitors and similar apps have; what do users do today that is manual or annoying; what does a day-1 user need versus a day-100 user; what makes a user stay (retention) versus pay (revenue); what is required to operate it (admin, support, billing, analytics, export, delete-my-data, notifications, onboarding, settings, accessibility, offline, import).

## 2. Fields for every feature (one table row or card)

| Field | What to write |
|---|---|
| Name and one-line job | what the user can do afterward |
| Done when | 3 to 7 observable, checkable statements plus what is not part of done and the evidence for each (see `definition-of-done.md`); a row without it is not `Ready` |
| Stage | Now / Next / Later / Never |
| Tier | Free, Paid, Paid-higher, Admin-only, Undecided (see section 4) |
| Value | high / medium / low, and who gets it |
| Build effort | S / M / L (use `effort-layers`: include tests, docs, deploy, support, not just the build) |
| Running cost | per-user or per-use cost: hosting, database size, API calls, storage, email/SMS/push, AI tokens, payment fees. Give a number or a range, and a worst case if usage 10x |
| New technology | each new service, library, SDK or API the feature adds, and the lock-in if it is swapped later |
| Debt it adds | maintenance, upgrades, migrations, extra tests, a second code path, a vendor to watch, compliance (see section 3) |
| Depends on / blocks | other features, schema, infra |
| Shared files touched | from the project's shared-file list (see `parallel-agent-structure.md`); fewer is better, and a feature touching many belongs in a serial slot |
| Risk | what could go wrong, and how it is switched off (flag) |
| Kill criteria | the measurement after launch that says remove it or leave it |

## 3. Cost and technical-debt check

Run it before a feature is `Ready`, in this order:

1. **Can the existing stack do it?** A new dependency, service or vendor is a standing cost even if it is free today. Prefer what is already in the project; walk the ladder in `dependency-selection.md` (platform, existing dependency, write it, library, service).
2. **Recurring cost.** Estimate per active user per month and the cost at 10x usage. Flag anything with no upper bound (AI calls, storage of user files, SMS, egress). Cap it or put it in a paid tier.
3. **Data and schema.** Does it add tables, columns or user data? Schema changes are the hardest to undo (expand/contract migrations, backups, RLS). Data about people adds retention, export and delete-on-request duties.
4. **Third-party risk.** Pricing changes, rate limits, deprecation, outages, terms. Note the exit path: how hard is it to replace.
5. **Operational load.** Anything that needs monitoring, a cron job, a queue, webhooks or on-call attention.
6. **Compliance.** Payments, health, location, children's data, email/SMS consent, tracking. Run `legal-readiness-gate` when any apply.
7. **Test and doc load.** New e2e flows, new fixtures, new UX docs.
8. **Debt rating:** none, low, medium or high, with one line why. Two or more mediums, or any high, need a decision recorded in `DECISIONS.md` (ADR) before building.

Rules of thumb: a feature whose running cost grows with usage must be paid or capped; a feature that adds a vendor needs an owner and an exit plan; the first release of a risky feature ships behind a flag; if debt is high and value is not, it goes to `Never` or `Later`.

## 4. Tier model (free versus paid)

Decide tiers during planning, not at launch. Principles:

- **Free should be genuinely useful and cheap to serve.** It earns trust and word of mouth, and it shows the value. A free tier that is crippled gets no users.
- **Paid is for what costs you money, saves the user real time, or serves heavier or more professional use.** Not for basics that other apps give free.
- **Charge for the cost driver.** Anything with per-use cost (AI, storage, SMS, sync of large data, exports at scale) is a paid-tier candidate or a free-tier cap.
- **Never gate the core loop or the user's own data.** Users can always see, export and delete their data; the main thing the app is for works on free.
- **Gate by limit, not by hiding.** Limits (counts, history length, storage) upsell better than removing a feature; keep the limit generous enough to show value first.
- **Keep the matrix small.** Two paid tiers at most at first (Free, Pro, optionally Team/Pro+).

Candidate sorting (adjust per product):

| Goes in Free | Goes in Paid | Goes in higher tier or Team |
|---|---|---|
| Core loop of the app | Higher limits (history, items, storage) | Multi-user, sharing, roles |
| Basic tracking and history | Sync across devices, backup | Admin console, audit log |
| Local and offline use | Advanced analytics and insights | API access, integrations |
| Export and delete my data | Automation, reminders, notifications at volume | SSO, priority support |
| Basic themes and accessibility | AI features (tokens cost money) | White-label, SLAs |
| Import from common formats | Integrations with third-party services | Bulk and team reporting |

For each feature, add: tier, the limit that separates Free from Paid if it is a limit, and the upgrade trigger (the moment a free user hits it). Record the matrix in `FEATURE-PLAN.md` and any pricing decision as an ADR. Before the first paid user: payments (test mode first, idempotent webhooks), a way to downgrade without losing data, and terms and refund policy (`legal-readiness-gate`).

## 5. Ranking

Rank `Ready` features by value, then lowest debt and cost, then dependencies (what unblocks other work), then parallelism (a feature that touches no shared files can run beside another). Revisit at each milestone.

## Where it lives

- Per project: `ROADMAP.md` (ranked, out of scope, link to the plan) and `FEATURE-PLAN.md` (inbox, full table, tier matrix, cost and debt notes) in `/home/jac/Videos/DevHiveMind/Projects/<project>/`.
- Create both when onboarding a project; update them when a feature is added, tiered, shipped or killed.
- Related skills: `design-scoping`, `ticket-evaluation`, `effort-layers`, `technical-cost-decision`, `legal-readiness-gate`, `user-story-decomposition`.
