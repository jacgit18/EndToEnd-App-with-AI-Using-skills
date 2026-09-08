---
name: skill-interaction-testing
description: Use after writing or substantially revising a skill in .claude/skills/, before considering it done — tests the new or changed skill against the other skills it could realistically collide with (its own group, a fixed short list of cross-cutting gates, plus any out-of-group skill a quick scan flags as sharing a concrete concept) for stacking (multiple gates firing in sequence), contradiction (skills giving opposite instructions), silent override (the right skill never fires because a broader one claims the request first), or beneficial chaining (one skill's output feeding another's input). It does not read the full catalog for this — see Step 1 for how the candidate pool is scoped, which keeps a new Finance skill, say, from ever being weighed against unrelated Git or Documents skills. Complements writing-skills, which only tests whether the new skill complies in isolation — it has no step for checking the new skill against siblings already in the project. Also use when an existing skill's trigger description is edited in a way that could newly overlap with another skill's. Skip when the project has fewer than two skills, and skip for edits that don't change what triggers the skill (typo fixes, wording polish, added examples that don't widen or narrow scope). For a periodic, whole-catalog hygiene pass instead of a per-skill one — stale backlog/memory pointers, skills missing from README, dead cross-references, untested old pairs — that's `catalog-drift-audit`, which hands any pair it flags back to this skill's own Step 2 onward rather than re-deriving the collision-testing method.
---

# Skill Interaction Testing

`writing-skills` proves a new skill works alone: baseline fails without it, the skill fixes the failure, refactoring keeps it fixed. None of that touches what happens when the new skill sits next to the other skills already in this project and a real request could plausibly trip more than one. That gap isn't hypothetical here — a new skill was drafted and screened in this project without anyone, including the model doing the drafting, proposing a check against the existing skill set until asked directly. This skill closes that gap as a checklist step after `writing-skills`, not a replacement for it.

## Step 1 — Scope the candidate pool

Don't read every skill in `.claude/skills/` — as the catalog grows past a handful of groups, full-catalog reasoning is wasted work and it dilutes attention on the pairs that actually matter. Build the candidate pool in three tiers instead, cheapest first:

1. **Same group as the new skill.** Always read these descriptions in full — a Finance skill and another Finance skill share enough subject matter that a trigger-shape collision is plausible even before you check.
2. **The fixed cross-cutting list.** Always read these regardless of the new skill's group, because their triggers are about request *shape*, not subject matter, so they can fire alongside a skill from any domain: `ambiguity-gate`, `learning-gate`, `problem-solving-gates`, `problem-journal`. (Keep this list itself short — a skill only belongs on it if its description says it triggers on how a request is phrased or where it sits in a workflow, not on what domain it's about. Add to it only when a new skill earns that description; if this list ever grows past ~6-8 entries, its own trigger shapes have probably drifted apart and it should be split, not just extended.)
3. **Everything else — name-and-one-line scan only, not a full read.** Skim just the skill names and the first clause of each remaining description (skip the rest of the file). Pull a skill into the full candidate set only if that skim surfaces a concrete, nameable shared concept with the new skill (a shared noun like "cost," "migration," "ticket," not a vague "both are technical"). If the new skill's own draft already documents a hand-off or "Feeds:" relationship to a specific out-of-group skill (common when built via `SKILL-BACKLOG.md`'s process), that named skill goes straight into the pool without needing the scan.

For whichever skills end up in the pool (tiers 1 + 2 + any pulled from tier 3), apply the original question: **could one realistic user prompt plausibly trip both this skill and the new one?** List the candidates that pass; most skills — including most skills outside the new one's group — will never reach this question at all, which is the point.

Example: a new `Finance/` skill's pool is every other `Finance/` skill (tier 1) + `ambiguity-gate`, `learning-gate`, `problem-solving-gates`, `problem-journal` (tier 2) + `Business/technical-cost-decision` (tier 3 — both are about pricing a recurring decision, a concrete shared concept, and prior Finance skills already hand off to it). It does not include `Git/commit-and-push`, `Documents/document-page-check`, or most of `Architecture/` — nothing in their one-line descriptions shares a concept with a money decision, so they're never even fully read.

## Step 2 — Write the collision scenarios

For each candidate pair, write one prompt a real user would plausibly send about their actual problem — not a prompt artificially engineered to force both triggers. Include:

- **A multi-turn pair if the new skill is gate-shaped** (it withholds an answer pending a precondition): a good-faith answer on turn 2, confirming the gate releases without a second skill re-firing on the new detail; and separately, the specific pressure named in the skill's own description ("already decided," "just tell me," authority), confirming the gate holds without going rigid or caving.
- **One control prompt** that should trip only the new skill, or only an existing one, and nothing else. This catches the opposite defect — gates firing on everything — which is just as bad as stacking and easy to miss if every test is a deliberate collision.

## Step 3 — Run and observe

Send each scenario to a fresh agent with the full project available — don't strip the skill set down to isolate the new one, since the failure only exists in combination, and a full skill set also catches the rare case where Step 1's scan under-scoped the pool (an unlisted skill fires anyway). Isolate the run (background agent, worktree) so nothing lands in the repo uninvited. Watch for:

| Outcome | What it looks like |
|---|---|
| **Hand-off** (good) | One skill classifies and routes to another; one coherent response |
| **Absorption** (good) | The skill that fires covers what a second skill would have asked; the second correctly stays out |
| **Chaining** (good, worth noting) | One skill's output becomes another's input, producing a conclusion neither reaches alone |
| **Stacking** (bad) | Multiple rounds of questions, or the same ground covered twice |
| **Contradiction** (bad) | Two skills give opposite instructions with no resolution |
| **Starvation** (bad) | The right skill never fires because a broader one claims the request first |

## Step 4 — Fix or record

If a bad outcome appears, the fix is almost always a one-line addition to a description — an explicit hand-off note, or a scope narrowing ("does not apply when X, see [other-skill]") — not a rewrite of either skill. Re-run the failing scenario to confirm the fix actually closes it before moving on.

Either way, record the result in project memory: which pairs were tested, what happened, and — if nothing broke — a note not to re-test the same pair without a new reason. An interaction test that isn't recorded gets silently re-run, or silently skipped, the next time a skill is added, which defeats the point of running it at all.

## What this is not

Not a reason to design skills around avoiding overlap. Overlap that hands off or chains cleanly is a feature, not a risk to eliminate — a cost skill and a services skill chaining together can produce a number neither reaches alone. The test exists to catch overlap that fights instead of composes, not to minimize overlap itself.
