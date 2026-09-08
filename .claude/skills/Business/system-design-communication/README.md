# system-design-communication skill

A live coaching skill (not a decision gate, not a procedure with a wrong-answer failure
mode) for practicing the *communication* side of system design — explaining a design out
loud, surviving a mock interview, defending a tradeoff under "what if?" pressure. It never
supplies the "right" design; the whole point is exposing gaps in the user's own explanation
and pressure-testing their own reasoning, not doing the design work for them.

Converted `2026-09-05` from a `.claude/agents/system-design-communication/` directory the
user had copied in from another project. As authored there it was structurally inert in this
harness — Claude Code subagents load from a single flat `.claude/agents/<name>.md` file, not
a directory with a nested `AGENTS.md` — and even fixed, the mechanism was wrong: all three
modes are live, turn-by-turn dialogue with the user in the foreground conversation, which is
what a Skill does, not what an Agent (a scoped, semi-autonomous delegate) does in this
project. The content itself needed no real rewrite — it was already shaped almost exactly
like this project's skill convention (an entry file + reference files for the deep material),
just carried over from `AGENTS.md`/`prompts/*.md` into `SKILL.md` plus two reference files
with no substantive changes.

## Where it sits

This is the only skill in the catalog about *rehearsing* system-design communication rather
than *doing* system design or *reporting on finished* system-design work:

```
design-scoping                  →  real system-design front door — produces a scope statement (real stakes)
system-design-communication     →  rehearse explaining a design — walkthrough / mock interview / tradeoff defense (this skill)
explaining-my-work               →  write up already-completed real work for a real audience (plain summary / script / post)
```

The dividing line with `design-scoping`: that skill fires the moment "design/architect a
system" is the *real* intent for something that will actually get built, and refuses to
proceed until purpose, scope, and numeric targets are stated. This skill fires when the
"design" is either hypothetical, already-settled, or explicitly framed as practice/interview
prep — the tell is stakes, not vocabulary. A request that sounds like "design a system for
X" but turns out to mean "let's rehearse me explaining a system for X" belongs here, not
there.

The dividing line with `explaining-my-work`: that skill turns a real evidence base into a
written deliverable for a real audience (a summary, a spoken script, a public post) — output
is a document. This skill runs a live back-and-forth practice session — output is the
practice itself plus a spoken debrief, not a document, and it's just as often exercised on a
hypothetical design as a real one.

The dividing line with `learning-gate`: each of this skill's three modes already embeds its
own no-answer-giving, gap-exposing coaching discipline (see the Shared discipline section in
`SKILL.md`) — that discipline *is* the coaching-level decision `learning-gate` would
otherwise be making. Stacking a second precondition on top would just re-ask a question this
skill's own mode selection already answered.

## The shape

Not a rep gate, not a procedure with inputs to gather — a mode selection (Walkthrough / Mock
Interview / Tradeoff Defense) followed by a live coaching session with its own internal
discipline (stay in listener/interviewer mode, don't rescue with the answer, debrief only at
the end).

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The three modes, when each applies, the shared discipline across all three, boundary lines. |
| `explain-design.md` | Mode 1 running notes — structure, pacing, how to probe without rescuing. |
| `interview-simulation.md` | Mode 2 running notes — staying in character, timeboxing, the debrief. |

Mode 3 (Tradeoff Defense) has no separate reference file yet — thin enough that `SKILL.md`'s
own description plus the shared discipline section covers it, same call the source material
made before conversion. Split it out if it sees enough real use to need more structure.

## Output

Entirely conversational — a live practice session plus a one-line recap or debrief at the
end. Writes no file.

## Interaction with sibling skills

- **`design-scoping`** — owns real system-design intent. A boundary clause was added there
  pointing rehearsal/interview-prep requests here instead of front-dooring them into a real
  scope-statement gate.
- **`explaining-my-work`** — owns writing up real, completed work for a real audience. A
  boundary clause was added there distinguishing its written-deliverable job from this
  skill's live-practice job.
- **`learning-gate`** — not registered in its Step 3 table. Unlike every other new domain
  skill in this catalog, this one doesn't need a rep deferred to it — it fires on its own
  distinct request shape (practice/interview-prep framing) rather than being reached through
  learning-gate's intent classification, the same reasoning that kept `skill-interaction-testing`
  and `catalog-drift-audit` off that table.
- **`ticket-evaluation`, `technical-cost-decision`, `user-story-decomposition`** — no
  realistic collision surface; none share a concrete concept with rehearsing an explanation
  out loud.

Converted by inspection, not run through a full isolation-screen / multi-agent
`skill-interaction-testing` cycle — the source content was pre-existing and well-formed, and
the only real changes made were the two reciprocal boundary clauses above. Worth a real
`skill-interaction-testing` pass the next time this skill's description changes.

## Using it in another repo

Repo-agnostic. Writes nothing.

```
cp -r ".claude/skills/Business/system-design-communication" /path/to/other-repo/.claude/skills/
```
