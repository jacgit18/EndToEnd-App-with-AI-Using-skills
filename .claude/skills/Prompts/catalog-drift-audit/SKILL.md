---
name: catalog-drift-audit
description: Use when the user asks to audit, health-check, or clean up the skill catalog as a whole — "has anything gone stale," "check the backlog/README are still accurate," "clean up dead references" — or proactively suggest it after a batch of skill work (several skills built or changed in one session) rather than waiting to be asked, since drift accumulates silently otherwise. This is NOT `skill-interaction-testing` — that skill runs once, right after writing or changing one skill, against a deliberately scoped candidate pool, to catch that one skill colliding with its likely neighbors. This skill runs periodically against the whole existing catalog, with no new skill as the trigger, to catch rot that accumulates over calendar time as skills and docs evolve independently: a `SKILL-BACKLOG.md` "Memory: pending" marker that was actually resolved and never updated, a built skill missing from `README.md`'s tables, a skill name mentioned in another skill's description that no longer exists on disk, a pair of long-standing skills that share a collision surface but were never actually tested against each other because neither was "new" when the other shipped, or a skill nobody else's description ever points to. Produces a drift report; applies the mechanical fixes directly (stale markers, missing catalog rows) and flags anything needing judgment (a real rewrite, a genuine contradiction) rather than auto-fixing it.
---

# Catalog Drift Audit

Every other skill in this catalog is triggered by something happening *now* — a request, a new skill being written. Nothing was watching what happens to the catalog *between* those moments. Skills get built, their memory gets recorded (or doesn't), their entry gets added to `README.md` (or doesn't), and six months and a dozen more skills later nobody has looked back to check any of it still lines up. This skill is that look-back — a periodic, whole-catalog pass, not a per-skill one.

## When to run this

- The user asks directly (audit, health check, "clean up the backlog," "is anything stale").
- Proactively, after a batch of skill work in one session — offer it the way `session-handoff` proactively offers a handoff file, don't wait to be asked every time.
- There's no actual calendar automation wired into this repo today. If the user wants this to run on a real cadence unattended rather than opportunistically, that's a `/schedule` or `/loop` job to set up — this skill is the procedure that job would run, not the scheduler itself.

## Step 1 — Stale record check

Every "pending," "TODO," or similarly open-ended marker in `SKILL-BACKLOG.md` (most commonly `Memory: pending`) gets cross-checked against what's actually in the memory directory. A marker left open is not evidence the work is undone — it's just as often evidence the work got done and the marker never got updated. Grep the backlog for the marker pattern, grep memory for a file matching the skill's name, and reconcile: if the memory file exists, the backlog entry is drift, not a real gap.

## Step 2 — Catalog-doc sync check

List every skill directory under `.claude/skills/` and cross-check each one against `README.md`'s per-group tables. A skill that exists on disk and is marked built in `SKILL-BACKLOG.md` but has no row in `README.md` is drift — the README is supposed to be the catalog's table of contents, and an entry-less skill is invisible to anyone reading it to find what's available.

## Step 3 — Dead-reference check

Skill names get cross-referenced constantly, in backticks, across descriptions and bodies (`hands off to X`, `see Y`, out-of-scope pointers). If a skill is ever renamed or removed, every other mention of its old name becomes a dead pointer. Spot-check a sample of cross-references (the fixed cross-cutting gates first — `ambiguity-gate`, `learning-gate`, `problem-solving-gates`, `problem-journal` — since they're the most heavily pointed-to) against the actual directory listing.

## Step 4 — Untested-pair backfill

`skill-interaction-testing`'s own candidate-pool scoping (Step 1 of that skill) means a pair of skills that are *both already established* — neither one was the "new" skill when the other shipped — may never have been tested against each other, even if they'd land in each other's candidate pool today. Sample a handful of same-group pairs and cross-cutting-gate pairs that have no recorded test in memory, prioritized by an actual shared concept (not the full combinatorial set — that grows faster than it's worth checking). Hand any pair worth testing to `skill-interaction-testing`'s own Step 2 onward rather than re-deriving its method here.

## Step 5 — Starvation-by-neglect check

A skill that no other skill's description ever mentions, defers to, or hands off from — despite sharing a plausible collision surface with at least one sibling — is starved by neglect, not by an active conflict. This already happened once for real (`failure-mode-analysis` shipped and was referenced by zero siblings until someone checked); this step makes that check standing instead of a one-off catch. Skim each skill's own "Boundary lines" / out-of-scope text for names it points at, and check the reverse direction is true for at least one of them.

## Step 6 — Report

One drift report, grouped by the five steps above. For each finding:

- **Mechanical fix** (a stale marker, a missing README row, a corrected dead-name reference) — apply it directly, no need to ask.
- **Judgment call** (a real description rewrite, a genuine contradiction between two skills, a pair that actually needs a full `skill-interaction-testing` run) — flag it and hand off, don't resolve it inline.

Record the audit itself in project memory — when it ran, what it found, what got fixed vs. flagged — the same way `skill-interaction-testing` records its own results. An audit that isn't recorded invites the next one to re-discover the same already-fixed drift from scratch.

## What this is not

Not a substitute for `skill-interaction-testing` on a new skill — that check is still mandatory per-skill, this one doesn't replace it, it catches what accumulates *between* those runs. Not a rewrite pass — most findings here are one-line reconciliations (a marker, a missing row), not a reason to restructure a skill's actual content.
