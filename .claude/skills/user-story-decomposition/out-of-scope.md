# User Story Decomposition — out-of-scope hand-offs (full)

Full reasoning behind the one-line summary in `SKILL.md`.

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
- **Drafting, dating, or publishing the actual writeup.** Once a story is closed, turning it
  into a LinkedIn post or talking points is `explaining-my-work` — its Evidence Block records
  when the work actually shipped, not when the draft was written — with `software-carpentier-
  brand` handling voice and career-wide honesty on top of that. This skill's reach stops at
  sizing stories so each is tellable on its own and flagging which ones are worth documenting;
  never at drafting the post, and never before the story is actually done.
