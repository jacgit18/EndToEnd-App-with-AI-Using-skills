# codebase-file-orientation skill

A **procedure** that authors or reconciles a companion **orientation doc** for a source-code file that
was just created or substantially changed. The doc is a short sidecar `.md` — matched to whatever doc
convention the repo already uses, or a sidecar `<file>.md` beside the source if there is none —
covering the file's **role**, its **entry points**, what it **depends on** (and what depends on it),
and the **gotchas** a reader can't infer from the code. Two modes: **Author** (no doc yet) and
**Reconcile** (a doc exists; diff it against the current file and propose a patch).

It is explicitly **complementary to inline comments**, not a replacement: comments carry the local
"why" at a line, this doc carries file-level "where". Writing the doc is not licence to strip the "why"
comments.

## Where it sits

```
codebase-file-orientation  →  the standing per-file doc: role, surface, edges, gotchas   (this skill; procedure)
explaining-my-work         →  completed work rendered for a human audience (post/script/summary)   (Business)
document-page-check        →  integrity pre-flight on a PDF/EPUB before Claude reads it   (Documents; opposite direction)
spec-drift-gate            →  the spec written BEFORE a multi-file build, audited as it drifts   (Skill Development)
change-surface-audit       →  what one change breaks ELSEWHERE in the system   (Architecture)
session-handoff            →  ephemeral end-of-session context dump with next steps   (Prompts)
commit-and-push            →  the commit message from the diff   (Git; composes — document, then commit)
problem-solving-gates      →  Knowledge Checker: "explain X so I can check I got it" — a rep, not this
learning-gate              →  Step 3: "document a file I made" = execution/reference, defers here
```

The boundary most worth stating: **`explaining-my-work` faces a person, this faces the codebase.**
"Write up what I built" → words for an audience → `explaining-my-work`. "Document this file" → an
in-repo structural reference for whoever reads the code next → here.

The second: **`spec-drift-gate` is forward, this is backward.** A spec is intent for work not done; an
orientation doc describes a file that exists now. `spec-drift-gate` even treats a settled scope as an
input and won't re-gate it — it has nothing to say about documenting the result.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point — when it applies / doesn't, the inputs, mode detection, the Author and Reconcile steps, the output block, the unprompted-offer rule. |
| `orientation-doc-format.md` | The fixed doc template field-by-field; the "belongs in the doc / in a comment / nowhere" rubric; the list of what the doc must not become; the Reconcile drift checklist. |

## What it produces

**Author:** one `.md` per file, written at the repo's detected doc convention (or a sidecar beside the
source), plus any `TODO(author)` lines for facts that couldn't be traced.

**Reconcile:** a drift report block (Role / Entry points / Depends on / Gotchas / Keep in sync +
newly-missing symbols) and a proposed patch — **not applied until the user confirms**.

## When it does NOT apply

- "Turn this into a post / script / standup / resume line" → `explaining-my-work`.
- "Give me a mock interview on this design" → `system-design-communication`.
- "Check this PDF is complete before you summarise it" → `document-page-check`.
- "Write the spec before I build this" → `spec-drift-gate`.
- "What does removing this break" → `change-surface-audit`.
- "Save my progress / wrap up for tomorrow" → `session-handoff`.
- "Write the commit message" → `commit-and-push` (run this first, then commit the doc with the code).
- "Explain how this file works so I can check I understood it" → `problem-solving-gates` (Knowledge
  Checker) — the user states their model first; this is not a study aid.
- The file already has a docstring the repo's tooling reads and it already carries role + surface →
  the sidecar may be unnecessary; say so.

## Using it in another repo

Repo-agnostic — reads source, writes one `.md` per file at the repo's own convention, owns no fixed
`docs/` path.

```
cp -r ".claude/skills/Documents/codebase-file-orientation" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Tested against the scoped pool on 2026-09-07 (`skill-interaction-testing`, 12 scenarios / 3 worktree
agents). Pool: `Documents/document-page-check` (tier 1) + `ambiguity-gate`, `learning-gate`,
`problem-solving-gates`, `problem-journal` (tier 2) + `explaining-my-work`,
`system-design-communication`, `spec-drift-gate`, `session-handoff`, `change-surface-audit`,
`commit-and-push` (tier 3). **One starvation fix + four reciprocal-pointer fixes; rest CLEAN.**

Run `skill-interaction-testing` whenever this skill or a sibling's description changes. Boundaries to
hold:

- **vs `problem-solving-gates` (Knowledge Checker)** — *the fix.* "Explain how this module works so I
  can check my understanding" was pulling this skill in and starving the rep. Now carved out both in
  this description and as an Out-of-scope bullet: this writes a reference *for other readers*, never a
  study aid.
- **vs `explaining-my-work`** — audience is the tell: a person hearing/reading about the work vs. a
  developer reading the code. Reciprocal carve-out added to `explaining-my-work`. Not a chain; pick one.
- **vs `document-page-check`** — both in `Documents/`, opposite directions: one *checks a document
  being consumed*, one *produces a doc about code*. Both descriptions carve the other out; no overlap
  in practice (CLEAN).
- **vs `spec-drift-gate`** — forward intent vs. backward description. The "needs a concrete existing
  file path" input gate keeps "set up the docs before I build" routing to `spec-drift-gate` (CLEAN).
- **vs `session-handoff`** — at session wrap-up this skill stays out entirely (description clause), no
  per-file-doc step stacked onto the handoff (CLEAN after fix).
- **vs `change-surface-audit`** — describing the changed file vs. tracing what the change breaks
  elsewhere. They *chain* on a risky change (audit blast radius, then Reconcile the file's doc).
  Reciprocal pointer added to `change-surface-audit`.
- **vs `commit-and-push`** — composes: document new files, then commit (doc included). Reciprocal
  pointer added to `commit-and-push`; this skill's unprompted offer never blocks the commit.
- **vs `ambiguity-gate`** — "document the stuff I changed": ambiguity-gate asks the one question; this
  skill's "not 'the stuff I changed'" clause keeps it from racing ahead. The post-answer "confirm the
  list" step is a confirmation, not a second question (CLEAN).
- **vs `learning-gate`** — classifies "document this file I made" as execution and defers; Step 3 row +
  "Never" list entry added. Only keeps the floor if the user asked to *learn how to document code*.
