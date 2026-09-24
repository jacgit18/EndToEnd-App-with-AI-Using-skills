---
name: skill-static-audit
description: Reads ONE existing skill closely as a document and returns cited findings rated blocker/should-fix/nit plus a verdict; read-only. Use for "audit this skill", "review this SKILL.md", "is this skill's description any good". NOT `skill-interaction-testing` (runs scenarios), `catalog-drift-audit` (whole catalog), or `prompt-tester` (prompts, not skills).
---

# Skill Static Audit

A skill that reads fine to its author can still never fire, or fire wrongly, or send an unfamiliar model guessing at step 3. This skill is the read-through that catches those: one skill, section by section, every finding tied to something in the text. It is a **procedure, not a gate** — it withholds nothing; if the user asks for an audit, run it. `learning-gate` only sets the coaching level (see Escape hatch).

It reads. It does not run the skill against prompts (that is `skill-interaction-testing`) and it does not edit (Step 8).

## Step 1 — Get the target, or branch

| Situation | Do |
|---|---|
| A skill name or path is given | Resolve it under `.claude/skills/<name>/`. Read `SKILL.md`, every companion `*.md`, the skill's own `README.md` if it has one (its absence is a finding only for a group whose other skills have one — check a sibling), and list any scripts/assets. |
| Pasted skill text, no file | Audit the pasted text. Say up front that Step 6 (bundled resources) and the wiring and sibling checks in Steps 2–3 are limited to what the paste shows. |
| Name matches nothing, or matches several | Say so and ask which — one question, with the candidates listed. Do not guess. |
| No target at all ("audit my skills") | Ask which one. If they mean every skill, that is `catalog-drift-audit` (mechanical drift) or a loop of this skill per skill — offer, don't start 60 audits. |
| `SKILL.md` has no frontmatter or no `description` | That is the first finding (blocker) — still audit the rest, and say the skill cannot trigger as written. |
| The ask is "why is this skill's output inconsistent?" | Read the steps for ambiguity and unstated branches and report them as *risk*; say a text read cannot explain runtime variance, and offer `skill-interaction-testing` or `anthropic-skills:skill-creator` if they have example runs. |
| The ask is "does it *actually* fire / collide?" | Not this skill — `skill-interaction-testing` (collisions) or `anthropic-skills:skill-creator` (measured triggering). Offer the pointer; a read-only audit can flag *risk*, not prove behavior. |

## Step 2 — Frontmatter

For `name` and `description`, check each and cite the offending words:

- **Name** matches its directory and is distinctive — no near-duplicate of a sibling (check its group in `.claude/skills/INDEX.md`).
- **Both jobs** — the description says what the skill does **and** when to trigger. Covering only "what" undertriggers.
- **Concrete triggers** — literal phrases a user would type, contexts, synonyms. "Helps with X" is a finding; quote it.
- **Carve-outs** — where a sibling plausibly overlaps, the description says "NOT for X — that's `sibling`". Name the sibling you think is missing and why (which shared noun or request shape). No overlap plausible → no finding.
- **Length** — long is normal in this catalog (carve-outs are the point). Flag only detail that belongs in the body (procedure steps, examples, thresholds) rather than trigger and boundary language.
- **Reciprocity** — for each sibling the description names, does that sibling's description point back? One-directional pointers are the most common defect here. Read the sibling's frontmatter to check; do not assume.

## Step 3 — Catalog wiring (skip on pasted text or a non-catalog skill)

- Row in `README.md`'s catalog table — **if this checkout has one**. Grep the root `README.md` for any skill rows or a table header: none at all means no table in this checkout (say "no table here" and move on); a table that lacks this skill's row is a should-fix.
- A `learning-gate` Step 3 row — needed only if the skill owns a learning-relevant "next rep" (`grep` its name in that file); a purely reference or procedural skill may not need one. Judge, don't demand.
- Gate vs procedure — does the body do what the description and README claim? A "gate" that never withholds anything, or a "procedure" with a hidden precondition wall, is a finding.
- Directory shape — `SKILL.md` (+ companions, + `README.md` for the groups that use one). Match the group's convention; don't impose Architecture's shape on a single-file group.

