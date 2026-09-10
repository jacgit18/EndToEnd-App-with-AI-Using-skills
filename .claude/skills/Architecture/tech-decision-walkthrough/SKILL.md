---
name: tech-decision-walkthrough
description: A coached, conversational procedure for choosing a build's technologies out loud — one decision at a time, system-design-interview style — instead of a stack appearing fully formed. Use when someone is building something and wants the technology choices reasoned through with alternatives and tradeoffs made explicit: "help me pick the stack and explain why", "walk me through the tech choices like a system design interview", "what are my options for X and the pros and cons", "compare A vs B vs C for this build and recommend one", "reason through each decision as we build together", "talk me out of it if I'm wrong". For each decision it frames what forces the choice, takes the user's lean and known constraints, lays out 2–4 realistic candidates, names the axes that actually discriminate for THIS build, scores them honestly (including where the rejected option is better), gives a recommendation with a "because" tied to an axis, lets the user make the call, and records a short ADR. Depth scales with blast radius; load-bearing decisions route into the specialist Architecture skill and come back as an ADR. Two registers — collaborative (Claude presents and recommends, default) and interviewer (user proposes and defends, Claude probes) — set by `learning-gate`'s assistance level. NOT `problem-solving-gates` Options Generator, which withholds Claude's option list until the user brings their own candidates + a lean — that gate makes the user generate; this skill teaches the option space. If the user wants to be forced to produce options first, hand to Options Generator. NOT `design-scoping`, which states a system's purpose / audience / non-functional targets and picks which 1–2 decisions deserve deep design — it does not run the candidate-by-candidate tradeoff conversation; this skill is downstream and walks its decision list, and a whole-system one-liner with no scope goes to `design-scoping` first. NOT the specialist Architecture decision skills used alone (`api-interface-style`, `microservices-decision`, `database-architecture`, `deployment-strategy`, `access-control-modeling`, `bff-gateway-placement`, `serverless-execution-model`, `migration-cutover`, `config-and-secrets-management`, `cloud-iam-boundary`, `capacity-estimation`) — those are the deep gates for one decision each; this skill is the learning-mode conversation across the whole set that routes into them and collects the ADRs. A single already-isolated decision with its inputs ready goes straight to the specialist. NOT `technical-cost-decision`, which owns the recurring-cost axis for one decision — this skill invokes it as one axis among several. NOT `incremental-build-pacing`, which delivers already-chosen technology file by file — this chooses it; they chain. NOT a full mock-interview drill (requirements → estimation → high-level design → deep dive → wrap). NOT `system-design-communication` Mode 3 (Tradeoff Defense): if the user wants a choice they have *already made* stress-tested with no recommendation wanted ("don't tell me the answer", "just poke holes", "help me defend X"), that is Mode 3 — this skill always lands a recommendation and writes an ADR, Mode 3 never declares a winner and records nothing. NOT for a decision already settled in a live ADR the user is not reopening.
---

# Tech Decision Walkthrough

When a build's technology gets chosen silently — "I'll use X + Y + Z" appears fully formed — the
user never sees the option space, the axes that mattered, or why the alternatives lost, and the
chance to learn how to reason about stack choices is gone. The opposite failure is a comparison
lecture that never lands a decision. This skill runs each decision as a short, honest exchange:
options on the table, axes named, a recommendation with a "because", the user's call, an ADR.

It is a **procedure**, not a withholding gate. `learning-gate` sets the assistance level (which
register, how much of the reasoning Claude does); this skill runs the loop at that level.

## Step 0 — Preconditions (light)

- **A scope exists** — what's being built, for whom, rough constraints — from `design-scoping`,
  a spec, or the conversation. A whole-system one-liner with none of this → `design-scoping`
  first, then come back.
- **Check `docs/architecture/decisions/`** — including `_archived/` and any superseded entries —
  for prior leanings and re-derivation notes. A decision already recorded in a *live* ADR the
  user isn't reopening is settled; don't re-walk it. An archived / superseded ADR is prior data,
  not a settled answer — mention its lean, don't defer to it.
