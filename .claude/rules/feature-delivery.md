# Feature delivery: one brief, one branch, one PR (applies to every project)

<!-- toc -->
## Contents

- [[#The default]]
- [[#When a split is allowed]]
- [[#Step 1: the brief (questions before code)]]
- [[#Question bank]]
- [[#Step 2: build in one pass]]
- [[#Audit and bug batches]]
- [[#Token economy]]
- [[#Enforcers]]
<!-- /toc -->

Goal: fewer PRs and fewer tokens per feature. Evidence: iron-log PRs #418 to #441 were 24 PRs in a row, many under 30 changed lines, each paying for its own checks, PR body, review, CI wait and context reload. Most of that cost comes from questions answered after the code, not before it.

## The default

One feature = one brief = one branch = one PR. Commits are the checkpoints inside it, not PRs. The PR carries code, tests, docs and changelog together. A fix found while building that belongs to the feature goes in the same PR.

## When a split is allowed

Say the reason in the PR body ("Split because: ..."). Valid reasons only:

1. A migration must be live before code that needs it (expand then contract; `production-access.md`).
2. A file overlaps an open PR and ordering is forced (`parallel-agent-structure.md`; name the file).
3. The diff is over about 600 changed lines or 25 files and the pieces ship independently.
4. A pure-move refactor (`pure-move-refactors.md`) must land before the feature.
5. Part of it needs a real device or the owner's production step and the rest does not.

"It was easy to do separately" and "it came up later" are not reasons; they go into the open feature's PR or the Inbox.

## Step 1: the brief (questions before code)

Before any code, one planning pass that asks every question the build would otherwise raise later.

1. Read the project's `FEATURE-PLAN.md`, `ARCHITECTURE.md`, `ux/` and `data/` docs for the area first; never ask what the docs answer.
2. Ask the question bank below in batches (AskUserQuestion takes up to 4 per call; several rounds are fine). Give each question a recommended default as the first option, so the owner can answer "defaults" for any batch.
3. Write the brief to `/home/jac/Videos/DevHiveMind/Projects/<project>/briefs/<feature>.md`: job, tier and audience, Done when (3 to 7, `definition-of-done.md`), data and schema, files touched, UI states, copy, tests, docs to update, out of scope, decisions made (with the default marked).
4. Ready gate: no open question left, files-touched list compared with open PRs, cost and debt row filled (`feature-planning.md`). Then restate it in five lines and start.
5. A large or unclear feature gets `design-scoping` or `idea-to-first-test` first; this rule starts once intent is settled.

## Question bank

Ask only what the docs do not answer. Group by theme.

- **Job and user:** who uses it, what they do today, what "works" looks like in one sentence, what must not change.
- **Scope:** smallest version worth shipping, what is explicitly out, what the next version adds.
- **Audience and tier:** everyone, admin, paid; limit that separates free from paid; flag or not.
- **States:** empty, loading, error, offline, over the limit, first run, many items, long text, undo.
- **Data:** new tables or columns, who owns the data, export and delete, what happens to old rows, sync and conflicts.
- **UI:** which screen and component, reuse or new, phone and desktop, dark mode, copy text, accessibility names, hands-off areas.
- **Cost and risk:** per-use cost and the cap, new dependency (`dependency-selection.md`), third party, kill criteria.
- **Verification:** which tests, which need a real device, what the owner will try, Lighthouse impact.
- **Docs:** which docs change (feature map, `ux/`, `data/`, ADR, changelog).
- **Edge decisions:** every "should it ..." the build would hit; decide now and record it.

## Step 2: build in one pass

- Work only from the brief; a new idea goes to the Inbox, a changed meaning of done is said out loud and edited into the brief.
- Run the project's check once before pushing, not after each commit; cheap checks (typecheck, one test file) as you go.
- One `/code-review` on the full diff before opening the PR, fixes in the same branch.
- One PR, body from the project's script, with the brief linked and the Done when list reported as verified, read-only, agent-reported or not run (`evidence-labels.md`).
- Docs and changelog updated in that PR, not in follow-ups.

## Audit and bug batches

Group audit findings and small fixes by area, one PR per area per batch, listing every finding ID in the body. A finding under about 30 lines never gets its own PR unless it is urgent or forced by a reason above.

## Token economy

- The brief is the handoff: a new session reads the brief, not the history. Start a fresh session per feature.
- Ask before reading: five questions to the owner cost less than building the wrong thing and redoing it.
- Read only the files the brief lists; use a search agent for broad sweeps and keep only its conclusion.
- Mechanical work goes to the small-model agents (`docs-update` for changelog and roadmap lines, `git-routine` for stage, commit, push), judgment stays on the main model.
- Do not re-read files you just wrote, re-derive settled decisions, or restate the plan each turn.
- Keep `CLAUDE.md` short and link out; it loads every session.

## Enforcers

- This rule is advisory today. Its checks: the PR template's "Brief" and "Split because" lines, and a count of open PRs per author in the weekly review.
- Add a script check to the project's `pr-body.mjs` (warn when a PR under 40 lines is opened while another PR from the same session is open) once the rule is missed twice (`rule-enforcers.md`).
- Related: `feature-planning.md` (what to build and its cost), `definition-of-done.md` (when it is done), `parallel-agent-structure.md` (what can run side by side).
