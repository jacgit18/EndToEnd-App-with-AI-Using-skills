# QA scenarios per feature (optional add-on to the PR kit)

For a project that has a QA environment with test accounts (personas) and wants every user-facing feature to arrive with numbered "try this" scenarios, without the owner having to remember. Off by default: a project with no `qa` key in `.github/pr-kit.json` sees no change from `pr-body.mjs`.

Reference implementation: iron-log (ADR 080 test accounts, ADR 094 this trigger). Files to copy the idea from: `server/qa/personas.ts` (accounts), `server/qa/scenarios.ts` (the list), `server/qa/scenarios.test.ts` (list tests), `scripts/qa-scenarios-doc.mjs` (generates the page and `--check`s it), `scripts/pr-body.mjs`.

## What it does

- A brief has a QA scenarios section (drafted from Done when and the states list, updated from the diff after the build).
- `node scripts/pr-body.mjs --qa "S-41, S-42"` (or `--qa "n/a: <why>"`) fills a `QA scenarios:` line in the PR description.
- It warns, never blocks, when: a user-visible PR gives no `--qa`; an id is not in the scenario file (also inside `n/a: covered by S-01`); real ids are named but the PR does not change the scenario file; `n/a` has no reason.
- A docs-only PR (audience n/a) gets `QA scenarios: n/a: no user-facing change` filled in.

It does not generate Playwright specs (CI budget: unit tests first), and no agent records a scenario result: the Result column of the generated page is the owner's.

## Setup (4 steps)

1. **Scenario file.** One list, ids `S-01` upward, never reused or renumbered (a scenario that no longer applies gets `retired: true`). Each entry: id, feature, title, persona (an existing test account), brief (slug or `feature-map`), steps, expected, optional `edge`, `device`. Write the ids as `id: 'S-01'` (single quotes, one space): `pr-body.mjs` reads the file as text so it needs no TypeScript loader.
2. **Config.** In `.github/pr-kit.json` add
   `"qa": { "scenarioFile": "<path of the scenario file>", "idPattern": "S-\\d{2,}" }`.
3. **Template.** In `.github/pull_request_template.md`, under `## Delivery`, add the line `QA scenarios: none given (pass --qa)` and `--qa "<S-ids or n/a: why>"` to the comment above it. (Without the line the warning stays off.)
4. **Rule and brief.** Add the Definition of done line and the brief section below to the project's `CLAUDE.md` and brief template.

## Text to paste

CLAUDE.md, Definition of done:

> New user-facing feature: its QA scenarios are in `<scenario file>` (a happy path per Done-when line, edge cases for the states that matter, a new feature entry; reuse a test account unless the brief justifies a new one), the PR names them with `--qa "S-41, S-42"` (`--qa "n/a: <why>"` for a change nobody can see), and the scenarios page is regenerated. Results stay the owner's. Enforcer: the scenario list tests, `pr-body.mjs` warning (advisory, never blocks).

Brief template, new section before "Tests and docs":

> ## QA scenarios
> Draft at the Ready gate from Done when and the states list; update from the diff after the build (`agent-reported` until the owner walks them). A change nobody can see says `n/a: <why>` here and in `--qa`.
> - Scenarios: one happy path per Done-when line a person can try, plus one edge case per state that matters (empty, over the limit, offline, two devices). Each is an entry in the scenario file: next free id, feature, title, steps, expected, `edge`, and `device` if it needs a real phone.
> - Test account: reuse an existing one (default). A new account needs a reason here: the plan, history length or data state no account has, and what it adds to the seed code.
> - PR line: `--qa "S-41, S-42"`.
> - After the PR: regenerate the scenarios page, keeping the Result column.

## Tests worth copying (iron-log `scenarios.test.ts`)

- ids are `S-nn`, unique, in order, and a minimum count of live scenarios;
- every scenario names an existing test account;
- every scenario has a title, steps and expected lines, and claims no result;
- every listed feature has a live scenario **and a happy-path one**, and no scenario uses an unlisted feature;
- `brief` is `feature-map` or a kebab-case slug;
- phone-only scenarios are marked `device`.

The page generator's `--check <page>` compares each scenario block (title, account, steps, expected) and the retired flag with the list, and ignores the Result lines filled in by hand. It runs locally; the page usually lives outside the repo, so it is not a CI check.

## Tightening later

The warning is advisory. If it is silenced with `n/a` or ignored a second time, add a CI check on the PR body (a new job: say the minutes in the PR and get the owner's yes under `ci-budget.md`), per `rule-enforcers.md`.

## Not installed by `install.sh`

`install.sh` does not copy this add-on yet: the `qa` key and the template line are opt-in per project, set by hand with the four steps above.