- **If a scope or spec doc asserts a decision the user now wants reasoned out** (e.g. a "stack
  fixed by the owner" line), name the contradiction, confirm they're reopening it, and treat it
  as open for the walkthrough. Don't silently override the doc, and don't let it shut down a
  decision the user explicitly asked to walk.
- **The list of decisions to walk.** Draw it from the scope's functional + non-functional needs
  and the build's shape. Typical set: language / runtime, web framework, datastore(s),
  data-access layer, frontend approach, API style, auth approach, background work, packaging,
  deployment target, observability. Cut the ones this build doesn't face; add domain-specific
  ones (for a finance app: money representation, rounding, audit trail).
- **The register** — **collaborative** (default) or **interviewer**. `learning-gate`'s
  assistance level sets it; the user switches anytime ("let me drive", "just show me the
  options"). Detail in `decision-loop.md`.

Don't gate harder than this. The rep is the reasoning *during* each decision, not a wall of
pre-questions.

## Step 1 — Order the decisions

Walk them in dependency order — the ones that constrain others first: runtime before framework,
datastore before data-access layer, deployment target before packaging specifics, API style
before frontend data layer. Show the ordered list once, and tag each with its Step 3 depth class
(load-bearing / structural / routine) in the same table — classifying while you order is fine,
the step numbers are the read order, not a strict sequence. One decision per exchange.

## Step 2 — The per-decision loop

For each decision — full protocol and the axes libraries are in `decision-loop.md`:

1. **Frame it** — what's being decided, and what forces it now (a slice needs it, a constraint
   triggers it). One sentence.
2. **Get the user's starting position** — what they lean toward, and the constraints they
   already know: team skills, existing systems, ops capacity, deadline, cost ceiling,
   compliance. In interviewer register they also give the reasoning; in collaborative a lean is
   enough. No lean is a fine answer — say so and continue.
3. **Candidate set** — 2–4 realistic options for *this* build, not a survey of the field. One
   line each: what it is, where it shines, where it hurts.
4. **Deciding axes** — the 2–4 dimensions that actually discriminate here. Name them *before*
   scoring. This is the interview move: make the evaluation criteria explicit. When the
   decision is "which library/package for X", use `library-vetting.md` for the supply-chain
   axes (weight, maintenance, license, security, exit cost) an improvised list skips.
5. **Score against the axes** — a compact comparison. Be honest where a rejected option is
   genuinely better; a comparison with no cost to the winner isn't finished. When one axis is
   **recurring cost**, give two reads — the user's actual plan *and* a short realistic-scale
   example naming the cost driver — per `decision-loop.md` "When cost is a deciding axis". If
   the candidates cost the same at every scale, cut the axis; don't invent numbers.
6. **Recommendation + because** — one clear lean, tied to a named axis and the stated
   constraints. Not hedged, not a menu handed back.
7. **User decides** — agree, override, or ask for another round. An override with a stated
   reason is a fine outcome — record the reason, not a rebuttal.
8. **Record it** — a short ADR (context / decision / alternatives considered + why they lost /
   consequences) to `docs/architecture/decisions/NNN-<slug>.md`, numbered as the next integer
   after the highest existing ADR. For a load-bearing decision, run the specialist Architecture
   skill first and fold its output into the ADR. **If the decision changes an upstream story or
   stated requirement** (a backlog item, a spec line), log the amendment in the spec/backlog
   drift log too — not just the ADR — so `spec-drift-gate` sees it.

**Sub-decisions and emergent decisions.** If a decision has linked sub-parts (e.g. "money
representation" = type + balance strategy + dedupe key), enumerate them at the top of the loop
and land them into **one** ADR, walking each sub-part as its own mini frame→axes→recommend. If
the walk surfaces a decision that isn't on the Step 1 list, **add it to the list** (with its
depth class) rather than cramming it into the current decision's loop.

## Step 3 — Depth control

Not every decision earns the full loop. Scale it to blast radius (`design-scoping`'s
significance axis):

| Class | Test | Treatment |
|---|---|---|
| **Load-bearing** | Changing it later means a migration or rewrite — datastore, money representation, sync-vs-async core, service boundaries, auth model | Full loop; route to the specialist Architecture skill; full ADR |
| **Structural** | Shapes the code but swappable with contained effort — web framework, data-access layer, frontend library, test strategy | Full loop; inline ADR |
| **Routine** | Easily reversible — formatter, test runner, a small utility lib, CI provider | Name the pick + a one-line because; no loop; batch several into one note |

## Step 4 — Closeout

When the last decision on the list has an ADR, don't just stop — run the closeout:

1. **Summary table** — one row per decision: choice, ADR number, depth class. Put it where the
   ADRs live (a `stack-walkthrough.md` log, or the spec).
2. **Cross-cutting obligations** — collect every downstream requirement the decisions surfaced
   that isn't itself an ADR (HTTPS, rate limiting, CSRF handling, a reconciliation job,
   backups, CI, a domain name). These get lost otherwise — list them so they can be slotted
   into the build, not discovered late.
