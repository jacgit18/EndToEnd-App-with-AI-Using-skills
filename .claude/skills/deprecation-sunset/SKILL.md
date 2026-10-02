---
name: deprecation-sunset
description: Gated decision for running the retirement of a feature, endpoint, API version or module you own that has consumers: keep/freeze/sunset, usage evidence, notice, enforcement ladder (warn, brownout, remove), stragglers. Triggers: "we want to sunset X", "how do we deprecate this API", "how long should the deprecation window be". Not a bare "delete X, what do I check" — `change-surface-audit` first. Not moving a system — `migration-cutover`.
---

# Deprecation & Sunset

Take a thing you own that other people or systems depend on — an endpoint, an API version, a feature, a shared module, a client SDK — and decide whether and how it goes away: keep it, freeze it, or sunset it, on what dated schedule, with what evidence that the schedule is safe, how consumers are told, what actually happens on the date, and who decides when someone is still there. The skill makes the user name the driver, the replacement, the consumer reach, and the enforcement stance before any timeline is drawn, then writes a sunset plan into the deprecation record.

This is the *program* around a removal. The one-time question "what breaks if I delete this" is `change-surface-audit`; this skill takes its consumer audit as an input and owns everything that plays out over weeks or months after the decision.

## When to use

- The user wants to **retire something with consumers**: "we want to sunset v1 of the API", "deprecate the legacy export", "drop support for the old SDK".
- The user asks about **timeline or notice**: "how long should the window be", "how do we tell customers", "what do we put in the deprecation header".
- The user asks what to do about **stragglers**: "three partners still call it", "the deadline passed and traffic isn't zero".
- The user proposes a sunset plan and wants it pressure-tested ("we'll announce it and turn it off in 30 days").

## Out of scope — hand these off

- **What depends on one proposed removal, and whether it is breaking** — the consumer audit, hidden dependents, expand-contract, the deprecation-record skeleton → `change-surface-audit`. A bare "delete this endpoint, nobody uses it, what do I check first" goes there **first**, even when the endpoint is public: its audit establishes whether consumers exist. Come here only once that audit finds consumers outside the owning team, or the user asks how to run the retirement (window, notice, brownouts). If the thing has no consumers beyond the team itself, that skill alone is enough; do not run a sunset program.
- **Moving a whole system to a replacement** — datastore, application, hosting → `migration-cutover`. Retiring one capability inside a system that stays is here; the system itself going away wholesale is there.
- **The API's versioning scheme** — URI vs header, how new versions are numbered → `api-interface-style`. This skill decides when an old version dies, not how versions are named.
- **How the replacement is released** — canary, blue-green, flags → `deployment-strategy`.
- **Whether the retirement is worth the ticket** — sizing and go/no-go against other work → `ticket-evaluation`.
- **Implementation** — the warning middleware, the brownout switch, the removal PR. The skill stops at the plan.
- **A vague "clean this up"** with no named target → `ambiguity-gate`.

---

## The gate

Before recommending any timeline, enforcement step, or window length, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **The concrete target** — the route, version, flag, module, or package, and where it is defined.
2. **What references it in code and config** — internal callers, tests, docs, SDKs, flags.
3. **Existing usage telemetry** — access logs, API-key or tenant attribution, metrics, and how far back they go.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not plan without them. If any is missing, name it and stop:

