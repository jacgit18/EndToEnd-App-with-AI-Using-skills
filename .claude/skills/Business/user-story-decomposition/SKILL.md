---
name: user-story-decomposition
description: Use when a feature, epic, or requirement needs to become concrete backlog items — "write user stories for X", "break this epic down", "what's the acceptance criteria for X", "should this be a use case or a user story", "turn these requirements into a backlog", or a named actor + action that needs a proper As-a/I-want/so-that with acceptance criteria. Decides the artifact format first — a user story (single actor, straightforward flow, negotiable in conversation) versus a use case (multiple actors/systems, meaningful alternate or error paths, a need for formal traceability) — then walks epic → user story → acceptance criteria, holding each story to the INVEST-style quality bar (cohesive, complete, consistent, correct, modifiable, unambiguous, feasible, testable) and a Definition-of-Ready checklist before calling it ready. This is downstream of `design-scoping`, whose functional/in-scope list is exactly the input this skill decomposes — that skill states a system's purpose, audience, non-functional targets, and constraints; it does not break the functional list into stories, and this skill does not re-scope the system, size non-functional targets, or pick the 1–2 deep-dive architecture decisions. It is upstream of `ticket-evaluation`, which judges whether an already-written, already-scoped ticket belongs in the sprint — this skill authors the story, that skill judges it once written; a bare feature name with no breakdown routes here if the ask is "turn this into stories," or to `design-scoping` first if the ask is to scope a whole system around it. Does not run the stakeholder interview/elicitation conversation that produces the raw requirement in the first place (unowned), and does not draw the UML diagrams the source material mentions — its output is textual backlog items, not diagrams.
---

# User Story Decomposition

A requirement is not a backlog. Between "we need X" and a sprint-ready set of stories sits a
format decision (which artifact actually captures this) and a breakdown discipline (epic →
story → acceptance criteria, each held to a quality bar) — skip either and the backlog fills
with items that are the wrong shape, missing a stated benefit, or missing the acceptance
criteria that would have made them testable. This skill forces both steps in order.

## Out of scope — hand these off

- **Scoping a whole system** — purpose, audience, functional + explicit out-of-scope,
  non-functional numeric targets, constraints, which 1–2 decisions deserve deep design →
  `design-scoping`. That skill's functional/in-scope list is this skill's typical input;
  don't re-derive it here, and don't let this skill quietly re-open it.
- **Judging or sizing an already-written ticket** — "should this be in the sprint," "how
  risky is this," backlog grooming across several tickets → `ticket-evaluation`. That skill
  separates what a ticket says from what it's missing and ends in a proceed/defer verdict;
  this skill ends when the story and its acceptance criteria are written, before anyone
  judges whether to build it now.
- **The technical design a story implies** — a schema, an API shape, a service boundary, a
  permission model. If a story surfaces one of these as load-bearing, name it and hand off
  to the specialist Architecture skill (`database-architecture`, `api-interface-style`,
  `microservices-decision`, `access-control-modeling`, etc.) rather than deciding it here.
- **Running the elicitation conversation** — the stakeholder interview, workshop, or survey
  that produces the raw requirement in the first place (question ordering, meeting
  structure, stakeholder mapping). Not owned by any skill in this catalog yet — if asked to
  run that conversation, say so rather than silently treating a first-pass guess as the
  requirement.
- **Drawing the UML diagrams** — a use case, sequence, or activity diagram. This skill's
  output is the textual structure those diagrams would visualize; it names when a diagram
  would help and stops there.
- **A vague ask with no established feature** — "help me with my backlog," "make this
  better" → `ambiguity-gate` first, to resolve what's actually being asked.

---

## The gate

Before writing a single story, three things must be stated — not invented:

1. **The epic or feature being broken down**, in the user's own words. "Build the
   notifications system" is a system to scope (`design-scoping`), not a feature to
   decompose. "Users can subscribe to and receive email digests of their notifications" is
   a feature this skill can work with.
2. **The actor(s)** — the real user type(s) this feature is for, stated by the user. Do not
   invent a persona to fill the "As a ___" slot. If the feature genuinely serves more than
   one actor (a requester and an approver, a visitor and an admin), that is one story set
   per actor, not one story that quietly conflates two roles.
3. **The format signal for this feature** — does it need a **use case** or a **user story**?
   See the decision below. If unclear, ask directly; don't default to whichever is easier to
   write.

