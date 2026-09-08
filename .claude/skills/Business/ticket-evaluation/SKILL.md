---
name: ticket-evaluation
description: Use when a work ticket is shared for analysis, prioritization, sizing, or a go/no-go read — a Jira/Linear/Asana issue, a GitHub issue, or a pasted-in feature description. Triggers include "should we pull this into the sprint," "is this worth doing," "evaluate this ticket," "how would you prioritize this," "what's the risk on this one," backlog grooming, and comparing several tickets against each other. Also use when someone asks for a verdict on a ticket immediately and does not want to answer questions first.
---

# Ticket Evaluation

A ticket is a request written by someone who already knows the context. The reader does not. The gap between those two is where every bad prioritization call comes from — and a ten-row rubric makes that gap worse, because ten empty rows create pressure to produce ten assessments whether or not ten assessments are available.

This skill separates **what the ticket says** from **what the ticket is missing** from **what can actually be judged**, and keeps the verdict at the bottom where it cannot outrun its own caveats.

## Out of scope

- **Rewriting the ticket.** Naming a dimension as weak is evaluation. Redrafting the acceptance criteria, splitting the scope, or designing the feature is a different job — offer it after the recommendation, only if asked.
- **A "ticket" that is just a system name** — "Build the notifications system", "Set up billing" — with no acceptance criteria, requirements, or scale. That is not a sizeable unit of work; it is an under-specified design ask → `design-scoping`. Come back here for the sprint verdict once it has been scoped.

- **A "ticket" that is a bare feature name with no description, acceptance criteria, or actor**
  — "Add notification preferences" — isn't a system to scope but also isn't yet a story to
  judge → `user-story-decomposition`. Come back here for the sprint verdict once it has an
  actor, an action, and acceptance criteria.
- **Implementation.** This skill ends at proceed / defer / needs more info / reconsider.

---

## The one hard rule

**"Insufficient info" is a real assessment. It is the correct output for a dimension the ticket does not address, and it is never upgraded by inference.**

The rubric has ten dimensions because ten things can matter — not because ten things are knowable from any given ticket. A typical ticket supports three or four. The rest are gaps, and naming them *is* the value: the gap list is what turns a ticket into a decision.

**No exceptions:**
- Not from what tickets like this usually involve. That assesses the archetype, not this ticket.
- Not from a plausible reading of the description. Plausible is not stated.
- Not with a hedge attached. "Likely strong," "probably moderate," and "assuming typical usage" are guesses wearing an assessment's clothes. A caveat does not convert a guess into a finding.
- **No invented numbers.** Not an estimate in days, not a multiplier, not a percentage, not a row count, not an ARR figure. An invented estimate is the number that becomes the sprint commitment.

If a dimension cannot be assessed, write `insufficient info` and the one question that would resolve it. That is a complete, correct answer.

---

## The output contract

Your response has these parts, **in this order**. The ordering is the skill.

1. **Intake** — what the ticket actually states
2. **Gap questions** — only the ones the ticket leaves open
3. **Scorecard** — all ten dimensions
4. **Open questions** — what is still unresolved
5. **Recommendation** — last, with one or two named drivers

**No verdict, lean, or "my read is" may appear before part 5.** Not as a headline, not as a TL;DR, not as an executive summary for the busy reader. A recommendation placed above the scorecard is the thing the reader carries into planning; the "insufficient info" rows underneath it do not make the trip. If the recommendation is worth qualifying, it goes below the qualifications.

---

## Part 1 — Intake

Pull out only what is written: title, description, acceptance criteria, priority and labels, linked epics or dependencies, requester, deadline, sprint.

Mark each as **stated** or **absent**. Absent is information — an unassigned sprint, no linked epic, and a priority set by someone outside engineering are all facts about the ticket, and they matter later.

Do not infer here. Do not begin evaluating here.

---

## Part 2 — Gap questions

Check the ticket against the ten dimensions. **Ask only about dimensions the ticket does not already answer.**

Do not run the full checklist as boilerplate. Asking someone what success looks like when the ticket states the metric in line two reads as not having read the ticket, and it trains them to skip your questions next time.

Common gaps:

| Gap | Ask |
|---|---|
| No success metric | What does "done and working" look like — what metric should move? |
| No scale or volume | How many users, records, or systems does this touch? |
| No cost of inaction | What happens if this doesn't get done this quarter? |
| No resourcing or timeline | Who would build it, and by when? |

**"Not sure" is a valid answer.** Record it as an open question in part 4. Do not fill the slot with a score to make the table look complete.

### When the user says there's no time for questions

This is the pressure case, and it is the one that produces bad evaluations. Sprint planning in ten minutes, "just give me the read," "no questions, I need the assessment now."

**Ask anyway — but change the form, not the substance.** Deliver the gap list as a short, answerable block they can resolve in the room, then produce the scorecard with those dimensions marked `insufficient info`. Do not silently substitute inference for the answers.

A ticket with four unknown dimensions is a real finding, and it is more useful in a planning meeting than ten confident-sounding rows, because it tells the room exactly what to ask the requester who is sitting right there. Time pressure is a reason to make the questions shorter. It is never a reason to guess and present the guess as an assessment.

