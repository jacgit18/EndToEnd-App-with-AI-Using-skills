# Parked skill candidates

Ideas evaluated and deliberately not built yet. Each has a trigger; re-check when it fires.
(`SKILL-BACKLOG.md` is absent in this checkout, so parked items live here.)

## change-order-gate (freelancer scope changes)

- **Job:** a client asks for something mid-engagement → in scope / out of scope / ambiguous,
  repricing as a range, and client-facing wording. Gate: baseline scope, delivered work and
  rate must be stated first.
- **Real gap vs. the catalog:** only the change-order rule. Initial scoping overlaps
  `user-story-decomposition`, `ticket-evaluation`, `design-scoping`.
- **Why parked (2026-10-03):** no owned client engagements yet; a project-history search
  returned 2 thin cases and 0 with a recorded outcome. Testing on invented cases would be
  circular.
- **Build when:** the owner has a paid, owned engagement, or 3 real change-request histories
  with recorded outcomes (original ask, the request, what was done, what it cost).
- **Test plan when built:** outcome-grounded isolation (see `adding-a-skill.md` step 3):
  three arms (no skill, plain prompt with same rules, skill), outcomes withheld, separate scorer.
- **Possible lead:** Capital One 2025 PTP workflow, requirements were unsettled; recall one
  real change in the 7-field format.
