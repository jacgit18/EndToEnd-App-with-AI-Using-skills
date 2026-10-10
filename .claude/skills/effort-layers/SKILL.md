---
name: effort-layers
description: Gate for effort estimates: the user's optimistic build number plus seven other kinds of work, with no total until each layer has a user number or "unknown". Use for "how long will this take", "quote this project", "why do my estimates run over". Not `ticket-evaluation` (go/no-go), `design-scoping` (unscoped system), `idea-to-first-test` (raw idea), `technical-cost-decision` (recurring bill), `capacity-estimation` (load).
---

# Effort layers

An estimate of "the build" covers only one of eight kinds of work. The other seven (meetings, scoping, setup, rework, change requests, surprises, running it afterwards) usually have no number until they show up as overrun. This skill puts them in front of the user **before** a figure is committed to.

Layer definitions, questions, answer format and log format: `layers.md`.

## The one hard rule

**Every figure in the output is the user's, arithmetic on the user's figures, or a ratio from the user's log under step 6.** Never "add 30%", "double it", "integration usually takes a third", and never a figure from layers.md's format examples (they show shape only, not defaults). A layer the user cannot size is `unknown`, and `unknown` is a complete answer. If the user says "you tell me", refuse and restate `unknown`.

Allowed: sums, and unit conversions of stated figures (4 h a week for 6 weeks is 24 h; show the working). Nothing else.

## Procedure

1. **Intake.** What is being estimated, unit (hours or days), whose time (client quote, employer, own), and where "done" ends. Ask only what is absent. For a client quote ask which layers the quote is meant to cover; by the diagram's convention layers 1, 2 and 8 sit outside the project, but that is the user's call. For own time all eight count.
2. **Optimistic number first.** Ask for the user's own figure for *the work* (build, design, tests, docs); a gut number is fine. Do not produce it. If the system is unscoped (no purpose, audience, scale), hand off to `design-scoping`; if the user declines, continue and label every total "for an unscoped system".
3. **One batch of layer questions** for the other seven layers (`layers.md`), each answered `likely / worst-case`, one number (taken as likely), `unknown`, or `n/a` with a reason. Challenge `n/a` once by asking only for the reason, never by proposing a figure. Stop and wait. Continue straight through (unanswered layers `unknown`) only if the user said there is no time; say up front that the table will be mostly `unknown` by design and the question block is the deliverable.
4. **Output contract**, in this order:
   - **Layer table:** layer, likely, worst-case, one line on what the number covers.
   - **Coverage line:** `N stated + M unknown + K n/a = 8`. *Stated* means a likely figure was given; the work counts once its figure is given.
   - **Totals**, project layers only (3 to 7, plus 1 and 2 if the user put them in the quote). **Fewer than 3 layers stated → no totals line**; print "lower bound only: <the user's own number>" and nothing that looks like a layered total. Otherwise: "likely, of the stated layers: X"; worst-case as "Y, stated for K of N layers". Never call a total the project total while any included layer is `unknown`.
   - **After the work** on its own line, per month, never summed into the totals.
   - **Biggest gap:** the one `unknown` layer to size first and the one question that would size it.
5. **Offer the log.** Ask once whether to append this estimate to `estimates-log.md` in the journal root named in the user's global CLAUDE.md (quote the path; it contains spaces). Writing is persistent, so wait for a yes.
6. **Close-out** ("here are the actuals", "how did that estimate do"). Find the entry by its id in the log, ask per-layer actuals, fill the open entry's Actual column and Status, show actual against likely. Only after **3 closed entries** may Claude show the log's per-layer ratios (actual divided by likely), labelled "from your log, N projects, sizes differ", next to the user's own figures, never instead of them. With no log or fewer entries, say so and offer to start one.

## Hand-offs

- A pasted ticket wanting a sprint verdict → `ticket-evaluation` first; offer this skill after, never both in one reply.
- "I have an idea, how long for an MVP" → `idea-to-first-test`, then `design-scoping`, then this.
- Hosting or any recurring bill in the after layer → `technical-cost-decision`.
- Sizing a single story → `user-story-decomposition`.
- Usage load, not people-time → `capacity-estimation`.
- A build needing a written spec and drift checks → `spec-drift-gate`.
- User cannot start at all → `entry-point-first`.

## Red flags — stop and rebuild from step 3

- A figure that is not the user's, derived from the user's, or from the log
- A totals line with fewer than 3 layers stated, or any total called the project total while a layer is `unknown`
- The per-month after layer summed into project hours
- Layers asked one at a time across many turns
- "Typically", "usually", "tends to" carrying a number
- Log ratios shown with fewer than 3 closed entries, or replacing the user's figure
- The optimistic number produced by Claude
- The log written or edited without a yes

## Portability

Needs no repo setup. Writes only to `estimates-log.md` in the journal root, only after a yes; with no journal root, offer the working folder instead.

Depends on: `ticket-evaluation`, `design-scoping`, `idea-to-first-test`, `technical-cost-decision`, `user-story-decomposition`, `capacity-estimation`, `spec-drift-gate`, `entry-point-first`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off. The load-bearing ones: no `design-scoping` and the system is unscoped → ask for purpose, audience and scale and give no layered total until they exist; no `ticket-evaluation` and the user wants a go/no-go → give the layer table only and say the verdict is outside this skill; no `technical-cost-decision` → leave the monthly after-layer figure to the user and do not price hosting.

## Routing boundaries (full)

The frontmatter `description` is trimmed for the listing budget; the full intent:

- Triggers include "how long will this take", "estimate this project", "quote this job", "why do my estimates always run over", "what am I forgetting in this estimate", and close-out phrases like "here are the actuals".
- Not a verdict on a ticket (`ticket-evaluation`), a design ask for a bare system name (`design-scoping`), an untested idea (`idea-to-first-test`), the monthly bill of a stack (`technical-cost-decision`), or load sizing (`capacity-estimation`).
