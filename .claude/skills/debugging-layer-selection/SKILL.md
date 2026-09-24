---
name: debugging-layer-selection
description: Procedure for triaging a live, reproducible symptom to the right observation layer: browser DevTools, backend logs/traces/metrics, or packet capture (Wireshark). Triggers: "should I use DevTools or Wireshark for this", "how do I debug this network issue", "is this a browser bug or a network problem", "why is this connection dropping/resetting". Not hypothesis testing (`problem-solving-gates`), long-term signals (`observability-strategy`), or `failure-mode-analysis`.
---

# Debugging Layer Selection

Given one live, reproducible symptom, decide which tool answers the question you actually
have — Chrome DevTools (what is my application doing), backend observability (what is my
server doing), or Wireshark/tshark (what is actually happening on the network) — before
opening any of them. The rule: **start at the highest abstraction level that can explain the
symptom, and descend only when that level's evidence is insufficient.** More raw information
(a packet capture) is not automatically more useful information than what the browser already
shows for free.

## When to use

- Someone has a concrete, reproducible symptom and is about to start debugging but hasn't
  picked a tool: a slow request, a failed call, a dropped connection, an error with an
  unclear cause, "why is this happening".
- Someone asks directly which tool to reach for: "DevTools or Wireshark for this", "should I
  capture packets", "is this a network problem or my code".
- Someone is already one layer down and stuck: the Network panel shows the request left the
  browser and a response never came back, and the next question is whether that's the
  backend or the network in between.
- Someone names a network-layer term without having confirmed it's actually where the
  problem lives — "we're getting TCP resets", "there's a retransmission" — before capture
  effort is spent confirming that's real.

## Out of scope — hand these off

- **Forming or testing a hypothesis about root cause** once you're looking at the right
  layer's evidence — `problem-solving-gates` (Rubber Duck). This skill answers "where do I
  look"; Rubber Duck owns "what do I think is wrong and how do I check it". Chain them: this
  skill locates the evidence, Rubber Duck reasons over it. If the user already has a stated,
  falsifiable hypothesis, skip this procedure and go straight to Rubber Duck — don't re-ask
  "which layer" once a guess about the cause already exists.
- **Designing what signals, SLIs, dashboards, or alerts a system should have** on an ongoing
  basis — `observability-strategy`. This skill is reactive and ad hoc (one symptom, right
  now, with whatever tooling already exists or a one-off capture); that skill is proactive
  and durable (what should always be instrumented). If triage keeps landing on "we have no
  way to see this," that's a signal to run `observability-strategy`, not a reason to build it
  mid-incident.
- **Optimizing code you've already localized with a profile** — `problem-solving-gates`
  (Optimization mode) owns the "I have a measurement, now what" step. This skill is for
  *getting* that measurement when you don't yet know which layer holds the cost — including
  when DevTools' own Performance/Memory panels are the right measurement tool.
- **Proactively enumerating what could go wrong before anything has** — `failure-mode-analysis`
  runs on a design with nothing on fire; this skill runs because something already is.
- **The test mix, coverage target, test-case list, or writing tests** — `test-strategy`, `coverage-policy`, `test-case-discovery`,
  `test-practice-gate`. Unrelated axis entirely.

---

## The procedure

**Step 0 — Bug record.** Before picking a layer, capture the symptom well enough to reproduce
without follow-up questions: repro steps, expected vs. actual, verbatim error output,
environment, timing/frequency, what's already ruled out (template and the
not-reliably-reproducible variant in `bug-record.md`). This is a capture step, not a gate.

- **Record already complete** (or the user has a stated hypothesis / is mid-investigation with
  evidence in hand): say "record complete" in one line and move on. Don't restate it back.
- **Gaps:** fill what you can from what the user already gave, and ask for at most 2–3 of the
  missing fields, most useful first — verbatim error output, then where the call originates
  (browser / service / script; local / staging / prod). One round, appended to the layer
  recommendation, not before it. Never invent a field.
