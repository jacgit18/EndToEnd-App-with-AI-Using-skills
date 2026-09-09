---
name: incremental-build-pacing
description: Use when the user is doing AI-assisted implementation of an already-planned build and wants it delivered slowly — one file or one small unit at a time, pausing so they can absorb each piece — instead of a large multi-file batch dropped in one turn. Triggers on "build this file by file", "go one file at a time", "slower, I want to follow along", "walk me through building this so I learn the codebase", "don't generate it all at once", or a mid-build request to slow the cadence down. Sets the increment size (one file / one cohesive unit like a model + its migration / one thin vertical slice), the checkpoint cadence, and whether Claude writes each piece for the user to review or shows it for the user to type, then runs a write → explain → check-understanding → next loop. NOT for deciding what to build or bounding scope — a spec, slice, or story must already exist; if it doesn't, that's `spec-drift-gate` (multi-file / multi-session build with no written spec) or `design-scoping` (a whole system to scope) first, and this skill governs delivery only once that is settled. NOT for classifying whether the user wants to learn at all, or setting the assistance-level ceiling — that's `learning-gate`, which routes here from its Step 3 table once intent is learning and the rep is "understand a build as it's assembled". NOT a procedure the user performs entirely with their own hands — environment setup, wiring two tools together, a runbook they'll repeat — that's `learning-gate` → `guided-walkthrough.md`; this skill covers a build where Claude may still write the code and the point is comprehension-paced delivery. NOT bug-fixing, an optimization, or an architecture decision that comes up mid-build — `problem-solving-gates`. Drops the pacing immediately on "just build it" / "execution mode".
---

# Incremental Build Pacing

A planned build fails to teach when it arrives all at once. The spec is written, the slice is
chosen, intent reads as "execution" — so Claude emits thirty files and a thousand lines in one
turn. The user who wanted to *understand* the codebase they are accumulating now owns a finished
tree they never read. This skill paces delivery to comprehension: small increments, each
explained and checked, before the next one is written.

It governs *how* a slice is delivered. It does not decide *what* the slice is — that is settled
before this skill runs.

`learning-gate` routing here from its Step 3 table is one way in, not the only one. When the
skill is reached directly — the user asked for file-by-file delivery outright — take the
learning intent as already established and go straight to Step 1; don't bounce back to
`learning-gate` to re-confirm it.

## Step 1 — Does this skill apply?

| Situation | What to do |
|---|---|
| No spec, slice, or story yet — what to build isn't settled | `spec-drift-gate` (a multi-file / multi-session build with no written spec) or `design-scoping` (a whole system to scope). Come back once a concrete slice is named. |
| The stack itself isn't chosen yet — the user wants to reason through the technology decisions | `tech-decision-walkthrough` first (it picks the stack and writes the ADRs); then it chains `→ spec-drift-gate → ` here. |
| The user wants the build done, fast, with no learning goal | Doesn't apply. Normal execution — don't impose pacing on someone who didn't ask for it. |
| A procedure the user will carry out end to end themselves — env setup, wiring two tools, a runbook they'll repeat | `learning-gate` → `guided-walkthrough.md`. The user makes every move there; here Claude may still write the code. |
| A bug, a slow path, or an architecture choice surfaces mid-build | `problem-solving-gates` for that sub-problem, then resume the loop. |
| A spec / slice exists and the user wants to follow the implementation as it's built, to understand it | Continue to Step 2. |
| Mid-build: the user asks to slow down, go file by file, or "redo this slower" | Continue to Step 2, then resume from where comprehension actually stopped. |

## Step 2 — Set the pacing contract (before writing any code)

Three things, stated by the user. Draft them from context and confirm — don't impose a cadence
the user didn't ask for, and don't start building to find out.

1. **Increment size** — the unit delivered per turn:
   - one file, or
   - one cohesive unit — a model + its migration; a router + its schema; a component + its hook, or
   - one thin vertical slice — a single endpoint through every layer.
2. **Checkpoint cadence** — stop after *every* increment (the default the first time through an
   unfamiliar stack), or after every unit / slice once the user reports it's dragging.
3. **Who writes it** — Claude writes each increment and the user reviews it, or Claude shows what
   to write and the user types it. Default: Claude writes, and the user must explain it back.

Write the contract down — one line in chat the user can point back to. If the user says "just
start", pick the defaults (one file, stop after each, Claude writes), say so in one line, and
proceed.