**Don't invent:**
- No invented personas beyond what the user stated.
- No invented benefit. "So that they have a better experience" is filler wearing a benefit's
  clothes — if the real "so that" isn't known, ask for it rather than writing a generic one.
  A story's benefit is what makes a later scope fight resolvable; a fabricated one resolves
  nothing.
- No acceptance criterion that isn't implied by the stated feature. An AC list is scope —
  padding it invents scope nobody asked for, and thinning it under-specifies what "done"
  means.

**Escape hatch:** if the user already states the actor, the action, the benefit, and enough
of the flow to see whether branches matter, assemble directly — don't re-interrogate a fully
specified opening.

---

## Format decision — use case vs. user story

| Signal | Use case | User story |
|---|---|---|
| Number of actors/systems involved | Multiple (a user *and* a downstream system, or two human roles) | One |
| Alternate / error paths | Meaningful enough to document up front (a payment fails, a validation rejects, a timeout occurs) | Handled as follow-up conversation or a separate story, not pre-documented |
| Need for formal traceability | Audit, compliance, or contractual sign-off requires a structured artifact | Agile team, negotiable in conversation, no such requirement |
| Altitude | A full interaction end-to-end | One thin, sprint-sized slice of that interaction |

Most agile-team work is a user story. Reach for a use case when the branching itself is the
point — a password reset with three failure paths that all matter to design now is a use
case; "let the user reset their password" as one slice of that flow is a story. The two are
not mutually exclusive: a use case's main success scenario commonly gets implemented as one
or more user stories, each with its own acceptance criteria.

**Use case structure:** Title · Actors · Preconditions · Main Success Scenario (numbered
steps) · Alternative Scenarios (each a deviation, named) · Post-conditions.

**User story structure:** "As a `[actor]`, I want `[action]`, so that `[benefit]`."

---

## The ladder

```
Theme        →  a strategic objective (rarely stated explicitly; usually implicit in a
                 design-scoping purpose statement)
Epic         →  a large initiative, too big for one sprint
Feature      →  epics decomposed into a focused unit, still multi-sprint
User Story   →  one sprint-sized, user-perspective slice — this skill's usual unit of output
Acceptance
Criteria     →  the testable conditions that make one story "done"
```

This skill typically enters at **Epic or Feature** (design-scoping's functional-list items
land here) and works down to **User Story + Acceptance Criteria**. Themes are context, not
something to draft. Sub-tasks (the implementation-level breakdown of one story) are out of
scope — that's planning, not requirements.