4. **The driver** — what is actually forcing retirement: a security or compliance problem, a maintenance cost with a number, a replacement that makes it redundant, a dependency or licence ending (with the date). "It's old" or "it's messy" is a reason to consider *freeze* instead, not a driver for sunset.
5. **The replacement or exit path** — what consumers move to, or "none: the capability ends". A sunset with no migration path is a product decision to remove a capability; say so explicitly.
6. **Consumer reach** — other internal teams, known external (partners, named customers), or unknown public (another team's code counts as a consumer; only the owning team's own callers do not — if that is the whole list, this is `change-surface-audit`'s plain removal); and for each, how you can contact them and how slowly they ship (a mobile client with a slow release cycle pins a window far longer than a server integration).
7. **Usage evidence and window** — what source, what time window. The window must cover the longest periodic consumer (a monthly report, a quarterly batch, an annual filing). "Nobody uses it" is not evidence.
8. **Minimum notice obligation** — contract, SLA, or published policy that sets a floor on notice. If none exists, say so.
9. **Enforcement stance** — what actually happens on the date: hard removal, brownouts first, redirect, read-only freeze, or "whatever the policy says."
10. **Straggler authority** — who may extend the date, how many times, and what a late consumer is told.
11. **Data disposition** — if the target holds consumer data: export window, archive, or delete, and who is told. State "none" if it holds none.
12. **Owner and capacity** — who sends the notices, watches the traffic, and flips the switch.

"We want to turn off v1 next month, give me the plan" with items 4–12 absent is not valid input.

**A deadline does not open the gate.** "Legal says it has to be gone by the quarter", "just give me the timeline" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–12 in one sentence each, because a sunset with no usage evidence and no straggler policy turns into an outage for whoever you did not know about.

---

## Challenge a proposed approach

If the user opens with the plan chosen, put their reasoning under the gate, then test the specific claim against `enforcement-and-notice.md`:

- **"we'll email everyone and turn it off in 30 days"** — who is "everyone", and is that the list from item 6 or the list you happen to have? Does 30 days clear the notice floor (item 8) and the slowest consumer's release cycle? What is the check that traffic is actually falling during the window?
- **"traffic is zero, just delete it"** — zero over what window and from what source (item 7)? Does the window span the longest periodic consumer? Is the source blind to some callers (a partner behind a shared key, a batch job outside the logs)?
- **"add a deprecation header, that's the notice"** — headers reach clients that read them, which is a minority. What reaches the humans who own the integration?
- **"we'll just extend whenever someone asks"** — an unbounded extension policy means the date never binds. Who decides, how many extensions, and what does the second ask cost the consumer?
- **"turn it off on the date, no warning shots"** — brownouts exist to surface consumers the evidence missed. Skipping them is only reasonable when the usage evidence is strong and the consumer set is closed.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `sunset-framework.md` in order once the gate is satisfied. In short: confirm this is a retirement with consumers, not a no-consumer removal or a system move → choose among keep / freeze / sunset-with-window / hard-remove from driver and evidence → set the window from the longest of the notice floor, the slowest consumer, and the longest periodic cycle → design the notice schedule and channels → choose the enforcement ladder → set the straggler policy → define the exit criteria that authorise final removal → record.

Reference files:

- `sunset-framework.md` — the 7-step process, worked once the gate is satisfied, including how to choose between keep, freeze, sunset, and hard-remove.
- `enforcement-and-notice.md` — read when challenging a proposed plan or choosing notice channels and enforcement rungs: the evidence-strength ladder, notice channels and what each actually reaches, the Deprecation and Sunset headers, the enforcement ladder (warn, brownout, read-only, remove), and straggler handling.

---

## Output

**1. In chat, a recommendation block:**

```
Target:              <the concrete thing being retired>
Driver:              <the dated or measured reason from gate item 4>
Choice:              <keep | freeze | sunset with window | hard remove> — <why, from driver + evidence>
Exit path:           <replacement, or "capability ends">
Consumer reach:      <internal / known external / unknown public> — <how each is contacted>
Usage evidence:      <source, window, what it can and cannot see>
Window:              <start → end> — set by <notice floor | slowest consumer | longest periodic cycle>
Notice schedule:     <dated steps and channels>
Enforcement:         <warn → brownout → read-only → remove, with dates>
Straggler policy:    <who decides, max extensions, what is offered>
Exit criteria:       <the measured condition that authorises final removal>
Data disposition:    <export / archive / delete / none>
Tradeoffs accepted:  <2–4 concrete costs: carrying the code longer, a partner annoyed, a brownout incident>
Not chosen because:  <one line per rejected option>
```

**2. On approval**, add a `## Sunset plan` section to `docs/engineering/deprecations/<slug>.md` — the record `change-surface-audit` creates. If that record does not exist yet, run that skill's consumer audit first or create the record with the same fields (`Removing`, `Consumer audit`, `Deprecation window`, `Notice mechanism`, `Point of no return`, `Status`) and add the plan beneath. The plan holds the recommendation block above plus a `Revisit when` line with a concrete trigger: "traffic on the target has not fallen 50% by the midpoint", "a named consumer asks for a second extension", "the notice floor changes".

Then stop. The warning middleware, the brownout switch, and the removal PR are separate, explicitly started steps.

---

## Escape hatch

If the user has genuinely worked this — the driver dated, evidence with a stated window and source, the slowest consumer named, an enforcement ladder and a straggler rule — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "We're sunsetting v1 of our public API. v2 has been live a year and v1 costs us a second deploy pipeline. Access logs for the last 13 months show 11 API keys still calling v1, 3 of them above 1k requests a day; the rest are a few calls a month, probably forgotten cron jobs. All keys have an owner email. Our terms promise 90 days' notice for breaking changes. Nobody holds customer data in v1-only tables. I want warnings first, then brownouts, then off. I'll sign off on one 30-day extension per key, no more. I own it, with one engineer for the traffic dashboards."

Gate satisfied. Choice: sunset with window. Window: 90 days (set by the notice floor; the 13-month log window covers the annual-cycle risk). Notice: direct email to the 11 key owners at day 0 and day 45, changelog entry at day 0, `Deprecation` and `Sunset` response headers from day 0. Enforcement: warn from day 0, a 1-hour brownout per week from day 60 with a pre-announced time, a 24-hour brownout at day 80, remove at day 90. Stragglers: one 30-day extension per key, requested in writing, second ask escalates to the owner. Exit criteria: zero v1 requests for 7 consecutive days after the last brownout. Tradeoffs: carrying the second pipeline three more months, a brownout may page a partner on-call.

> "We want to turn off the legacy export next month, can you write the plan."

Gate not satisfied — item 4 (no driver), item 6 (who uses it?), item 7 (no usage evidence), item 8 (any contractual notice?), item 9 (what happens on the date?). Response: name what is missing, say that a sunset with no usage evidence and no enforcement stance is an outage for whoever was not on the list, and ask for the driver, the consumer list and how it was built, the log window, any notice obligation, and what turning it off should look like. Do not draw a timeline.

> "We're deleting the `/internal/debug-dump` route. Only our own admin page calls it and it ships with the same repo." / "Delete the unused `legacy_flag` column."

Not this skill — no consumers beyond the owning team, so there is nothing to notify, brown out, or extend. That is `change-surface-audit` (hidden dependents, mechanical cleanup). Do not run a sunset program.

> "We're moving off MySQL 5.7 and retiring the old billing app."

Not this skill — a whole datastore and application are moving to replacements → `migration-cutover`. A sunset plan can still apply later to one capability inside the system that stays.

> "Should our API use URI versioning or a header?"

Not this skill — how versions are named → `api-interface-style`. Come back here when the question is when v1 dies.

---

## Portability

Repo-agnostic. Writes a `## Sunset plan` section into `docs/engineering/deprecations/<slug>.md`, the record `change-surface-audit` owns. Copy the `deprecation-sunset/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.

## Routing boundaries (full)

- Use when someone says "we want to sunset X", "deprecate this API", "retire this feature", "end-of-life the old SDK", "how long should the deprecation window be", "how do we notify customers about removing this", "partners are still calling the old version", "should we brown out the old endpoint", or proposes a sunset plan and wants it checked.
- Not for a removal whose only question is what else it breaks ("what do I check before I delete this endpoint"), or one with no consumers beyond the owning team — that is `change-surface-audit`, which runs first and whose deprecation record this skill extends.
- Not for retiring a datastore, application, or hosting environment wholesale — that is `migration-cutover`.
- Not for deciding how API versions are named or numbered — that is `api-interface-style`.