**Say up front that this is what you are doing.** One line, before part 1: the questions go out unanswered, so the scorecard will be mostly `insufficient info` by design, and the gap list is the deliverable. A reader who expects an evaluation and receives a mostly-blank table will read it as the evaluation having failed, when it is the evaluation having worked.

**Do not write the same questions twice.** Part 2 and part 4 overlap heavily in this mode — every unasked question is by definition still open. Part 2 is the room-ready block, in the order you would actually say them out loud. Part 4 refers back to those by number and adds only what part 2 did not contain: the ranking by decision impact, and any question the evaluation itself raised.

---

## Part 3 — Scorecard

Every dimension gets a row. Assess qualitatively: **strong / adequate / weak / insufficient info**.

Qualitative is the default because most tickets lack the data for a defensible 1–5, and a number implies a precision the ticket does not support. Score numerically **only** when the user asks — typically to rank several tickets against each other — and say the scale you are using.

One line of justification per row, tied to something actually known from the ticket or from the answers to part 2. A justification that would read identically for a different ticket is not a justification.

### `weak` or `insufficient info`? Ask where the answer lives

Both describe an absence. They are not interchangeable, and the test is **where the missing fact would be found if someone went looking**:

- **The fact lives outside the ticket** — in usage data, in the codebase, in an engineer's head, in a customer's contract. The ticket not carrying it means you don't know. → **`insufficient info`**, plus the question that resolves it.
- **The ticket is itself the authoritative place for that fact** — and it is absent. Nothing is being withheld; the absence *is* the finding. → **`weak`**, and say precisely what is weak.

Strategic Alignment is the usual case: an unlinked epic, an unassigned sprint, and a High set by a reporter outside engineering are not missing information about the roadmap. They are the ticket asserting no roadmap linkage. Score that `weak` — and scope the claim to what is actually weak (the stated linkage), not to the strategic fit, which nobody has evaluated.

Scale, Feasibility, and Consistency almost always go the other way: usage volumes, build effort, and whether an export pattern already exists elsewhere all live outside the ticket.

### Partially-knowable dimensions

A dimension can have real evidence and no magnitude. Recurring customer requests with a named workaround is genuine Impact evidence; without an account, a revenue figure, or a volume it does not support "large."

**Assess the part that is known and name the part that isn't.** "Real and recurring; magnitude unstated" is a complete assessment. Rounding it up to `strong` imports a magnitude the ticket never gave, and dropping it to `insufficient info` discards evidence that is actually there. Take a second line where a row needs one — the one-line norm is for brevity, not a cap that forces false precision.

| Dimension | What it asks |
|---|---|
| **KPI / Success Metric** | What metric does this move, and how would success be measured? |
| **Scale** | How many users, records, systems, or transactions does this touch? One-off or systemic? |
| **Feasibility** | Given current tools, team skills, and time, can this be built as scoped? |
| **Impact** | How much does it change if done — and what does it cost to leave undone? |
| **Sustainability / Maintainability** | Does this reduce or add long-term maintenance burden? |
| **Efficiency** | Is the effort proportionate to the benefit, against alternatives? |
| **Consistency** | Does this follow existing patterns, or add a one-off exception that fragments the system? |
| **Risk** | What could go wrong, how large is the blast radius, is it reversible? |
| **Adoption** | Will the people it's for actually use it? What's the friction? |
| **Strategic Alignment** | Does this ladder up to a stated priority, or is it disconnected from the roadmap? |

Close the scorecard with the count: **N of 10 assessable, M insufficient info.** That count is what part 5 has to answer to.

---

## Part 4 — Open questions

Everything still unresolved after part 2 — unasked because there was no time, asked and answered "not sure," or newly raised by the evaluation itself.

Order them by which would most change the recommendation. If one question would flip the call, say which call it flips.

---

## Part 5 — Recommendation

One of: **proceed / defer / needs more info / reconsider.** Stated plainly, in a sentence.

Then name **the one or two dimensions actually driving it** — not a recap of the other eight. If three or more dimensions are genuinely co-driving, the honest statement is that the ticket is contested, and that is worth saying instead of ranking them artificially.

**`needs more info` is the correct call when the dimensions that would decide it are the ones marked insufficient info.** Reaching for proceed or defer anyway, on the strength of the dimensions that happened to be knowable, is how a ticket gets sized on its most legible attribute rather than its most important one.

**When several blocked rows trace to one unknown, the unknown is the driver — not the rows.** Listing Feasibility and Efficiency as two drivers overstates their independence if a single unanswered question is what blocked both. Name the question, then say which dimensions it is holding.

Where a recommendation depends on an unknown, state the branch: "proceed if the export is page-scoped; needs more info if it means the full result set."

---

## Red flags — stop and rebuild from part 1

- A verdict, lean, or summary appears before the scorecard
- Ten rows assessed on a ticket that stated four things
- "Likely," "probably," "typically," or "assuming" load-bearing in a justification
- An *estimate* in the output that appears nowhere in the ticket or the answers — days, percentages, multipliers, row counts. (Counting your own rows — "3 of 10 assessable" — is not an estimate.)
- Zero questions asked because the user said there was no time
- A justification that would read identically for a different ticket
- The output redrafts the acceptance criteria or splits the scope
- The recommendation names five drivers

**All of these mean: the rubric got filled instead of applied. Go back to what the ticket actually says.**
