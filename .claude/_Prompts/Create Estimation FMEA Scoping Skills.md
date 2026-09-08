---
tags:
  - prompt
  - AI
  - skills
author:
  - jacgit18
Comments: Run in a fresh session from the repo root. Builds the three new Architecture skills identified in the 2026-09-04 note review.
Purpose: Instruct Claude to author capacity-estimation, failure-mode-analysis, and design-scoping as full skills, one at a time, following the repo's skill-authoring process.
Status: Draft
Started:
EditDate: 2026-09-04
Relates: "[[SKILL-BACKLOG]]"
dg-publish: false
---
Build three new skills for this repo, one at a time, in the order below. Full
context for each is in [SKILL-BACKLOG.md](../../SKILL-BACKLOG.md) ("New skills — to
build", items 1–3). Do not start item 4 (`repo-topology`) — its source note needs
enrichment first.

For EACH skill, follow the repo's process end to end before moving to the next:

1. Read the `writing-skills` guidance and an existing Architecture skill
   (`.claude/skills/Architecture/resilience-strategy/`) as the structural template —
   `SKILL.md` entry point + companion `*.md` reference files + a `README.md` that
   places the skill against its siblings.
2. Read the source notes listed for that skill (paths in SKILL-BACKLOG.md) and pull
   the framework/vocabulary from them. Where a source note flags its own math or
   method as shaky, fix the method in the reference file — don't copy the errors.
3. Draft the skill under `.claude/skills/Architecture/<name>/`.
4. Screen it in isolation: write a scenario the skill should catch, confirm a
   baseline agent without the skill fails it, confirm the skill fixes it.
5. Run `Prompts/skill-interaction-testing` against the whole existing skill set.
   Apply the boundary/handoff edits it surfaces — including the reciprocal
   description edits on sibling skills noted in the backlog.
6. Add the skill to the catalog table in [README.md](../../README.md) and tick its
   box in SKILL-BACKLOG.md.
7. Write a memory file recording the skill-interaction-testing result (follow the
   pattern of the existing `skill-interaction-*` memories).

Then stop and report what changed, per skill.

---

## 1. `capacity-estimation` (priority 1)

A gated a-priori estimate. Refuse to produce numbers until the user has stated:
DAU / traffic driver, actions per user, payload sizes, read:write ratio,
peak:average ratio, growth horizon, replication factor. Stating the assumptions is
the rep — do not invent them.

Output: QPS (avg + peak), bandwidth / egress GB/day, storage per day + per year +
replicated, cache working-set memory, server count, and an explicit "what binds
first" line. Hand off: dollars → `technical-cost-decision`; DB bottleneck →
`data-tier-operations`; what-binds-first / overload → `resilience-strategy`;
volume & cardinality → `observability-strategy`.

Boundary lines to write into the description: NOT dollar cost; NOT
shard/replicate-given-the-numbers; NOT a measured live bottleneck (that's
`problem-solving-gates`). This is the estimate before the system or its telemetry
exists.

Reference file should carry a cleaned-up method: the unit and time-conversion
tables, the walk order (storage → traffic → cache → servers), and worked examples.
Sources named in the backlog.

## 2. `failure-mode-analysis` (priority 2)

A structured procedure skill (not a withhold-the-answer gate — model it on
`document-page-check`). Over a design, workflow, or service graph the user
describes: walk each component and interaction; for each, enumerate failure modes
by the nine categories (functional, availability, performance, consistency,
integration, dependency, security, operational, human/process); record cause →
manifestation → impact; score and rank; emit a prioritized failure-mode register.

Include a scoring rubric (RPN = severity × occurrence × detection, plus a lighter
2-axis fallback) and a register format — the source note has neither.

Hand off: mitigations for dependency/overload modes → `resilience-strategy`;
impact ranking → `observability-strategy` alerting; fault-injection / chaos target
list → `test-strategy`.

Boundary line to write into the description AND into `resilience-strategy`'s
description (reciprocal): this skill **enumerates and prioritizes every mode,
proactively, across the whole design and all nine categories**;
`resilience-strategy` **picks the protection mechanism for a known overload or
dependency failure**. `problem-solving-gates` Rubber Duck is one bug happening now.

## 3. `design-scoping` (priority 3)

The front-door gate for the Architecture group. Consolidate all three source notes
into ONE skill (Specifying Scope indepth + Userbase + Define system threshold).
Refuse to design until the user has stated: purpose + audience; functional
requirements + an explicit out-of-scope list; non-functional numeric targets (RPS
ceiling, concurrency, latency budget, uptime, error budget, cost cap); constraints
(team, timeline, existing stack, platforms, compliance — GDPR / HIPAA / PCI DSS);
and the 1–2 features to design deeply.

Output: a scope statement that then sequences into `capacity-estimation`,
`microservices-decision`, `api-interface-style`, `database-architecture`,
`failure-mode-analysis`.

Critical boundary — this is the highest absorption risk of the three. The
description must defer to `ambiguity-gate` for "what do you even mean by this
request" and take over only once "architect / design a system" is the established
intent. Mirror the wording pattern already used between `test-practice-gate` and
`ambiguity-gate`. Also draw a line vs `ticket-evaluation` (that judges/sizes a
defined ticket; this elaborates scope on an undefined ask). If
skill-interaction-testing shows `ambiguity-gate` still swallows the trigger, add a
one-line handoff clause to `ambiguity-gate` pointing system-design requests here.
