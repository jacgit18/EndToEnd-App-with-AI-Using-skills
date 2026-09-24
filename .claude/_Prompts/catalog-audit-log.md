# Catalog drift audit — log

Durable trail for `catalog-drift-audit` runs (manual and the weekly cloud routine). Each run
reads this first so it never re-flags something already resolved. Newest entry on top.

---

## 2026-09-06 — manual run (post `_Other/` triage + `prompt-authoring`)

Run against `main` after PRs #11/#12 merged and the prior session's uncommitted catalog docs
were reconciled (`0874bb9`, `17228c6`).

**Step 1 — stale markers:** CLEAN. No live `Memory: pending` / TODO markers in `SKILL-BACKLOG.md`
(the 5 the prior audit flagged were resolved in the reconciliation commit). One stale *note*
fixed: the item-16 "Bonus finding" about `Architecture/reddit-researcher/` still described it as
untriaged with no memory record — updated to point at `skill-folds-other-directory.md` and the
`Research/` relocation.

**Step 2 — catalog-doc sync:** 3 missing `README.md` rows, all added:
- `Research/reddit-researcher` (+ new `### Research` group section)
- `Prompts/prompt-authoring`
- `Business/delete-ai-words`
Plus 3 stale descriptions refreshed for fold changes: `software-carpentier-brand` (feed-post
mode), `spec-drift-gate` (Step 2a), `learning-gate` (`guided-walkthrough.md`).
`SKILL-BACKLOG.md`: added item 18 (`prompt-authoring`) and a `_Other/`-triage entry to the
"Fold into existing skills" section.

**Step 3 — dead references:** CLEAN. Cross-cutting gates all resolve (`ambiguity-gate` ×10,
`learning-gate` ×26, `problem-solving-gates` ×34, `problem-journal` ×6). Deleted skills
(`grill-me`, `my-viral-post`, `how-to`, `linkedin-hook`, `Prompt optimizer`) referenced
nowhere. `reddit-researcher`'s one hit is its own frontmatter.

**Step 4 — untested-pair backfill:** recent work is covered (`skill-folds-other-directory.md`,
`skill-added-prompt-authoring.md`). FLAGGED, not fixed: `Prompts/session-handoff` has no
recorded interaction test and shares a "session state / handoff artifact" concept with
`spec-drift-gate` and `prompt-archive` — low priority, hand to `skill-interaction-testing`
Step 2 if revisited.

**Step 5 — starvation-by-neglect:** 1 gap fixed — `prompt-tester` and `prompt-archive` both said
"not for writing a new prompt from scratch" without naming `prompt-authoring`; added the pointer
to both. `reddit-researcher` is pointed at by nothing but shares no collision surface with any
gate (it's a standalone tool) — not a real starvation finding.

**Applied:** all Step 1/2/3/5 mechanical fixes directly.

**Step 4 backfill (done same day):** ran `skill-interaction-testing` on `session-handoff` (1
worktree agent, 6 scenarios vs `spec-drift-gate` / `prompt-archive` / `problem-journal` /
`ambiguity-gate` + 2 controls). 5 clean; 1 fix — `session-handoff` triggers on
"recap" / "before I forget" and could pre-empt `problem-journal` Journal mode on a post-fix
bug write-up. One-line scope-narrowing clause added to `session-handoff`'s description pointing
resolved-bug post-mortems to `problem-journal`. Memory: `skill-interaction-session-handoff.md`.

## 2026-09-24 — post static-audit pass (whole catalog, 61 skills)

Context: whole-catalog `skill-static-audit` (0 blockers, ~105 should-fixes) followed by three fix PRs
(#34 tiers 1-3, #35 reciprocity + interaction-test fixes, this branch: splits + pointer triage).

**Step 1 — stale markers:** not applicable — `SKILL-BACKLOG.md` not present in this checkout.
**Step 2 — README sync:** not applicable — root `README.md` has no catalog table in this checkout.
**Step 3 — dead references:** CLEAN for skill names. Scripted scan of backticked kebab tokens across all
skill `*.md`: the only unresolved skill-like name is `spec-executor` (`.claude/agents/spec-executor.md`
is missing though `repo-map.md`/`agents.md` describe it) — FLAGGED for a user decision, `spec-drift-gate`
now carries an inline fallback. `equity-trade-decision`, `code-review`, `security-review`, `claude-api`
are plugin/built-in skills, not dead. Frontmatter check: all 61 `SKILL.md` have `name` = directory and
`description:` on line 3 (three folded `>` blocks predate this work).
**Step 4 — untested pairs:** the edited sets were interaction-tested by router scenarios (Architecture/Data,
Skill Development/Prompts, Business writing); fixes applied and 4 of 6 post-fix scenarios re-run clean.
Not re-run: the gym-app prompt after the `entry-point-first` clause.
**Step 5 — starvation by neglect:** CLEAN. Every skill has >= 2 inbound mentions from other skills' files.
55 one-way NOT pointers triaged: 17 back-pointers added (grouped lines, no description growth), ~27
non-issues (consumer-side disclaimers where the target would never claim the request) left deliberately.

**Left for the user:** (a) `data-tier-operations` claims warehouse physical tuning ("which distribution /
sort key") with no body; `index-tuning` and `dimensional-modeling` route it there — add the content or drop
the claim and re-point; (b) restore `.claude/agents/spec-executor.md` or correct `repo-map.md`/`agents.md`.
