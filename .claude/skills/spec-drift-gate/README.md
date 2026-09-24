# spec-drift-gate

A spec-before-build gate. Before substantial AI-assisted implementation (multi-file, multi-turn,
or multi-session) it refuses to start writing code until a written spec exists — problem framing,
a tradeoff actually weighed, an in-scope *and* out-of-scope line, and (when the approach is
uncertain) a cheap controlled-experiment slice. Mid-build it diffs the work against that spec at
each checkpoint and forces every expansion to be either an amendment or a pull-back.

It is a **gate**: it withholds implementation until the spec is written down, and withholds
"proceed" on out-of-spec work until the expansion is named.

## Where it sits

| Boundary | Skill | Split |
|---|---|---|
| A whole system to design (purpose, audience, numeric targets) | `design-scoping` | Owns the front door. Its settled scope statement satisfies this gate's framing and scope items; tradeoffs and the experiment slice are still required here. |
| One request with more than one reading | `ambiguity-gate` | Resolve the reading first; once intent is "build this multi-step thing", this gate's spec applies, not a second clarifying question. |
| Blast radius of one decided change on existing code | `change-surface-audit` | That audits the codebase against a change; this audits the build against its own plan over time. |
| End-of-session context dump | `session-handoff` | The spec is what a handoff points back to, not a replacement for one. |
| "Walk me through it" setup the user performs | `learning-gate` → `guided-walkthrough.md` | Not an unattended build; this gate resumes only if the task grows into one. |
| Delivery pace of a specced build | `incremental-build-pacing` | Starts only after this gate names a slice; scope and Step 4 drift checks stay here. |
| Running a slice unattended | `spec-executor` agent | Executes one slice; its report is a Step 4 checkpoint, never an approval. |
| Cheaper-model routing for a slice | `model-routing-decision` (In-session mode) | The named agent's own model wins over a tier guess. |

## Files

| File | Role |
|---|---|
| `SKILL.md` | Applicability table, spec gate, extraction interview, precision instruction, executor handoff, Step 4 drift check, red flags. |

## Design choices

- **The out-of-scope line is the load-bearing item.** "In scope" alone bounds nothing; drift lives
  in what was never excluded.
- **Draft from context, confirm, don't interrogate.** The interview (Step 2a) is capped at 2-3
  rounds and every question must be able to change the build.
- **Drift is a decision, never a default.** Amend or pull back; silent expansion is the failure.
- **Subagent reports are input, not approval.** Whoever reviews diffs the report against the spec.

## To try it

- "Build me a dashboard for my finances" → no spec yet: run the Step 2a interview, write the spec, then slice.
- "Phase 2 starts now — also, add CSV export while you're in there" → Step 4: CSV export isn't in the spec; amend or pull back.
- "Add a null check on line 40 of parse.py" → does not fire; the request already is the spec.
- "Build an app for my gym" → `design-scoping` first; this gate adds the build-level spec afterward.