## Step 4 — Body structure and progressive disclosure

- **Length** — is the body short enough to load every time? Roughly: past ~250 lines, or a big block only some invocations need, is a split candidate. Cite line ranges.
- **Rare-case content** — material needed only in an edge case (a long worked example, a rubric, a lookup table) should live in a companion file the body points to.
- **Pointers** — each companion is referenced *with when to read it*, not just listed. A file listed with no trigger is a finding.
- **Large references** (roughly 100+ lines) have a contents list at the top so a reader can decide relevance without reading it all.

## Step 5 — Workflow

Walk every step as written, as a model that has seen only this skill.

- **Unstated context** — a step that names a thing the skill never defined ("the usual rubric", "the sibling skill"). Quote it.
- **Decision points** — explicit ("if X, A; if Y, B") or implied? Implied branching is where skills fail on edge cases; name the branch that is missing.
- **Unhappy paths** — missing input, ambiguous request, tool or file absent, user declines. If only the happy path is covered, say which unhappy path a real invocation will hit first.
- **Contradictions** — a later instruction that overrides an earlier one without saying so, or a Never-list item the body itself violates.
- **Dead guidance** — a step nothing reaches, or a hand-off to a skill that does not exist (check disk).

## Step 6 — Bundled resources (skip if none)

Read the actual scripts, commands and companion files — do not trust the prose about them.

- Does each script do what the surrounding text says? Quote the mismatch.
- Are paths, invocations and expected outputs still correct? Run `ls` on paths.
- Anything referenced but missing, or present but never referenced?

No scripts or assets → write "none — skipped" and move on. Do not invent a critique.

## Step 7 — Examples and edge cases

- Do the examples exercise the skill's actual purpose, or are they cases that would not have needed the skill? A trivial example is a finding.
- Is there at least one **non-fire** example (a request that looks similar and should route elsewhere)? Its absence is a finding for any skill with carve-outs.
- Known failure modes and pressure cases documented (escape hatch, "user pushes back", "input is thin"), or only the best path?

## Step 8 — Calibrate, rate, report

**Every finding must cite** a line, a quoted phrase, or a named gap between what the description promises and what the body delivers. No citation → delete it. "Add more examples" and "clarify the instructions" are not findings.

Rate each:

| Rating | Meaning |
|---|---|
| **Blocker** | The skill will not fire, fires on the wrong requests, or a core step cannot be executed at all — no named mechanism or fallback for the thing the step tells the model to do (e.g. "dispatch a sub-instance" with no tool named). Includes a missing/vague description and hand-offs to nonexistent skills. A step that is merely ambiguous is a should-fix. |
| **Should-fix** | The skill works but will misbehave on a foreseeable case (missing carve-out, one-way sibling pointer, unhandled unhappy path, body that should be split). |
| **Nit** | Polish. List briefly, last; drop if the list is long. |

If a section is genuinely fine, write "fine" and one line why — do not manufacture a critique.

**Output**, per section: *what's there → the problem (with citation) → the concrete recommendation*. Then:

- **Verdict:** ready to use / needs targeted fixes / needs a rewrite.
- **Fix order:** blockers first; within a rating, description/trigger issues before internal polish (a skill that does not fire never gets read).
- **Not checked:** anything skipped and why (pasted text, no scripts, no catalog table). Honest scope beats a false all-clear.

**Hand-off, then stop.** Offer the next step in one line: apply the fixes yourself, or `/new-skill` step 5 for sibling edits, or `skill-interaction-testing` if the changes widen or narrow what triggers it. Do not edit files as part of the audit.

## Never

- Produce an overall impression without section-level citations.
- Criticize to fill the format — "fine" is a valid result.
- Report a check as a failure when its precondition is absent (no scripts, no catalog table, pasted text).
- Simulate the skill against prompts and call that the audit — that is `skill-interaction-testing`.
- Judge whether the skill's domain claims are true — only whether the skill is well-built.
- Edit the audited skill or its siblings during the audit.

