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

## 2026-09-24 (second run, after PRs #34-#38 all merged)

**Steps 1-2:** not applicable — no `SKILL-BACKLOG.md`, no README catalog table in this checkout.
**Step 3 — dead references:** CLEAN. All 61 `SKILL.md` have `name` = directory and `description:` on line 3
(three folded `>` blocks predate the audit). Only non-directory skill-like names are the known externals
(`code-review`, `security-review`, `claude-api`, `equity-trade-decision`) and `spec-executor`, which the rule
files now document as absent from this checkout; `sync-catalog` in `skill-usage-log`'s description is a
command (`.claude/commands/sync-catalog.md`), not a dead skill. `writing-skills` no longer referenced anywhere
and removed from `sync-catalog`'s allowlist.
**Step 4 — untested pairs:** the edited sets were router-tested on 2026-09-24; gym-app scenario
(`design-scoping` vs `entry-point-first` after the added clause) deliberately not re-run.
**Step 5 — starvation:** CLEAN. Every skill has >= 2 inbound mentions. Full one-way scan: 122 pairs, 6 real
back-pointers added, 116 documented non-issues (table in the session scratchpad, categories: hub fan-out,
ADR-template reuse, audit examples, consumer-side disclaimers).
**Companions:** no unreferenced companion files.
**FLAGGED, not fixed:** three SKILL.md files now exceed the ~250-line split heuristic — `failure-mode-analysis`
(279), `capacity-estimation` (272), `disclosure-gap-audit` (271). They are procedures with worked examples;
split candidates if a further trim pass is wanted (worked examples -> companion, as done for the other four).

## 2026-09-24 (addendum) — gym-app scenario re-run

Re-ran the one scenario left open: `design-scoping` vs `entry-point-first` after the added
"plain 'I'm building X, where do I start' goes to design-scoping" clause. Six router prompts
(gym app where-to-start, overwhelmed, repo, dashboard, "what should v1 include", inherited codebase):
all six routed as expected, no stacking. Bodies also resolve the two soft spots (the documented
v1 sequence in `design-scoping`; the three-bullets rep then hand-off to `spec-drift-gate` in
`entry-point-first`). Two optional nits left unapplied by design (add "make me a dashboard" as an
`entry-point-first` example phrase only if it ever mis-routes in practice; mirror the stall carve-out
in `design-scoping`'s body). No open items remain from the 2026-09-24 audit.

## 2026-09-24 (addendum 2) — layout, listing budget, blind routing test

- **Layout:** the grouped layout (`.claude/skills/<Group>/<name>`) was not discovered by Claude Code (no catalog
  skill appeared in the skill list; usage logs showed only new-skill/code-review/run). Flattened to
  `.claude/skills/<name>/`; groups live in `.claude/skills/INDEX.md`. After the move the skills appeared in the list.
- **Listing budget:** official docs truncate a description at 1,536 chars, and the listing has a TOTAL budget
  (measured: ~29.7k chars of `- name: description` fit, ~31.6k did not, leaving skills name-only). All 61
  descriptions trimmed twice (142k -> 30.2k -> 23.5k chars); every cut sentence lives verbatim in each body's
  `## Routing boundaries (full)`. Catalog listing text ~24.9k, ~16% under the measured fit.
- **Blind routing test** (routers saw only the listing text, 66 prompts covering every skill + no-skill cases):
  65/66 first-choice correct. The miss, "I'm building a gym app, where do I start" -> `entry-point-first`,
  was a regression of the earlier clause; restored in both descriptions and re-tested (8/8 gym-cluster prompts).
  Caveat: prompts contained trigger words, so the score is optimistic for oddly-phrased requests.
- **Lint:** `scripts/skills/lint.sh` now automates frontmatter, dead-pointer, length and one-way-pointer checks;
  the SessionStart hook surfaces errors only.
- **Left as warnings:** `change-surface-audit` (267 lines), `data-access-layer` (260), `disclosure-gap-audit` (258),
  `serverless-execution-model` (251) exceed the 250-line split heuristic.

## 2026-10-01 — skill-usage-log feedback pass (overrides + organic-use read)

**Overrides.** Ran the override-phrase recipe over all 8 skills-log days. **Zero overrides** found
across 86 distinct skill fires with a same-session follow-up (2026-09-13 excluded: no matching
`<date>.md` prompt log that day, so its fires are unchecked). No evidence of the user bypassing a
gate with "just tell me" / "skip this" / etc. in this window. Clean result, but note the phrase
list is a heuristic and this is the first time it's been run — no prior baseline to compare against.

**Organic-use vs. construction-day fire (new finding, not previously tracked).** Cross-referencing
fire dates against each skill's own build date shows the top-line usage tally is contaminated: the
great majority of the 55 skills sitting at count=1 fired on **2026-09-24**, the day of a bulk
`new-skill` / interaction-testing pass (confirmed via the per-day breakdown and the override-recipe
output above, which shows ~60 distinct skills firing that single day). That is very likely each
skill's own isolation-screen exercise, not an independent reach-for-it during real build work — the
log has no field distinguishing "fired because the build needed it" from "fired because this skill
was being constructed/tested that day." `tech-decision-walkthrough` (5 fires spread 09-24..09-29)
and `session-handoff` (17 fires spread 09-24..10-01, partly hook-nudged) are the clearest examples
of genuinely organic, repeated, cross-day reuse. Recommendation for the next audit: when scoring
"never used" or "lightly used," exclude a skill's own creation-day fire from the organic count, or
flag it separately, so a future tally doesn't read construction-testing as field validation.

**Never fired since logging began (unchanged from the count/never-used pass earlier this session):**
`context-promotion` (pre-dates this session's build-out, no construction-day excuse — a real
candidate for a routing check), `repo-reality-audit`, `web-vitals-audit` (both newly added, not
yet due to fire organically).

No description edits proposed this pass — nothing here points to a specific wording fix, only a
measurement-method fix for the next `catalog-drift-audit` / usage-log run.

## 2026-10-03 — whole-catalog mechanical pass (70 skills), ahead of global/plugin packaging

- **Steps 1–2:** skipped (`SKILL-BACKLOG.md` and README catalog table absent in this checkout).
- **Step 3 dead references:** none real. 8 backticked names flagged by the heuristic were concepts or
  external skills (`threat-model`, `pip-audit`, `equity-trade-decision` = anthropic-skills, etc.).
- **Step 5 starvation:** none; every skill has 3+ inbound pointers.
- **Mechanical fixes applied:** 11 one-way description pointers → 0, by adding reciprocal "Not for"
  bullets to the Routing boundaries section of `problem-solving-gates`, `debugging-layer-selection`,
  `test-case-discovery`, `catalog-drift-audit`, `change-surface-audit`, `observability-strategy`,
  `spec-drift-gate`, `test-strategy` (bodies only, no description budget spent). Trimmed
  `repo-reality-audit` description from ~1,500 to ~480 chars (carve-outs already in its body);
  listing total 29,051 → 28,172 chars.
- **Step 4 (untested old pairs):** flagged, not run. Handled by the Data-cluster interaction test.
- **Usage read:** organic repeat use only for `session-handoff`, `tech-decision-walkthrough`,
  `spec-drift-gate`; 8 skills never fired (`browser-test-tooling`, `bug-hunt-drill`,
  `context-promotion`, `deprecation-sunset`, `diagnostic-injection`, `idea-to-first-test`,
  `repo-reality-audit`, `web-vitals-audit`). Most are new; no action.
