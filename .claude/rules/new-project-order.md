# New project order: fast first, guardrails at triggers (applies to every new project, 2026-10-30)

Iron Log's process (briefs, PR kit, review bot, Lighthouse floors, CI budget, dependency scans, doc rules, tracker rows) was right for an app at 25 accounts heading to billing and the Play Store. Applied to a project on day 1 it slows every AI-generated change, because each change pays for reading and ceremony the project does not yet need. Order the work so speed comes first and each guardrail arrives when something makes it worth its cost. Basis: the iron-log docs, read-only (`evidence-labels.md`); the speed cost is the owner's observation, not measured.

## Stage 0: day 1 (cheap, costly to retrofit)

Do all of these before the first feature; about a day, and none of it slows generation.

1. **Load-bearing data decisions, one line each** in `DECISIONS.md`: units (canonical unit), dates and weeks (local date strings, week start), IDs and deletes (client ids, tombstones), who owns a row, sync model. A wrong call here means migrating real data. Skip a line only if the project has no stored data.
2. **Strict types and a typecheck** (TypeScript `strict`, or the language's equivalent).
3. **Migrations as plain files** from the first table, even locally.
4. **Unit tests on pure logic only** (money, dates, merging, validation); no component-test layer, no e2e yet.
5. **One-command deploy** to a real URL, and look at it in a real browser at phone and desktop width.
6. **A short `CLAUDE.md`** from `new-project-claude-md-template.md`: stack, commands, data rules, under about 40 lines.

## Triggers: add the guardrail when the event happens

| Trigger | Add |
|---|---|
| First person other than you uses it | Auth, per-user data isolation, error reporting, backups and one restore test |
| First schema change with real data in it | Migration rehearsal on a copy, expand/contract rule |
| Second contributor, or two agents at once | One branch per task, PR template (`pr-kit`), `parallel-agent-structure.md`, e2e for the main flows |
| Any package you did not already approve | `dependency-security.md` (name check, vetting) |
| Before raising any sign-up cap | Rate limits, storage caps, privacy page, delete-my-data, staging |
| First paid user | Billing in test mode, idempotent webhooks, terms and refunds |
| Store listing or public launch | Compliance checklist, Lighthouse floors (`web-accessibility-and-lighthouse.md`), real-device checks |
| A doc passes 100 lines | Table of contents (`document-toc.md`) |
| CI takes long enough to notice | CI budget and job timeouts (`ci-budget.md`) |
| A rule is missed twice | An enforcer for that rule (`rule-enforcers.md`) |

Brief, planning pass and review bot (`feature-delivery.md`, `pr-review-bot.md`) start at the second-contributor trigger, or earlier for one large or risky feature. A one-file fix never needs a brief (`Brief: n/a`).

## The hard rule that makes "fast first" safe

When a trigger fires, **feature work stops until its guardrail is in.** Iron Log shipped Experiments and Groceries (about 20 PRs) ahead of the safety work, then had to freeze features. A trigger that fires and is ignored turns fast-first into fast-and-fragile.

Ranking when two things compete: can it lose or corrupt data; does it block the next milestone; does it make shipping safer; last, how it looks.

## Tiering an existing heavy process

A project that already has the full set (Iron Log) keeps it. For a small change inside it, tier by size rather than dropping rules: pure docs or one-file fixes skip the brief and run only the checks `npm run check` picks; the full set applies to features, schema, auth and UI changes.

## Enforcer

Advisory. The check is the stage table above, read at project start and when a trigger event is mentioned. Related: `feature-planning.md`, `definition-of-done.md`, `dependency-selection.md`.