## Escape hatch

If the user only wants a quick sanity check ("just look at the description"), do Step 2 alone and say the rest was not read. If the user is *learning* to write skills and asks to be coached, `learning-gate` may lower this to a hint pass: name the section with the weakest findings and ask what they see before revealing the citation. Default is the full report — this is a review, not an exercise.

## Example invocations

> "Audit `entry-point-first`."

Applies. Read SKILL.md + README.md, read its group in `INDEX.md`, grep sibling descriptions for reciprocal pointers. Step 2 checks whether each sibling named in the carve-outs points back; Step 3 checks `learning-gate`'s Step 3 row exists. Report per section, verdict, fix order, "Not checked: no scripts".

> "This is my draft skill: [pasted text]. Will it trigger?"

Applies, with limits: audit the paste, say Steps 3 and 6 were not possible, and flag trigger *risk* from the description. Point to `anthropic-skills:skill-creator` if they want triggering measured.

> "I just changed the description of `debugging-layer-selection` — does it collide with anything now?"

Does not apply. That is a collision question → `skill-interaction-testing`. Offer this skill afterward only if they also want the description critiqued as writing.

> "Check that every skill is in the README."

Does not apply. Whole-catalog mechanical check → `catalog-drift-audit`.

## Portability

Repo-agnostic except Step 3, which names this catalog's conventions (`learning-gate`, a README table, `/new-skill`). Copy the directory into another repo's `.claude/skills/`; in a repo without those conventions, drop Step 3's wiring bullets and the hand-off names you don't have.

## Routing boundaries (full)

- Use when the user wants ONE existing skill read closely and critiqued as a document — "audit this skill", "review this SKILL.md", "is this skill's description any good", "why might this skill not trigger — read its description" (a read-based diagnosis of the text only), "check my skill before I ship it", "give me feedback on this skill", "is this skill too long / does it need splitting", "does this skill's workflow hold up", "why does this SKILL give inconsistent output — read its steps for ambiguity", or a pasted `Use when…` … `NOT for…` description block with no other context.
- Walks the skill section by section (frontmatter, body structure and progressive disclosure, workflow, bundled resources, examples and edge cases) against what it is supposed to accomplish, and returns findings that each trace to a specific line or gap, rated blocker / should-fix / nit, plus a verdict (ready / targeted fixes / rewrite).
- Read-only: it reports and changes nothing; the fixes go through `/new-skill` step 5 (reciprocal edits) or a normal edit.
- Checks include this catalog's own conventions — carve-outs in the description, reciprocal sibling pointers, a `README.md` row, a `learning-gate` Step 3 row, gate-vs-procedure honesty — and skips any check that does not apply to the skill in front of it.
- NOT `skill-interaction-testing` — that RUNS realistic prompts to see whether a new or changed skill collides with its neighbors (stacking, contradiction, silent override, chaining); this only READS one skill and never simulates a request.
- NOT `catalog-drift-audit` — that is the periodic whole-catalog pass for stale markers, missing README rows and dead pointers; this is one skill, on demand, and goes deep on its content.
- NOT `anthropic-skills:skill-creator` — that creates skills and runs evals or description-optimization loops to measure triggering; this gives a reading-based critique and measures nothing (if the user wants triggering measured, or a skill created or rewritten, that is skill-creator / `/new-skill`).
- NOT a general "teach me what makes a skill description good" with no skill named — that is `learning-gate` (it routes here once there is a real skill to read).
- NOT `skill-usage-log` — that reports which skills were actually invoked, from the log; this reads one skill's text.
- NOT `prompt-authoring` or `prompt-tester` — those are for prompts, not `.claude/skills/` entries ("why does my PROMPT give inconsistent output" is theirs, not this skill's).
- NOT for judging whether the skill's SUBJECT is right (is the finance advice correct, is the SQL advice sound) — this audits the skill as a skill, not the domain claims inside it.
