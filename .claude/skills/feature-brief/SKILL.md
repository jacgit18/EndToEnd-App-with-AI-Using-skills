---
name: feature-brief
description: Pre-build planning pass for one feature in a project whose intent is settled: reads the project docs, asks the question bank in batches with a recommended default on each (skips the bank for audit and bug batches), and writes a brief (Done when, files touched, decisions) so the feature ships as one branch and one PR. Use for "let's build X", "plan this feature", "write the brief", "start the next card". Not a bare system design (`design-scoping`), a vague ask (`ambiguity-gate`), a go/no-go on a ticket (`ticket-evaluation`), or a one-file bug fix (no brief needed: write `Brief: n/a` in the PR).
---

# Feature Brief

The cheapest place to find a wrong assumption is before the code. This skill runs one rigorous planning pass for one feature, writes the answers down, and hands a build that needs no further questions. Rule behind it: `feature-delivery.md` (one feature = one brief = one branch = one PR).

## When it applies

| Situation | Do |
|---|---|
| A feature, card or "let's build X" in a project that has docs | Run the steps below. |
| A one-file bug fix, a typo, a change under about 40 lines with no new behavior | Skip. Write `Brief: n/a: <why>` in the PR. |
| Several audit findings or small fixes | One brief for the batch: list the finding IDs, group by area, no question bank unless a finding is ambiguous. |
| The owner is dictating a messy story about a problem | First use `design-scoping`'s propose-and-react lane (`feature-in-existing-app.md`) to get a concrete shape and a preview, then return here to close the remaining questions. |
| No project docs and no settled intent ("I have an idea") | `idea-to-first-test` or `design-scoping` first. |

## Steps

1. **Read before asking.** The project's `FEATURE-PLAN.md` row for the card, `ARCHITECTURE.md`, `ux/` and `data/` docs for the area, the feature map, open PRs (`gh pr list`, `gh pr diff <n> --name-only`). Never ask what these answer. Label what you learned `read-only`.
2. **Draft the brief with defaults.** Fill `brief-template.md` with your best answer for every field and mark each guess `(default)`. This is the thing the owner reacts to.
3. **Ask only the real decisions; list the rest as defaults.** A question is real when the docs and code leave two or more reasonable answers that change the build (what Silent covers, which sound, who sees it). A question whose answer you already know from the docs or a project rule is not asked: state it as `(default)` in a "Defaults I am taking" list and let the owner veto in one reply. Ask the real decisions in one round (up to 4 per AskUserQuestion call, recommended default first), then show the defaults list and the draft brief together for a single "go" or change. Add a second round only if an answer opens new decisions. Test run 2026-10-21 (rest-timer sound): without this rule the skill asked 8 questions in 3 rounds when only 2 were real.
4. **Close the edge decisions.** List each "should it..." the build would hit (empty, offline, over the limit, old data, undo, long text) and decide it now. A decision the owner skips is recorded as `(default)`, not left open.
5. **Check overlap and cost.** Compare the files-touched list with open PRs; apply the `feature-planning.md` cost and debt check; split into several PRs only for a reason in `feature-delivery.md`.
6. **Ready gate.** The brief has no open question, 3 to 7 Done-when lines each naming its evidence, and an out-of-scope list. Write it to `<docs root>/<project>/briefs/<feature>.md`, add the brief link to the `FEATURE-PLAN.md` row, run `doc-toc.mjs` if it is over 60 lines. Restate it in five lines and ask for one "go".
7. **Build handoff.** The build session reads only the brief and the files it lists. New ideas go to the Inbox. A changed meaning of done is edited into the brief out loud. The PR links the brief (`pr-body.mjs --brief`). Hand the build to `spec-drift-gate` (or `incremental-build-pacing` for a slow, file-by-file build) and the PR to `commit-and-push`.

## Rules that keep it cheap

- `ambiguity-gate`'s one-question limit does not apply here: this pass is deliberate. No more than 2 rounds of questions; if a third is needed, the feature is not understood yet: say so and return to `design-scoping`.
- Questions are about decisions, not facts you can look up.
- Do not write code, schemas or UI in the brief; name the files and the shape.
- Never re-ask a decision recorded in the project's `DECISIONS.md`.

## Portability

Needs a project docs folder with `FEATURE-PLAN.md` (without it, create the brief beside the README and say so). Writes `briefs/<feature>.md` in the docs root; uses `gh` for open PRs when available (otherwise ask the owner for open PRs).

Depends on: `design-scoping`, `spec-drift-gate`, `incremental-build-pacing`, `commit-and-push`; routes away to `ambiguity-gate`, `ticket-evaluation`, `effort-layers`, `user-story-decomposition`, `idea-to-first-test`. If a named sibling isn't installed, say so and give the one-line answer inline. Load-bearing fallbacks: no `design-scoping` → ask for the job, user and smallest shippable version in one question before the bank; no `commit-and-push` → open the PR with the project's own body script and link the brief by hand; no project docs → write the brief to the repo root and flag the missing `FEATURE-PLAN.md`.

## Routing boundaries (full)

- Use when a feature, card or "let's build X" is about to start in a project and the intent is settled.
- Not for designing a whole system from a bare name or numeric targets (`design-scoping`); not for vague verbs where the reading itself is unclear (`ambiguity-gate`); not for deciding whether a ticket is worth doing (`ticket-evaluation`); not for how long it takes (`effort-layers`); not for splitting an epic into stories (`user-story-decomposition`); not for a raw idea with no demand evidence (`idea-to-first-test`).
- Hands off to `spec-drift-gate` or `incremental-build-pacing` for the build, and to `commit-and-push` for the PR.
