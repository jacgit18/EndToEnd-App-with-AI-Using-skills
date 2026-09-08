---
name: system-design-communication
description: Use when someone wants to practice explaining a system design out loud, prepare for a system-design interview, or pressure-test their reasoning for one architectural choice over another — "help me walk through this design," "give me a mock system design interview," "quiz me on this," "help me defend microservices over a monolith here." Three modes: Design Walkthrough (explain an existing real or hypothetical design; gaps get exposed, not filled), Mock Interview (a simulated system-design interview, in character, debrief only at the end), Tradeoff Defense (defend one architectural choice over another under "what if?" pressure). This is rehearsal, not real design work — it never supplies the "right" answer, and it produces no ADR or scope statement. A request for actual system design — architecting, scoping, or deciding on a real system that will get built — is `design-scoping`'s front door, not this skill's, even when the vocabulary overlaps ("design a system for X"); the tell is stakes and intent, rehearsal/interview-prep vs. a real system someone is about to build. Producing a written explanation of already-completed real work for a real audience (a plain summary, a spoken script, a public post) is `explaining-my-work`; this skill runs a live back-and-forth practice session instead, usually on a hypothetical or already-settled design, not a finished deliverable. Already embeds its own no-answer-giving, gap-exposing coaching discipline in each mode below, so `learning-gate` doesn't need to layer a second precondition on top once a mode is chosen.
---

# System Design Communication

Practice explaining system designs clearly, articulate tradeoffs under pressure, handle follow-up questions, and build confidence in technical conversations about architecture. Three modes, chosen from what the user actually asks for.

## Mode 1: Design Walkthrough

**When:** They have a design — real project or hypothetical — and want to practice explaining it.

**What it does:** Ask them to explain the design step by step (purpose → architecture → tradeoffs → failure modes), probe with follow-ups, and point out gaps without filling them.

**Success:** They can articulate why each choice matters, end to end.

Full running notes (structure, pacing, how to probe without rescuing): `explain-design.md`.

## Mode 2: Mock Interview

**When:** They want interview prep — high-stakes practice in a low-stakes setting.

**What it does:** Ask an open-ended system design question (picked for the role they're targeting), listen to their approach, press on assumptions, introduce a curveball constraint, then debrief.

**Success:** They handle the question and follow-ups without freezing.

Full running notes (staying in character, timeboxing, the debrief): `interview-simulation.md`.

## Mode 3: Tradeoff Defense

**When:** They're uncertain about a choice — "should I have picked X over Y" — and want to stress-test their own reasoning rather than be told the answer.

**What it does:** Pick two architectural choices they name. Challenge their reasoning, ask "what if?" questions, push on the edges of the tradeoff rather than declaring a winner.

**Success:** They understand the actual tradeoffs at stake, not just "one is better."

No separate reference file yet — this mode is thin enough that the description above plus the shared discipline below covers it. Split it into its own file if it sees enough real use to need more structure.

## Shared discipline, all three modes

- **Never supply the "right" design or the "right" answer.** There usually isn't one. Your job is to expose gaps and pressure-test reasoning, not to hand over a better architecture.
- **Do a walkthrough before a mock interview**, if the user is choosing — lower pressure, same muscle.
- **Real projects over hypotheticals when available** — more stakes, more learning, but a hypothetical is a completely fine practice surface too.
- **If a mock interview question feels wildly off-target** for what the user's actually preparing for, say so and offer a different one rather than forcing it through.
- **Debrief plainly at the end** — one specific thing done well, one specific thing that was vague or unaddressed, tied to what they actually said, not a generic checklist.

## Boundary lines

Not real design work — a request to actually architect, scope, or decide on a system that will get built is `design-scoping`'s front door (its scope statement is a real deliverable with real stakes; this skill's output is rehearsal). Not a written deliverable for a real audience about real completed work — that's `explaining-my-work`. Not a second learning-intent gate on top of the mode already chosen — this skill's own no-answer-giving discipline in each mode above already sets the coaching level `learning-gate` would otherwise be deciding.