- **Never withhold the layer recommendation** for a field the user can't or won't supply, and
  honor "no questions": say which fields are missing and proceed. If the question asked is
  answerable without the details (e.g. "DevTools or Wireshark?"), answer with the
  highest-layer-first rule and flag what would sharpen it.
- **Only exception:** a bare "it fails sometimes" with no repro steps and no error output, and
  a question that depends on them ("where do I look?"). Ask for the error output and the origin (plus the observed rate, if it is intermittent)
  first, and give a provisional hint in the same turn (which layer you'd open first if the
  answer is X vs. Y) so the turn isn't only questions.
- **Failing client isn't yours** (some users in prod, a request that already happened): the
  browser steps below can't run. Ask for a HAR or RUM trace from an affected user, or start
  at backend observability scoped to that request (edge access log → app log → DB/downstream).

Then ask what the browser already shows, in this order, and stop at the first step that resolves
the symptom:

1. **Is this a browser or frontend problem at all?** — JS error, DOM/CSS issue, a component
   not re-rendering, a console error. If yes: Chrome DevTools (Console, Sources), done.
2. **Is it about one HTTP/HTTPS/WebSocket request?** — status code, headers, payload, timing,
   which code fired it, CORS, auth/cookies, caching, a service worker. Start in the Network
   panel. Most application-level questions resolve here; see `layer-reference.md` for the
   full symptom table.
3. **Does the Network panel's own timing breakdown (Queueing → Stalled → DNS → Connecting →
   TLS → Waiting (TTFB) → Content Download) already explain it?** — e.g. it's all in
   "Waiting", meaning the browser sent the request cleanly and is waiting on the server. If
   yes, the browser's job is done; move to backend observability (logs/traces for that
   request), not to a packet capture.
4. **Is the backend healthy and the request/response well-formed, but the behavior is still
   unexplained** — inconsistent latency with no server-side cause, a connection that resets
   before any HTTP exchange, TLS failing before the browser gets far enough to log a normal
   error? First check the reverse proxy / load balancer / server access log, which times the
   request before and after the handler and often explains a "handler fast, browser slow" gap
   without a capture. If that is also clean, that is the actual trigger for Wireshark/tshark: TCP handshake, retransmissions,
   resets, DNS packet behavior, TLS negotiation, raw timing between machines.
5. **Is the traffic non-HTTP, or between two machines/services with no browser involved at
   all** (service-to-service, a non-web protocol, arbitrary host-to-host traffic)? Skip
   steps 1–3 — there is no browser layer to check first — but still start with the
   highest layer that exists: the failing side's own logs/traces, the proxy or load balancer
   log (step 4), and any error the client library already reports. Go to Wireshark/tshark
   once those are clean, missing, or already point at the wire (resets, retransmissions,
   handshake or DNS failures).

**Do not skip to step 5 because packet capture "has more information."** If step 1–3
already explains the symptom, stop there — the fact that a lower layer is more detailed is
not evidence it is where the answer lives.

`layer-reference.md` has the full abstraction model, a symptom → tool lookup table for both
tools, the AI-agent-assisted variant of this same procedure (grounding an agent's tool calls
in real DevTools/tshark output rather than having it guess from a raw capture), and a
Tier 1/2/3 learning-priority list for a generalist engineer building this judgment over time.

---

## Output

State, in order: **the bug record** (or the fields still missing from it), **the layer** (browser/application, backend, or network), **the specific
panel/command to open there** (e.g. "Network panel, filter by the failing request" or
"`tshark -i any -f 'tcp port 443'` on both ends"), and **what finding at that layer would
mean you're done vs. need to descend further**. Then stop — actually reading that tool's
output and reasoning about it is the debugging itself (or `problem-solving-gates` Rubber
Duck, if a hypothesis is already forming), not this procedure.

