# Sunset framework

Reference for `SKILL.md`. Work these seven steps in order once the gate (items 4–12) is satisfied.

---

## 1. Confirm this is a retirement with consumers

Three misroutes to catch first:

- **No consumers beyond the owning team** (internal helper, an unreleased flag, a route only your own frontend calls and ships with) → this is a plain removal. `change-surface-audit` is enough; stop here and hand off.
- **A whole system is going away** (datastore, app, hosting) → `migration-cutover`.
- **The "sunset" is really a replacement rollout** (new version of a unit you deploy) → `deployment-strategy`.

If real consumers exist outside the team — other teams, customers, partners, or unknown callers — continue.

## 2. Choose: keep, freeze, sunset, or hard-remove

Decide from the driver (gate 4) and the evidence (gate 7), cheapest option that solves the driver first.

| Option | Fits when | Costs |
|---|---|---|
| **Keep** | The driver is "it's old" or "it's untidy" with no measured cost | Nothing changes; say so and stop. |
| **Freeze** | Maintenance cost is the driver and the surface is stable: no new features, bugs only for security, clearly labelled | Carrying the code indefinitely; a freeze with no end date is a slow sunset nobody owns. Give it a review date. |
| **Sunset with window** | A real driver, real consumers, and a path off | A multi-month program: notices, dashboards, stragglers. |
| **Hard remove** | A security or legal driver that does not allow a window, or evidence strong enough that the consumer set is closed and tiny | Whoever was not on the list finds out by breaking. Requires the evidence to be named and dated. |

A freeze is often the right answer when the driver is cost but the consumer count is unknown: it buys time to measure without breaking anyone. Name it as an option when the evidence is weak.

## 3. Set the window

The window is the **longest** of three floors:

1. **Notice floor** — the contract, SLA, or published policy minimum (gate 8). No floor stated means you pick one deliberately and write it down.
2. **Slowest consumer** — the longest realistic time for the slowest consumer class to ship a change (gate 6). A server integration might need weeks; a mobile or embedded client tied to app-store review or device updates needs a release cycle plus adoption time.
3. **Longest periodic cycle** — the evidence window must span it, and the sunset window must contain at least one full run of the longest periodic consumer *after* notice, or you will not see it fail until the date. A quarterly batch job needs a window over a quarter.

State which floor set the window in the output (`set by …`). If the three disagree wildly, say which consumer is driving the length; that is where to spend outreach effort, or where to offer a bridge.

## 4. Design the notice schedule

Dated steps, not "we'll announce it". Cover:

- **Day 0 announcement** — direct contact to every consumer in the list from gate 6, plus the public channel (changelog, docs banner, status page) for the unknown ones.
- **Machine-readable signal** — response headers and log warnings from day 0 (see `enforcement-and-notice.md`).
- **Reminders** at fixed fractions of the window (for example the midpoint, one month out, one week out), each worded with the exact date.
- **A "no response" path** — what you do about a consumer that never acknowledges. Silence is not consent; it feeds the enforcement ladder.

Each notice names: what is going, the date, what to move to, where the migration guide is, and who to ask. A notice without a migration path or an owner contact is a threat, not a notice.

## 5. Choose the enforcement ladder

From `enforcement-and-notice.md`: warn → brownout → read-only (where it makes sense) → remove. Choose the rungs and the dates. Rules of thumb:

- Brownouts are the cheapest way to find consumers the evidence missed. Announce the times in advance, and make each longer than the last.
- Skip a rung only for a stated reason: a closed consumer set, strong evidence, or a driver that forbids delay.
- Read-only is a rung only when the target holds state consumers might still need to read.
- The final rung is a dated event with an owner, not "after traffic drops".

## 6. Set the straggler policy

Decide before the first notice goes out, because it is much harder after:

- **Who** may grant an extension (a named role, not "whoever is asked").
- **How many** — a cap per consumer. One is a strong default.
- **What a late consumer is offered**: help with migration, a shim, a paid extension, or nothing. Name which.
- **What happens at the cap**: the date binds. State who communicates it.

An extension policy with no cap means the date never binds.

## 7. Define exit criteria and record

Final removal is authorised by a **measured** condition, not by the calendar alone: zero requests for N consecutive days after the last brownout, no open extensions, data disposition complete. The calendar date is the *earliest* removal, not the guarantee.

Record the plan in the deprecation record under `## Sunset plan` (see `SKILL.md` Output). Update the record's `Status` as consumers migrate. Stop there; implementation is a separate step.
