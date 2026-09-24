# skill-interaction-testing skill

A procedure (not a gate) for testing a new or substantially changed skill against the
siblings it could collide with. The isolation screen proves a skill works alone; this proves
it works beside the others. It builds a candidate pool in three tiers (same group,
a fixed cross-cutting list, name-scan of the rest), writes realistic collision scenarios
plus a control prompt, runs each on a fresh isolated agent, and classifies the outcome:
hand-off, absorption, chaining (good) versus stacking, contradiction, starvation (bad). Bad
outcomes are usually fixed with a one-line description edit and re-run; the result is
recorded in project memory so pairs are not silently re-tested or skipped.

## Files

| File | Role |
|---|---|
| `SKILL.md` | The whole skill: Step 1 candidate pool, Step 2 scenarios, Step 3 run and observe, Step 4 fix or record, plus the "what this is not" note. There are no companion files. |

## Where it sits

- **After the isolation screen** — the checklist step in `.claude/rules/adding-a-skill.md`
  that follows step 3; it complements the isolation screen, it does not replace it.
- **`skill-static-audit`** — read-only critique of one skill without running prompts. A
  description edit that widens or narrows scope hands back here.
- **`catalog-drift-audit`** — the periodic whole-catalog pass; it hands any pair it flags
  back to this skill's Step 2 onward rather than re-deriving the method.
- **`skill-usage-log`** (feedback mode) — reads real fire/override data and hands each
  proposed description edit to this skill's Step 2 onward.
- **Fixed cross-cutting pool** — `ambiguity-gate`, `learning-gate`, `problem-solving-gates`,
  `problem-journal` are always read in Step 1.

Skip when the project has fewer than two skills or the edit does not change what triggers
the skill (typos, polish, examples that do not widen or narrow scope).

## Using it in another repo

Repo-agnostic apart from the fixed cross-cutting list, which names skills from this catalog;
adjust it to the target repo's own request-shape skills. Copy the directory into the other
repo's `.claude/skills/`:

```
cp -r .claude/skills/skill-interaction-testing /path/to/other-repo/.claude/skills/
```