Present the contract and the Step 3 increment map together in one turn and pause there — one
agreement gate, no code, not a separate round-trip for each.

## Step 3 — Map the increments for this slice

Before writing anything, list the files or units this slice needs, in dependency order. Show the
list once. Don't start until it's agreed.

Tag each increment one of three ways — the worked table with examples is in
`increment-delivery.md`:

- **Plumbing** — no mental model at stake (empty `__init__.py`, boilerplate config, lockfiles,
  `.gitignore`, generated scaffolding, a one-line router include). **Batch these** into a single
  "skim these" step: together, one line each, no comprehension check. A quiz on an empty package
  marker wastes the rep. On a slice added to an existing codebase there may be almost none — fine.
- **Structural** — the shape matters but the mechanism is familiar (a schema, a plain CRUD
  router, a list component). One per turn or grouped into a unit; short explanation, light check.
- **Load-bearing** — a wrong mental model costs later: a money / precision round-trip, an auth
  dependency, the ORM session lifecycle, a dedupe key, the dev-server proxy or CORS wiring, a
  migration that is hard to reverse, or anything that introduces a framework primitive the user
  hasn't met yet. One per turn, full explanation, comprehension check. When unsure, tag it
  load-bearing.

## Step 4 — The delivery loop

Per increment. The full protocol — the exact shape of each step, the coaching register, the
checkpoint-quiz mechanics — is in `increment-delivery.md`.

1. **Write it, or show it to type.**
2. **Explain** — what it does, why it's shaped this way, how it connects to what already exists,
   and the one thing that usually trips people on this kind of file.
3. **Stop.** The turn is the user's. Don't narrate the next increment or assume this one landed.
4. **Check understanding** — the user says back what the increment does and how it connects; a
   real "why", not the code restated in prose. Before an increment that builds directly on this
   one, use `AskUserQuestion` for a one-question checkpoint — answer position varied, not revealed
   until they submit.
5. **If it's shaky, stay here** — a smaller sub-piece, or a plainer explanation. Don't advance on
   a parrot.
6. **Advance** — only now write or reveal the next increment.

## Step 5 — Drift and scope

If writing an increment reveals the slice was mis-scoped — it needs a file the map didn't
mention, or a decision nobody actually made — that is a `spec-drift-gate` Step 4 decision. Name
it out loud, amend the spec or pull back, and only then keep building. Don't fold it in silently
because "it's basically part of this slice."

## Ending

Stop when all three are true: every file in the slice exists, the user can explain the slice end
to end without looking, and the user could change one piece without breaking the others.
Understanding each file in isolation isn't done — the connections are the point.

Show the increment list fully checked, say in one line what the user can now do that they
couldn't before, and stop. If time runs out first, save the list with the current place marked
and the next increment named.

## Never

- Impose pacing on execution-intent work with no learning goal.
- Emit the next increment before the current one is understood.
- Run a comprehension check on batched plumbing.
- Manufacture difficulty — if the user plainly gets a piece, don't stage a quiz for it.
- Keep pacing after "just build it" / "execution mode" — drop it for the rest of the thread, the
  same switch rule `learning-gate` uses.
- Decide scope here. No spec → hand back to `spec-drift-gate` / `design-scoping`.

## Escape hatch

If the user is following comfortably and wants to move faster, widen the increment (file → unit →
slice) or stretch the cadence *before* dropping the skill entirely. An explicit "execution mode"
always wins immediately, no negotiation.

## Example invocations

> "Let's build the auth slice — one file at a time, explain each, I want to actually learn this
> stack."

Step 2: one file / stop after each / Claude writes, user explains back. Step 3: map the auth
files (`config` → JWT util → auth dependency → login router → token schema), mark the dependency
and the JWT util load-bearing. Then run the loop.

> "You just dumped 40 files on me. Can we redo this slower?"

Mid-build entry. Set the contract, map what's left, resume file by file from where the user's
understanding actually stops — not from file 41.

> "Build the whole dashboard, I don't care how, just make it work."

Execution, no learning goal → this skill doesn't apply.

> "Walk me through setting up the Postgres container and running the first migration myself."

The user performs it end to end → `learning-gate` → `guided-walkthrough.md`, not here.

## Portability

Repo-agnostic. Writes no project files of its own; produces the increment list and the paced
delivery in chat. Copy the `incremental-build-pacing/` directory into another repo's
`.claude/skills/` to use it there.
