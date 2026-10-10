# effort-layers

Group: Business. A gate, not a procedure: it withholds the total until every layer has a user-given number or `unknown`.

## Where it sits

- **`ticket-evaluation`** judges whether a ticket is worth doing and forbids invented estimates. `effort-layers` is what you run when you need the estimate itself; it never invents one either.
- **`design-scoping`** comes first when the system is unscoped. `effort-layers` needs something concrete to size.
- **`technical-cost-decision`** takes over for the recurring hosting and service bill that sits in the "after" layer.
- **`capacity-estimation`** sizes load. This skill sizes people-time.
- **`spec-drift-gate`** guards a build once it starts; this runs before it.

## Status

Built 2026-10-10. Results, all light (one scenario each, scored by the author, not a separate scorer):

- **Static audit:** 2 blockers (one-way pointers; totals mixed per-month and per-project units, no bucket for `n/a`) and several hard-rule loopholes. All fixed in the same pass.
- **Isolation screen (booking-app quote, "build is 40 h"):** baseline with no skill failed as expected (quoted 75 to 80 h, invented every layer's hours and percentages, asked nothing). The same rules given as a plain prompt passed, and so did the skill. So the skill's added value over the bare rules is the log, close-out mode, hand-offs and routing, not the rule itself.
- **Totals re-screen (partial answers):** sums, worst-case labelling, per-month after layer and `n/a` bucket all came out as the contract says.
- **Interaction test:** no rule contradictions with `ticket-evaluation`; fixed the routing gaps it found (ticket-evaluation no longer says "sizes", both skills now point at each other, design-scoping points here).

**Unverified:** that layered totals land closer to actuals than a point estimate. No estimate-versus-actual history exists yet. The log in `layers.md` is how that gets tested; after about 3 closed entries run the outcome-grounded screen in `.claude/rules/adding-a-skill.md` step 3. The log is a third file in the journal root, beside `decisions-log.md` and `problems-log.md`.

## Ships in

Project-only until the owner chooses a plugin (candidate: `planning-skills`, beside `ticket-evaluation`).
