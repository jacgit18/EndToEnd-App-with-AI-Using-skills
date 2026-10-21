# Design Scoping — a messy brief for a feature in an existing app

Read when the ask is a **feature inside a codebase that already exists**, the person briefing you is its owner and user, and the brief is narrative or dictated ("here's how I shop, here's what annoys me") rather than a requirements list. The five-item gate in `SKILL.md` is built for new systems with a team and scale targets; here items 4 and 5 (RPS, availability, error budget) are noise, and the user cannot state requirements before seeing something concrete. Use **propose-and-react** instead of withholding the design.

Worked once, 2026-10-19: splitting grocery costs in iron-log (BJ's card shared three ways). The user called the requirements gathering very successful. This is the loop that produced it.

## The loop

1. **Restate with their own numbers, and do the math.** Put their figures in a small table. A mismatch between what they believe and what the arithmetic says (they expected $400 to $450 a month; their share was about $250 to $320) is the cheapest requirement you will ever find, and it proves you understood.
2. **Separate the invariant from the incidental.** Their situation has details that are theirs alone (a credit card repaid from a relative's account) and a core that generalises (a purchase divided among N people, one of whom is you). Name the core, say what the model deliberately ignores, and keep accounts, cards and banks out of it.
3. **Read the code before recommending.** Open the types and the screen the feature lands on. Reuse what exists (here, a per-pack price array already in the data) and name the real costs you find (a server table that held only a name, so a store-level setting needs a schema change). Label these `read-only` until run.
4. **Recommend one integration shape and say why the other lost.** "Inside the existing list, not a separate tab: a second tab means typing prices twice."
5. **Phase it, and re-phase out loud.** V1, V2, V3 with what is deferred. When a later answer breaks an earlier assumption (headcount alone cannot give exact per-person amounts, so named people moved from V3 into V1), say so and why.
6. **One question at the end, at most.** Everything else is a stated assumption (the `ambiguity-gate` contract still applies). Do not ask for numbers the user cannot know yet.
7. **Show an interactive preview of their own scenario with live numbers**, before any code. Their reactions are the requirements: the multi-pack meat case, the settle-up card, and "Me +2" instead of "÷3" all came from reacting to a mock, not from a questionnaire. Write labels in their words.
8. **After each reaction, answer the edge case, then ask what it conflicts with.** Existing behaviour the new feature changes (here, the spend chart's headline number and the average) must be named and resolved explicitly, not discovered in review.
9. **Apply the project's standing rules without being asked**: audience (admin-only until the owner says otherwise), feature flag registry, which files overlap open PRs, data-format and backup round-trip. State them as constraints, not options.
10. **Keep the handoff current.** If the design moves after a handoff file is written, update the file. In this session the handoff was written one turn before named people and the "Me +N" wording were agreed.

## Pitfalls seen

- Dictated messages arrive duplicated or with sound-alike words ("review" for "preview"). State the reading you took in one line instead of asking.
- A preview with made-up prices invites debate about the prices. Use the owner's real figures where they gave them.
- Rounding and money: integer cents, the payer absorbs the odd cent, totals must add to the card bill. Settle this in the preview, not in the PR.
- Do not let the preview stand in for the plan: the feature still needs a `FEATURE-PLAN.md` row (tier, cost, debt, shared files) and the project's docs updated in the same PR.

## Exit

The user says they like the preview, the open questions are listed with who answers each, and the next step is concrete (a branch off `main`, the files to read, the tests to write first). Then hand off to `spec-drift-gate` or `incremental-build-pacing` for the build.

Then run `feature-brief` to close the remaining questions and write the brief before the build.