**If the investigator is an agent rather than a person**, name whether the chosen layer's
tool is itself agent-drivable (Chrome DevTools MCP for the browser/application layer, a
`tshark`-wrapping tool for the network layer — both scriptable) versus requiring a human at
a GUI — see `layer-reference.md`'s AI-agent-grounded section for the "ground every step in a
real tool call, not inference from a raw capture" rule this implies.

---

## Example invocations

> "A POST to /api/users is returning 401 and I don't know why."

Step 1–2: application-level symptom with a clear HTTP status. Answer: Chrome DevTools Network
panel, inspect the request and response headers for the failing call. No reason to go further
yet. (Name where to look, not the suspected cause — forming that guess is Rubber Duck's job.)

> "GET /api/orders takes 4.8s in the Network panel — Waiting is 4.7s of that, Content Download
> is 100ms. Backend logs for that request show nothing unusual and normal processing time."

Step 3 resolved (all the time is server-side wait, backend logs look clean but that's a
contradiction) → step 4: the backend claims it was fast but the browser waited 4.7s longer
than that, so the time is spent before or after the handler. Check the reverse proxy / load
balancer / server access log for that request first (total vs. upstream time). Only if that
also shows a fast server is a Wireshark capture on both ends (TCP retransmissions, a stalled
TLS renegotiation) justified, to explain the gap the application-level views can't.

> "We're seeing TCP resets in our load balancer logs between two internal services."

Step 5: no browser involved, and the load balancer log already shows the resets, so the
evidence points at the wire. Wireshark/tshark on both hosts.

---

## Portability

Repo-agnostic; names no project-specific files or paths. Copy the
`debugging-layer-selection/` directory into another repo's `.claude/skills/` to use it there.

## Routing boundaries (full)

The frontmatter `description` is kept short for the skill listing budget; the full original description is preserved here.
- A procedure for triaging a live, reproducible symptom (a slow request, a failed call, a dropped connection, unexplained behavior) to the right observation layer before investigating — browser/application (Chrome DevTools: console, network panel, performance, memory, application/storage), backend observability (logs, traces, metrics), or the network/packet layer (Wireshark/tshark: TCP, TLS, DNS, retransmissions, resets).
- Use when someone asks "should I use DevTools or Wireshark for this", "how do I debug this network issue", "is this a browser bug or a network problem", "the request is slow/failing and I don't know where to look", "should I capture packets", "why is this connection dropping/resetting", "CORS error" / "401 with no body" / "the response never arrives" investigated from scratch, or names a symptom (retransmissions, TLS handshake failure, WebSocket disconnects, DNS resolution) without having picked a tool yet.
- It is a mechanical decision procedure, not a gate — it does not withhold anything pending a user rep; it captures the bug record, then asks one question (what does the browser already show) and returns a layer plus what to look for there, with an explicit rule to stop at the highest abstraction level that already explains the symptom.
- Not for reasoning about *why* a bug happens once you're looking at the right layer's evidence — forming and testing that hypothesis is `problem-solving-gates` (Rubber Duck), which this skill feeds by locating the evidence first; if the user already has a stated, falsifiable hypothesis, skip straight to Rubber Duck instead of re-asking which layer.
- Not for designing what signals, dashboards, or alerts a system should have long-term — that's `observability-strategy`; this skill uses whatever observability already exists plus ad hoc tool capture, reactively, for one symptom happening now.
- Not for optimizing code you've already localized with a profile in hand — that's `problem-solving-gates` (Optimization); this skill is for when you don't yet know which layer even holds the slowness.
- Not for proactively enumerating everything that could go wrong with a design before it ships — that's `failure-mode-analysis`, which runs when nothing is on fire; this skill runs because something already is.
- Not for the test mix or coverage of a system — `test-strategy` / `coverage-policy`.
- Not for interpreting live telemetry numbers once a layer is chosen -- percentile breakdowns, SLO burn, Little's Law, utilization against the queueing curve (`reliability-math`); not for a user who cannot begin at all ("where do I even start" with no observed symptom yet) -- that is `entry-point-first`, which hands back here once there is a live symptom.
