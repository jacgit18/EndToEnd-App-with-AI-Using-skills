---
name: demand-experiment-design
description: Designs and reads one demand experiment (fake door, A/B, concierge, landing page) once a DEMAND risk is named: pass line, sample limits, honest labels, then build/kill/retest. Use for "design a fake door", "will anyone use this", "5 of 20 clicked". Not a raw idea (`idea-to-first-test`), ticket verdicts (`ticket-evaluation`), code tests (`test-strategy`), "what is X" (`learning-gate`), rollout mechanics (`deployment-strategy`).
---

# Demand Experiment Design

A demand test fails two ways: it runs with no pass line, so any number gets read as a yes, or it deceives the people it measures. This gate withholds "go build it" until a threshold is written down before the test runs, and withholds the verdict until it is compared to that threshold.

## Step 1 — Does this skill apply?

| The user… | Route |
|---|---|
| Has a named DEMAND risk and needs the test designed, or has results to read (including "I already ran it, 5 of 20 clicked": see Escape hatch) | **This skill** |
| Holds a raw idea, no risk named yet | `idea-to-first-test` (it hands the DEMAND branch here) |
| Has a written ticket and wants go/no-go | `ticket-evaluation` |
| Has a settled feature to plan | `feature-brief` |
| Asks what a fake door or A/B test *is* | `learning-gate` (explain, then back here to design) |
| Asks how a version reaches users (canary, flag, % rollout) with no question about whether users want it | `deployment-strategy`. If the point is "see if they like it", it is this skill: design the exposure as the test (pass line first), then `deployment-strategy` for the mechanism |
| Wants to test whether code works (BUILD) | `test-strategy` |
| Wants a one-off sanity check of a single number | answer inline, no gate |

No named risk: ask for the one sentence "we believe <who> will <do what>" before Step 2, nothing else.

## Step 2 — Pick the test type

| Type | Use when | Weakness |
|---|---|---|
| Interview or message | no audience yet, need the why | says vs does |
| Landing page + real ask | no product yet, can drive traffic | needs traffic |
| Fake door (button in a live app, "Coming soon" shown on click) | users exist, one feature in doubt | measures curiosity, not payment |
| Concierge / manual version | value delivery is the doubt | does not scale; effort per user |
| A/B test | two live variants, enough traffic | needs volume; a small beta cannot power it |

Pick the cheapest that touches the assumption. A small beta (under about 100 exposed users) rules out A/B: use a fake door, concierge or interviews.

No traffic or exposure count yet: the first step is getting exposure (who will see it, how many), not running the test.

## Step 3 — Write the pass line before running

All of these, in writing, before any data exists:

1. **Who is exposed** and how many (the denominator: users who saw it, not total users).
2. **Action counted** (clicked, joined waitlist, gave an email, agreed to pay). A stronger action beats a weaker one; a click alone is weak.
3. **Build / kill / retest thresholds**, e.g. "build at 15%+ of exposed, kill under 5%, between = retest with a stronger ask".
4. **Window** (a result date, not "until we see enough").
5. **Honest labelling** (required for a fake door): the page says the feature is not ready yet ("Coming soon", join a list). No fake loading states, no implied availability, no charging for something that does not exist.
6. **Reachability**: pick the build bar so it can be cleared at the planned n. If the interval at the planned n cannot sit above the kill line (e.g. 20 users cannot separate 15% from 5%), raise exposure, strengthen the ask, or switch type before running. Bars come from what the decision is worth (what a build costs vs. the value if the rate holds), not a default. No cost estimate from the user: propose a starting bar, label it a placeholder, and ask for the build cost in one line.
7. **Cleanup**: what happens to people who clicked (tell them, offer the waitlist, do not leave a dead button).

## Step 4 — Read the result

- Report `action / exposed` and the interval, not the bare rate. Rule of thumb: 5 of 20 is 25%, but the 95% interval is roughly 11% to 47%; 0 of n means the true rate could still be up to about 3/n.
- Compare to the Step 3 line only. A threshold changed after the data is a new experiment.
- Under the planned minimum n, or the pass line was set after the data: the verdict is **retest** at best, never build.
- Verdict: **build** (clears the line with an interval that stays above the kill threshold), **kill** (below it), or **retest** (straddles; run a stronger ask or more exposure). Say what the result cannot show: a click is curiosity, not willingness to pay.
- Record the outcome as the feature's kill/keep criteria in `FEATURE-PLAN.md` (`feature-planning.md`).

## Output

```
Risk: <we believe who will do what>
Test: <type>  Exposed: <n>  Action counted: <x>  Window: <date>
Pass line: build >= _  kill < _  retest between
Labelling / cleanup: <how it stays honest>
--- result (after the window; a post-hoc pass line caps this at retest) ---
<action>/<exposed> (interval _ to _) -> build | kill | retest   Cannot show: <x>
```

## Never

- Set or move the threshold after seeing data.
- Run a fake door without visible "not ready yet" labelling, or collect payment for it.
- Call a small-group result significant, or run an A/B test a small beta cannot power.
- Treat a BUILD test as a demand answer, or a click as a purchase intent.
- Re-brainstorm the idea or plan the feature; those are `idea-to-first-test` and `feature-brief`.
- Add an analytics package without the owner's yes in chat (rule `dependency-security.md` in `.claude/rules/`); count with what the app already has, or by hand.

## Escape hatch

"Just design it, I'll read it later" → Steps 2–3 only, and say the verdict is pending. "I already ran it" → reconstruct Step 3 honestly, say which parts were written before the data, then Step 4; a threshold set after the data caps the verdict at retest. A pending verdict is recorded as `result: pending <date>`.

## Example invocations

> "I want to put an AI workout recommendations button in my beta app, 20 testers."

Applies. Fake door (beta too small for A/B). Pass line written first; interval stated at n=20; "Coming soon" label required.

> "Wild idea: an app that negotiates my bills."

Doesn't apply yet. `idea-to-first-test` names the risk first.

> "Should we pull this ticket into the sprint?"

Doesn't apply. `ticket-evaluation`.

## Portability

Needs no setup and writes nothing unless the user asks to record the criteria in `FEATURE-PLAN.md`.

Depends on: `idea-to-first-test`, `ticket-evaluation`, `feature-brief`, `test-strategy`. If a named sibling isn't installed, say so and give the one-line answer inline. Load-bearing fallbacks: no `idea-to-first-test` and no risk named → ask for the one-sentence belief and continue; no `feature-brief` or `FEATURE-PLAN.md` → give the criteria in chat; no `test-strategy` → say a BUILD question is out of scope here.

## Routing boundaries (full)

- Idea or risk not yet chosen: `idea-to-first-test`, which hands its DEMAND branch to this skill.
- A written ticket's go/no-go: `ticket-evaluation`. A settled feature's plan: `feature-brief`.
- Whether code works: `test-strategy`. What a number means in prod: `observability-strategy`.
- Release exposure to a share of users: `deployment-strategy` (that is rollout, not demand).
