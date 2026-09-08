# incremental-build-pacing

A delivery-cadence gate for AI-assisted implementation. When a build is already planned — spec
written, slice chosen — but the user wants to *understand* the codebase as it's assembled, this
skill withholds the large one-turn batch: it sets an increment size and checkpoint cadence, maps
the slice, and delivers one piece at a time with a comprehension check before each advance.

It is a **gate**: it withholds "here is the whole slice" until the pacing contract is set, and
withholds each next increment until the current one is understood.

## Where it sits

| Boundary | Skill | Split |
|---|---|---|
| What to build / scope | `spec-drift-gate`, `design-scoping` | Those settle the spec, the out-of-scope line, and the slice. This skill starts only once a concrete slice exists and governs delivery of it. No spec → hand back. |
| Whether the user wants to learn at all; the assistance-level ceiling | `learning-gate` | `learning-gate` classifies intent and routes here from its Step 3 table when intent is learning and the rep is "understand a build as it's assembled". This skill runs the delivery once routed. |
| A procedure the user performs with their own hands | `learning-gate` → `guided-walkthrough.md` | There the user makes every move (env setup, tool wiring, a runbook). Here Claude may write the code; the user owns the understanding, checked per increment. |
| A bug, a slow path, an architecture choice mid-build | `problem-solving-gates` | Those get their own prior-effort rep. Resume this loop after. |
| Prose style of the explanations | `delete-ai-words` | Not this skill's job. |

## Files

| File | Role |
|---|---|
| `SKILL.md` | The apply check, the pacing contract, increment mapping, the loop, drift handling, Never list, escape hatch, examples. |
| `increment-delivery.md` | The per-increment protocol in detail — batch-vs-slow-down sizing table with examples, the delivery shape, coaching register, keeping the map visible, ending criteria. |

## Design choices

- **Governs cadence, not scope.** Deliberately starts after `spec-drift-gate` / `design-scoping`.
  A skill that both scoped and paced would re-open the same scope fights those skills exist to
  close.
- **Claude still writes the code.** The distinction from `guided-walkthrough.md` is that the
  user's rep is comprehension — say it back, could you change it — not keystrokes. A "user types
  it" dial exists in the contract for those who want it.
- **Plumbing is batched on purpose.** A comprehension check on an empty `__init__.py` trains
  nothing and teaches the user the checks are noise. The sizing table pushes the attention onto
  the few load-bearing files.
- **Escape hatch widens before it drops.** Faster means a bigger increment or a longer cadence
  first; "execution mode" drops the skill immediately.

## To try it

- "Build the accounts slice one file at a time, explain each — I want to learn the stack" → sets
  the contract (one file / stop each / Claude writes), maps the files, runs the loop.
- "You generated 40 files at once, let's redo it slower" → mid-build entry; resume from where
  understanding stops, not from the next unwritten file.
- "Just build the whole thing, make it work" → doesn't apply; normal execution.
- "Walk me through running the migration myself" → `guided-walkthrough.md`, not here.
