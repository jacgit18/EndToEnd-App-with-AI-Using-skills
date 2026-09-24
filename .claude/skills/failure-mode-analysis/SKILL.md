---
name: failure-mode-analysis
description: Structured FMEA / pre-mortem over a design or service graph: enumerates failure modes across nine categories, scores and ranks them, emits a prioritized register plus watchlist. Use for "do an FMEA", "run a pre-mortem", "what could go wrong with this design". Not for choosing one overload protection (`resilience-strategy`) or a failure happening now (`problem-solving-gates`).
---

# Failure Mode Analysis

Take a design, a workflow, or a service graph and systematically find the ways it can
break before it breaks in production. The procedure walks every component and every
interaction, asks the same nine questions of each ("how does this fail *functionally* /
*for availability* / *under load* / ..."), writes each failure mode down as a concrete
cause → manifestation → impact chain, scores it for severity, how often it will happen, and
how likely you are to catch it in time, ranks the list, and hands back a prioritized
register. It is a mechanical enumeration, not a reasoning gate — it does not withhold
anything pending a user rep; it produces a document and asks one question about what that
document should do.

## When to use

- The user asks for an **FMEA, a pre-mortem, a failure-mode register, or a reliability /
  risk review** of an architecture or workflow they describe.
- The user asks **"what could go wrong with this design"**, "where are the weak points",
  "what happens if each piece fails", "which parts are fragile".
- A design is up for review and someone wants its **failure surface enumerated** before
  sign-off.
- The user has a diagram or a written architecture and wants it **walked for failure
  modes** across categories they might not think to check (consistency, human/process,
  operational).
- A post-incident action item is "do an FMEA on this subsystem so we find the *next* one".

## Out of scope — hand these off

- **Picking the protection mechanism for a failure mode you already know about** — "the
  service falls over under load", "a slow dependency took everything down", "add a circuit
  breaker / rate limit / bulkhead" → `resilience-strategy`. That skill takes one concrete
  pressure and designs the defense; this skill *surfaces the candidate pressures* across
  the whole design. The dependency, overload, and cascade rows of this register are its
  input. Chain, don't merge.
- **Diagnosing a failure that is happening now** — "this endpoint started 500ing last
  night", "why is the queue backing up", with a hypothesis → `problem-solving-gates`
  (Rubber Duck). That is one bug, one hypothesis, right now. This skill is proactive and
  exhaustive; it runs when nothing is on fire.
- **Designing the alerting, the SLIs/SLOs, and the detection** — "what should we page on",
  "how do we know when this mode fires" → `observability-strategy`. This skill *scores*
  detection (how would we currently find out) and flags the modes where the answer is
  "a customer tells us"; turning that into instrumentation and alert policy is that skill,
  which takes this register's impact ranking as its starting point.
- **Choosing the test mix and writing the fault-injection / chaos tests** — which levels,
  effort split, what to actually inject → `test-strategy`. This skill produces the ranked
  target list ("these are the modes worth injecting"); that skill decides how they're
  tested and at what level.
- **A deep security audit** — the security category here is a coarse enumeration (is there
  an obvious auth gap, an over-exposed endpoint, a secret in the wrong place). A real
  threat model / pen-test / STRIDE pass is a separate, deeper exercise; name it and defer.
  Gaps between what the product *does* and what it *discloses or secures* — undisclosed data
  practices, a missing privacy control, a policy that doesn't match the build → that's
  `disclosure-gap-audit`, not an operational failure mode.
- **The blast radius of one already-decided add/modify/remove change** — "what could this
  specific change break", "is this a breaking change", "we're removing this endpoint" →
  `change-surface-audit`. That skill is reactive to one concrete, already-proposed change
  and its six blast-radius surfaces; this skill is proactive and exhaustive across a whole
  design with nothing yet decided. If someone hands over a whole design with nothing
  specific proposed, this skill; if they hand over one specific change, that one.
- **The capacity ceiling itself** — when a performance or availability mode's trigger is
  "load exceeds what the system can serve", the *number* (what QPS / storage / bandwidth it
  can take, and what binds first) is `capacity-estimation`. This skill records the mode;
  that skill sizes the threshold.
- **Computing or interpreting availability / composite-reliability numbers** (nines, serial-vs-parallel compounding, percentiles) → `reliability-math`. This skill records the mode; that skill does the arithmetic.
- **Fixing the modes** — the register lists and ranks; implementing mitigations,
  refactoring the fragile component, adding the retry logic is separate work, started
  explicitly per row.

---

## Inputs the procedure needs

Not a rep gate — but the analysis needs a system to analyze. If these are missing, ask for
them and stop; don't invent an architecture to critique.

1. **The component inventory** — every service, datastore, queue, cache, external API,
   scheduled job, and manual/human step in the part of the system under analysis. A diagram
   or a paragraph is fine; restate it as a list for confirmation.
2. **The interaction inventory** — every call, message, or data flow between those
   components: direction, synchronous vs asynchronous, and what it carries. This is where
   most failure modes live.
3. **The scope boundary** — which components are *in* the analysis and which are treated as
   "assumed reliable / analyzed elsewhere". A whole-system FMEA and a one-service FMEA are
   different exercises; say which.
4. **The analysis altitude** — whole design, one service, or one workflow end to end.
5. **What "severe" means for this system** — the worst realistic outcome (permanent data
   loss? a safety issue? a regulatory breach? an hour of downtime? one user sees a stale
   number?). This calibrates the severity scale so a "10" means something concrete.
6. **Existing detection** — what monitoring, alerting, and tests exist today, even roughly.
   Detection is scored against what exists *now*; "nothing yet" is a valid answer and it
   makes detection scores high (bad), which is itself a finding.

---

## The procedure

Work `nine-categories.md` and `scoring-and-register.md` alongside these steps.

### 1. Frame the system

Restate the component and interaction inventories as two lists. Draw the scope boundary
explicitly — name what is out and why. State the altitude. Confirm with the user before
walking, because an inventory error propagates into every row.

### 2. Choose the scoring scheme

From `scoring-and-register.md` (which has the when-to-use for each): **RPN** (severity × occurrence ×
detection, 1–10 each) for long-lived, regulated, or many-team systems and registers tracked over time;
**2-axis grid** (severity × likelihood, 1–5 → 5×5 red/amber/green) for a fast design-review pass, early
designs where occurrence/detection are too speculative, or sessions under ~90 minutes.

Pick one, and calibrate each axis *for this system* using input 5 — write down what a top-of-scale severity actually is here.

### 3. Walk each component × the nine categories

For every component, go through all nine categories from `nine-categories.md` and ask "what
does a failure in this category look like *for this component*?" Use the probe questions in
that file. Where a category genuinely doesn't apply to a component, record it as `n/a —
<reason>` so a skipped category is a decision on the record.

In chat, present a **coverage table** (one row per component, failure-mode IDs per category, one
`n/a` clause with reasons) rather than all `components x 9` cells; the full grid goes in the
written register only. Every component must still be walked against every category. Read
"Coverage table" in `nine-categories.md` for the format.

### 4. Walk each interaction × the interaction-heavy categories

Interactions concentrate failure in **integration, dependency, consistency, performance,
and availability**. Walk each interaction (sync and async) against them; the per-interaction
question list is under "Walking interactions" in `nine-categories.md` -- read it when doing this step.

### 5. Record each mode as cause → manifestation → impact

- **Cause** — the concrete trigger (a deploy, a load spike, a dependency outage, a bad
  input, a clock skew, an operator action).
- **Manifestation** — what an operator or user actually *observes* (504s, a stuck queue, a
  wrong total, silent data divergence). This is the symptom you'd see, not the internal
  fault.
- **Impact + blast radius** — the business/user consequence *and* how far it spreads: one
  request, one user, one tenant, one region, the whole system.

Keep each row concrete enough to be turned into a test.

### 6. Score and rank

Apply the chosen scheme. Sort by RPN (or grid band) descending. Then do the **severity
override**: pull every mode with top-of-scale severity into a separate **high-severity
watchlist** regardless of its RPN — a catastrophic-but-rare, well-detected mode gets a low
RPN and would otherwise be buried, and "rare" is not "won't happen".

### 7. Emit the register and the handoff lists

Produce the register table and the watchlist (format in `scoring-and-register.md`). Then
derive:

- **dependency / overload / cascade rows** → `resilience-strategy` (mechanism selection)
- **impact ranking + rows with a bad detection score** → `observability-strategy` (alerting
  and closing the detection gap)
- **the ranked rows as a target list** → `test-strategy` (fault-injection / chaos scope)
- **functional / consistency logic rows** → the normal engineering backlog
- **security rows** → a real threat-modelling pass if any are non-trivial

### 8. Ask what the register should do

Like `document-page-check`, put one choice to the user:

- **"Register only"** — hand over the ranked list and the handoffs; the user triages.
- **"Block sign-off"** — the design isn't considered reviewed until every high-severity
  watchlist row and every row above the RPN-must-mitigate threshold has an **owner** and an
  explicit decision. A row is **unblocked** when it carries an owner and *any* of the three
  decisions — *mitigate now*, *accept with reason + revisit trigger*, or *defer with a
  trigger*; a deferred or accepted row stays in the acceptance log with its trigger, it is
  not silently closed. The person who owns the design's sign-off confirms the unblock.
- **Owners on a small team** — if there aren't enough people to give blocker rows
  *independent* owners (a two-person team, 20 blockers), assign anyway and record the
  concentration as its own human/process failure mode (bus factor); "we couldn't staff
  independent owners" is a finding, not a reason to skip the field.

Default recommendation: for a design review or a pre-ship gate, recommend **block
sign-off**; for an exploratory "what are we missing" pass, **register only**.

---

## Output

**1. In chat**, a summary block then the register:

```
System under analysis:  <altitude — whole design / service / workflow>
In scope:               <components + interactions walked>
Out of scope:           <assumed-reliable components, and why>
Scheme:                 <RPN 1–10×3  |  2-axis 5×5>  ·  severity 10/5 here means: <concrete worst case>
Modes found:            <n>   (walked <c> components × 9, <i> interactions)
Top risks:              <the 3–5 highest — one line each: mode → RPN/band>
High-severity watchlist: <modes with max severity regardless of rank>
Detection gaps:          <count of rows where detection ≥ 8/10 or "customer would tell us">
Handoffs:                resilience-strategy <n rows> · observability-strategy <n rows> · test-strategy <n rows> · eng backlog <n rows> · threat model <n rows>
```

Then the full register table and the watchlist from `scoring-and-register.md`.

**2. On request** (or when "block sign-off" is chosen), write the register to
`docs/architecture/failure-modes/<system-slug>.md` (living document, not an ADR; create the
directory if absent). Read the "Written register file" section of `scoring-and-register.md`
for its required contents, including the acceptance log.

Then stop. Designing the mitigations, the alerts, and the tests are separate, explicitly
started steps that consume this register.

---

## Not a gate

This skill does not withhold analysis pending a user's independent attempt. If the user
wants a lighter touch — "just eyeball the obvious failure points" — do that and say it was a
partial pass, not the full nine-category walk. The full procedure is the default when
someone asks for "an FMEA" or "a pre-mortem" by name.

---

## Example invocations

Three worked invocations (a checkout-service pre-mortem scored with RPN, a narrow Redis-cache
addition, and a live-502 request that is routed away) are in `example-invocations.md`. Read it
when you need a model of a frame, sample rows, or the routing call.

---

## Portability

Repo-agnostic. Writes a living register to `docs/architecture/failure-modes/` (not the
`decisions/` ADR tree — this is a tracked document, not a point-in-time decision). Copy the
`failure-mode-analysis/` directory into another repo's `.claude/skills/` to use it there.
See `README.md` for where it sits among the sibling skills.

## Routing boundaries (full)

- A structured FMEA / pre-mortem procedure over a design, workflow, or service graph the user describes — it walks every component and every interaction, enumerates the ways each can fail across nine categories (functional, availability, performance, consistency, integration, dependency, security, operational, human/process), records each as cause → manifestation → impact with a blast radius, scores and ranks them (RPN = severity × occurrence × detection, or a lighter severity × likelihood grid for a fast design-review pass), and emits a prioritized failure-mode register plus a high-severity watchlist.
- Use when someone says "do an FMEA", "failure mode analysis", "run a pre-mortem", "what could go wrong with this design", "where are the weak points / failure points", "reliability or risk review of this architecture", "walk the failure modes", "what happens if each part fails", or hands over an architecture and asks for its failure surface.
- This is a proactive enumeration across the whole design and all nine categories — it is not picking the protection mechanism for one already-known overload or dependency failure (that is `resilience-strategy`, which consumes the dependency/overload rows of this register), not diagnosing one failure that is happening now (that is `problem-solving-gates` Rubber Duck, which needs one hypothesis about one bug), not designing the alerting or SLOs (that is `observability-strategy`, which consumes this register's impact ranking and detection-gap rows), not choosing the test mix or writing the fault-injection tests (that is `test-strategy`, which consumes this register as its chaos / fault-injection target list), and not the blast radius of one already-decided add/modify/remove change (that is `change-surface-audit`, reactive and scoped to one concrete change; this skill is proactive across a whole, not-yet-decided design).
- Not the happy/unhappy/edge test-case list for one feature — that is `test-case-discovery`, which hands the chaos / fault-injection target list back here.
- It is a procedure that produces an artifact, not a gate that withholds an answer; the only thing it puts to the user is register-only vs block-sign-off-until-triaged.
- Not for policy-vs-practice disclosure or missing-security-control gaps — that is `disclosure-gap-audit`, a different audit than an operational pre-mortem.
- Not for a-priori sizing arithmetic — that is `capacity-estimation`, whose "what binds first" line feeds this register's performance rows.
- Not for triaging a live, reproducible symptom that is happening now to the right observation layer -- that is `debugging-layer-selection`; this skill runs when nothing is on fire.
