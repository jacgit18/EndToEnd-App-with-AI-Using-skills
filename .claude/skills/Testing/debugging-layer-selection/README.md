# debugging-layer-selection skill

A procedure (not a gate) for triaging one live, reproducible symptom to the right
observation layer before investigating it: Chrome DevTools (what is my application doing),
backend observability (what is my server doing), or Wireshark/tshark (what is actually
happening on the network). The rule it enforces: start at the highest abstraction level that
can explain the symptom, and descend toward packet-level analysis only when that level's
evidence is insufficient. It answers "where do I look," then stops — it does not diagnose
the cause itself.

Built from a standalone "Chrome DevTools + Wireshark Debugging Skill" reference doc: the
Chrome-DevTools-vs-Wireshark decision framework, the abstraction-layer model, the
symptom-to-tool tables, the AI-agent-grounded debugging note (tool calls against real output,
not an LLM guessing from a raw capture), and the Tier 1/2/3 learning-priority list.

## Where it sits

```
debugging-layer-selection  →  which layer/tool explains a live symptom   (this skill)
problem-solving-gates        →  Rubber Duck: the hypothesis-and-reasoning gate once you're
  (Rubber Duck)                 looking at the right layer's evidence
observability-strategy       →  what signals/dashboards/alerts should exist, durably
problem-solving-gates        →  Optimization: what to do once you have a measurement /
  (Optimization)                profile already localizing the cost
failure-mode-analysis        →  proactive enumeration before anything is on fire
```

This skill is reactive and ad hoc — one symptom, right now. `observability-strategy` is
proactive and durable — what should always be instrumented. If triage under this skill keeps
concluding "we have no way to see this layer," that's a signal to run
`observability-strategy` afterward, not a reason to design it mid-incident.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The 5-step decision procedure and output contract. |
| `bug-record.md` | Step 0 template: the reproducible bug record (repro, expected/actual, verbatim error, environment, timing, ruled out) and the not-reliably-reproducible variant. |
| `layer-reference.md` | Abstraction model, full symptom → tool tables for both DevTools and Wireshark/tshark, the AI-agent-grounded variant, the Tier 1/2/3 learning list. |

## What it produces

A short recommendation in chat: the bug record (or its missing fields), the layer, the specific panel/command to open there, and
what finding at that layer would mean "done" versus "descend further." It does not open the
tool, read the output, or diagnose the cause — that's the debugging itself, or
`problem-solving-gates` (Rubber Duck) once a hypothesis starts forming from what the chosen
layer shows.

## Deliberately out of scope

- Reasoning about *why* a bug happens once you're looking at the right layer's evidence →
  `problem-solving-gates` (Rubber Duck). Chain: this skill locates the evidence, Rubber Duck
  reasons over it.
- Designing what signals/SLIs/dashboards/alerts a system should have long-term →
  `observability-strategy`.
- Optimizing code you've already localized with a profile in hand →
  `problem-solving-gates` (Optimization) — though DevTools' Performance/Memory panels are
  frequently *where* that profile comes from, which is this skill's territory.
- Proactively enumerating everything that could go wrong before anything has →
  `failure-mode-analysis`.
- The test mix, coverage target, or writing tests → `test-strategy` / `coverage-policy` /
  `test-practice-gate`. Unrelated axis; grouped here as a sibling because both are
  quality/engineering-practice skills, not because the subject matter overlaps.

## Using it in another repo

Repo-agnostic; names no project-specific files or paths.

```
cp -r .claude/skills/Testing/debugging-layer-selection /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Tested via `skill-interaction-testing` (worktree agent, 5 scenarios) at build time — 2 real
issues found and fixed reciprocally, recorded here so the pair isn't silently re-tested
without a new reason:

- **vs `problem-solving-gates` (Rubber Duck) — starvation, fixed.** Rubber Duck's Mode 1
  trigger is broad enough ("user is debugging... without having shown their own attempt
  first") to claim a bare "no idea where to even start" and demand a hypothesis before any
  evidence is located — backwards, since you can't hypothesize about a layer you haven't
  looked at yet. Fixed with a one-line hand-off added to `problem-solving-gates` Mode 1,
  right after its Trigger line, deferring to this skill when no layer/tool is picked yet.
  The reverse direction (a stated, falsifiable hypothesis → skip straight to Rubber Duck,
  don't re-ask "which layer") was already safe by keyword mismatch. The pointer is mirrored
  for robustness in this skill's description, in `problem-solving-gates`' description
  carve-outs, and in `learning-gate`'s Step 3 Debugging row (which also routes the
  which-layer question here instead of Rubber Duck).
- **vs `observability-strategy` — contradiction/stacking, fixed.** Its description contains
  the near-verbatim phrases "we can't tell why prod is slow" and "our logs are useless in an
  incident," and its existing carve-out routed only to `problem-solving-gates`, never to this
  skill — so a live-incident prompt could trigger both a heavy multi-question ADR gate and
  this skill's light mechanical procedure at once, with no resolution between them. Fixed
  with an added clause on `observability-strategy`'s carve-out sentence: the *ad hoc,
  haven't-checked-yet* reading of that complaint is this skill; the *no durable way to see
  this at all* reading stays `observability-strategy`.
- **vs `failure-mode-analysis`** — clean, no fix needed. This skill's description carves it out (proactive, nothing on fire); `failure-mode-analysis` does not yet point back here, so a back-pointer on its side is a pending reciprocal edit. Proactive/no-symptom trigger
  phrasing doesn't overlap with this skill's live-symptom phrasing.
- **Control scenario** (unambiguous "DevTools or Wireshark for this dropped WebSocket")
  fired only this skill, confirming the fixes above didn't overcorrect into starvation the
  other direction.
- **vs `problem-solving-gates` (Optimization)** — that mode requires a measurement already in
  hand before Claude engages. This skill is frequently the step that *produces* the
  measurement (which DevTools panel to open) when the user doesn't have one yet.
- **vs `failure-mode-analysis`** — proactive/design-time vs reactive/live-symptom. Not
  expected to be confused in practice (very different trigger phrasing), but both are
  "systematic investigation procedures" in the same architectural family.
- **vs Testing-group siblings (`test-strategy`, `coverage-policy`, `test-practice-gate`)** —
  no real overlap; different axis (deciding a test approach vs. debugging a live symptom).

- **Step 0 bug record (added later, from a pasted "document the error first" prompt).**
  Folded in as a capture step instead of a new skill, per the prefer-a-lens-over-a-new-skill
  preference. Reciprocal pointer added to `problem-solving-gates` Rubber Duck. Interaction
  tested with 6 read-based scenarios (control, vague symptom, stated hypothesis, full record,
  "no questions" pressure, `observability-strategy` overlap): no stacking or starvation of
  siblings; carve-outs with Rubber Duck, `learning-gate`, `ambiguity-gate` and
  `observability-strategy` held. Fixes applied from the run: cap of 2-3 asks, no restating a
  complete record, hard exception narrowed (tool-choice questions and "no questions" still get
  an answer) with a provisional hint, a branch for a failing client that isn't yours, proxy/LB
  access log checked before packet capture, and the "almost certainly an Authorization header"
  example softened so it doesn't teach a diagnosis. Post-fix re-run of the three most-changed scenarios (vague symptom, "no questions", full record): all pass; two small follow-ups applied (intermittent-rate ask; the slow-request example now checks the proxy/LB log before Wireshark, matching step 4).