**Rough sizing signal** (not a substitute for the team's own estimate): a slice expected to
take **less than one sprint** is probably not epic-sized — check whether it should just be a
story. One that would run **more than 5–6 sprints** is too big for one epic — split it into
two before writing stories under it, rather than writing an unbounded story list.

---

## Writing the stories

For each capability inside the epic/feature:

1. Write the story: `As a [actor], I want [action], so that [benefit].`
2. Attach acceptance criteria — either a plain bulleted list of outcomes or
   Given/When/Then, matching whichever the team already uses. Each criterion is one
   testable, in-scope outcome; list what's explicitly *not* covered if a reader would
   otherwise assume it is (a flight-search story's criteria naming alternate dates and
   destinations, but explicitly not rewards points, is the shape to match).
3. If an acceptance criterion is itself branching into a distinct piece of future work,
   that's a signal it wants to become its own story — note it, don't force it into this
   one's criteria.

### Splitting a story that's too big

Check whether all of these are needed *right now*, in this order — drop or defer whichever
aren't:

- **Conditions** — are all the stated conditions required immediately, or can some wait?
- **Workflow steps** — is this too many steps for one slice?
- **Paths** — does the happy path alone deliver value, with alternates deferred?
- **Operations** — are all the named operations (create/read/update/delete/etc.) needed now?
- **Acceptance criteria** — are all the test scenarios needed at this point, or do some
  belong to a later story?
- **Data / interfaces / platforms** — are all the named variations (formats, integrations,
  client platforms) needed immediately?

A story that fails this check is written as two or more stories, not one story with a longer
list of acceptance criteria.

---

## Quality bar — run this against every story before calling it done

| Attribute | What it means here |
|---|---|
| **Cohesive** | One topic — one business process, interface, or event. Not two features stapled together. |
| **Complete** | Self-contained; a reader doesn't need a side conversation to know what's being asked. |
| **Consistent** | Doesn't contradict a related story; similar level of detail to its siblings. |
| **Correct** | Matches what the actor/subject-matter source actually said, not a plausible guess. |
| **Modifiable** | Structured so a later change doesn't require rewriting unrelated stories. |
| **Unambiguous** | One reading. If two people would build different things from it, it's not ready. |
| **Feasible** | Achievable given the team, tools, and time actually available. |
| **Testable** | The acceptance criteria give someone outside the story's author a way to verify it. |

A story failing **Testable** almost always traces back to acceptance criteria that were
skipped or left vague — fix that before rewriting the story prose.

## Definition of Ready — before the backlog calls it ready

Business value stated · acceptance criteria + any needed data sets written · dependencies,
risks, and constraints named · priority set · a rough size/estimate given · testability
confirmed. A story sitting in the backlog missing several of these isn't ready regardless of
how well-written its prose is — name the gaps rather than rounding up.

---

## Prioritizing within an epic (optional pass)

When several candidate stories are competing for the same release and the team needs a fast
categorical cut (not the deeper ten-dimension read `ticket-evaluation` gives one already-
written ticket), use **MoSCoW**:

| Category | Meaning |
|---|---|
| **Must-have** | Non-negotiable; the release fails its objective without it. |
| **Should-have** | High-value, not launch-blocking. |
| **Could-have** | Desirable if time and resources allow. |
| **Won't-have (this time)** | Explicitly deferred — say so, don't just omit it. |

This is a triage pass over a batch of candidate stories, not a verdict on one ticket already
in flight — once a story is written and specifically being judged for a sprint, that's
`ticket-evaluation`'s job, not a MoSCoW re-sort.

---

## Output block

```
Epic/Feature:      <name, one sentence>
Actor(s):          <stated, not invented>
Format:            User Story | Use Case — <one-line reason>
Sizing signal:      XS/S/M/L/XL — <split needed? y/n>

[User Story format, one block per story:]
Story N: As a <actor>, I want <action>, so that <benefit>.
  Acceptance Criteria:
    - <criterion>
    - <criterion>
  Explicitly not covered: <if a reader would otherwise assume it is>

[Use Case format:]
Title:                <goal>
Actors:               <who/what>
Preconditions:        <state before>
Main Success Scenario:
  1. <step>
Alternative Scenarios:
  - <deviation, named>
Post-conditions:      <state after>

Quality bar:          <pass, or named gaps>
Definition of Ready:   <pass, or named gaps>
Handoffs:             <specialist Architecture skill, if a story surfaced a load-bearing
                       decision> · `technical-cost-decision` if a story's acceptance criteria
                       implies a real recurring cost (a stated volume, a per-unit third-party
                       charge) · `ticket-evaluation` once these are real tickets and someone
                       needs a sprint-worthiness verdict
```

---

## Red flags — the decomposition isn't done

- A story's benefit reads like it would fit any story ("so that they have a better
  experience") — that's an invented benefit, not the stated one.
- "We'll write acceptance criteria later" — a story without them isn't ready; AC is what
  makes "done" checkable, not an optional follow-up.
- A use case chosen only because the story "has a lot of steps" — length isn't the signal;
  actor count and whether the alternate paths are worth documenting now is.
- One story quietly covering two actors ("As a user or admin, I want...") — split it.
- A story that would need a migration, a schema change, and a new integration all at once,
  written as a single sprint-sized item — it failed the splitting check; go back to it.
- The output redrafts or re-scopes the epic instead of decomposing what was stated —
  re-scoping is `design-scoping`'s job.

---

## Worked example (condensed)

Epic: *Playing-card-game app — gameplay.*
Actor: *player.*
Format: **User story** — single actor, no meaningfully distinct alternate paths worth
pre-documenting as a use case.

> Story: As a player, I want to start a new game and select the card game variation, so that
> I can play the game I'm in the mood for.
> Acceptance Criteria:
> - A list of available game variations is shown.
> - The selected variation's rules and mechanics are what's enforced for the rest of the game.

> Story: As a player, I want to view and interact with my hand during the game, so that I can
> make my moves.
> Acceptance Criteria:
> - The player's hand is shown with clear visuals and card information.
> - The player can select and play a card from their hand.
> - An invalid move is rejected with feedback, not silently ignored.

Multiplayer (invite friends, join public rooms, in-game chat, leaderboards) and customization
(deck/card-back appearance) are separate feature groups — each gets its own story set rather
than folding into gameplay's.

---

## Portability

Repo-agnostic. Writes no files; produces the story/use-case text and an optional Definition-
of-Ready gap list in chat. Copy the `user-story-decomposition/` directory into another repo's
`.claude/skills/` to use it there.
