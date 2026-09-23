# Delegate by decision density, not by complexity

A recall card for interviews and live conversations. Skim it, don't read it out.

## The one question

> **How many choices in this task are load-bearing, and how many are reversible?**

Not "is it hard to write" (lines of code, number of fields, CRUD-shaped). Ask how many meaningfully different choices exist, and how much later work depends on which one gets picked.

- A field name is reversible, so the stakes are low.
- An FK structure that other tables build on is load-bearing, so the stakes are high.

## The delegation ladder

| Decision density | Test | AI's role |
|---|---|---|
| **Low** | One defensible answer. Shape is dictated by the data or by a stated rule. | **Owns it**: decision and implementation. |
| **Mid** | A real choice exists, but it's swappable with contained effort. | **Drafts, I review.** |
| **High** | Load-bearing, or a proxy for a business decision not yet made. | **I design, AI implements.** |

- **Low examples:** add a column, standard FK, boilerplate CRUD, validation scaffolding, a direct translation of a stated rule.
- **High examples:**
  - normalize vs. denormalize for read/write patterns
  - a many-to-many that must serve query patterns not yet written
  - nullable vs. required where the answer depends on uncaptured business rules
  - state machines and eventual consistency
  - audit trails and PII
  - the "10-minute" schema that is really "how does the business define X?"

## Two modes for using AI inside the decision

| Mode | When | Direction |
|---|---|---|
| **1. AI enumerates, I decide** | The task is open. I don't know all the paths, and the choice is load-bearing. | AI does reconnaissance: shapes, edge cases, tradeoffs. **Judgment stays mine.** |
| **2. I reason, AI stress-tests** | A real tradeoff, and I can reason it through. | I decide first. AI's job is to **break it**: poke holes, find missed edge cases. |

The distinction is whether AI widens what I'm looking at before I choose (1), or attacks a choice I've already made (2).

## The tripwire

Density often shows up mid-task. A second fork appears three steps in, such as "does this field need soft-delete for compliance?"

**Before delegating, name what discovery kicks the decision back to me.** The real risk isn't complexity. It's AI quietly picking a reasonable-sounding default on an ambiguous, load-bearing decision and moving on.

Example tripwires:
- The task touches a table other tables reference.
- The task needs a nullable/required choice the rule doesn't state.
- The task implies retention, audit or PII handling.
- The task needs a status or lifecycle the spec doesn't define.
- The same field would mean two different things to two consumers.

## Questions to say out loud (interview / live conversation)

1. What would it cost to undo this in six months? (A rename or a migration?)
2. Is there one defensible answer, or am I choosing a business definition?
3. What future query or workflow does this need to support that isn't specified yet?
4. Do I need to see the whole option space first (mode 1), or have I already chosen (mode 2)?
5. What discovery mid-task should stop the work and come back to me?
6. If AI picked a default here without telling me, would I find out before it mattered?

## 20-second interview version

"I triage by decision density, not complexity. If a task has one defensible answer, I delegate it fully. If it has real tradeoffs, I either have AI enumerate the options so I can pick, or I decide first and have AI attack it. Load-bearing choices, like keys other tables depend on or business definitions, stay mine. And I set a tripwire up front, so anything ambiguous and load-bearing that turns up mid-task comes back to me instead of getting a silent default."