3. **Spec amendments** — list every upstream story/requirement a decision changed, cross-linked
   to the ADR and the drift-log entry.
4. **Missed-decision audit** — scan the axes-library headings and the build's shape for
   decisions not walked: config & secrets, test tooling (front and back), CI provider,
   date/time & timezone policy, container base images, i18n/a11y if relevant. Name each with a
   one-line recommendation and whether it's ADR-worthy or a build-time detail.
5. **Deferred list** — what was explicitly pushed to v2 / build-time, in one place.
6. **Hand off** — to `spec-drift-gate` (fold the ADRs + amendments into the build spec), then
   `incremental-build-pacing` for the paced build. A rough dependency-ordered build sketch is a
   useful thing to hand over but isn't this skill's job to finalize.

Don't wait to be asked for the closeout — it's part of finishing.

## Registers (summary — detail in `decision-loop.md`)

- **Collaborative (default).** Claude frames the decision, presents candidates + axes, scores,
  and recommends; the user weighs in and decides. Assistance level 3.
- **Interviewer.** The user proposes the choice and defends it; Claude probes the way an
  interviewer would ("why not X? what happens at 10× the data? what's your ops story?") and only
  fills the gaps the user misses. Assistance level 1–2. Use on "let me drive" / "quiz me".

## Never

- Assert a stack without walking it when the user asked to reason through the choices.
- Lecture without landing a decision — every loop ends in a recommendation and the user's call.
- Give a recommendation with no "because", or a "because" not tied to a named axis.
- Hide the cost of the winner. Every choice loses something; name it.
- Run the full loop on a `.prettierrc`. Match depth to blast radius (Step 3).
- Re-open a decision already recorded in an ADR unless the user is explicitly reconsidering it.
- Withhold the option list to force the user to generate it first — that is
  `problem-solving-gates` Options Generator, a different skill the user has to ask for.

## Escape hatch

If the user wants the fast answer for one decision with no walkthrough — give the recommendation
+ a one-line because + the top alternative, and move on. "Do the whole stack, don't explain it"
→ hand to `spec-drift-gate` with no walkthrough.

## Example invocations

> "Let's build the finance dashboard. Walk me through the stack choices like a system design
> interview — I want to understand the tradeoffs, not just be handed a framework."

Collaborative register (no "let me drive" signal). Step 0: scope is in the spec + scope doc;
decision list = runtime, web framework, datastore, data-access, frontend, API style, auth, money
representation, packaging, deployment. Step 1: order them. Step 2: first decision — runtime —
framed, user's lean, 3 candidates (Python / Node / Go), axes (team familiarity, ecosystem for
CSV/finance, async needs, deploy footprint), honest score, recommendation with the because, user
decides, ADR.

> "I think Postgres is right for this but talk me out of it if I'm wrong."

One decision, user has a lean + reasoning → collaborative, single loop. Candidates (Postgres /
SQLite / a document store), axes (relational query needs, single-user scale, ops burden, backup
story), honest score, recommendation (likely agree, with the because), ADR.

> "Just pick a test runner."

Routine → escape hatch: "pytest — standard for Python, fixtures + parametrize cover this, no
compelling alternative at this size." No loop.

> "Give me options for the auth approach and make me choose."

The user wants to be *gated* into committing first → `problem-solving-gates` Options Generator,
not this skill. Hand off.

## Portability

Repo-agnostic. Reads `docs/architecture/decisions/` and any scope / spec docs for context;
writes new ADRs there. Copy the `tech-decision-walkthrough/` directory into another repo's
`.claude/skills/` to use it there. See `README.md` for its place among the sibling decision
skills.
