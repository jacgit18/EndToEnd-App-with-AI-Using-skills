---
name: codebase-file-orientation
description: >
  A procedure that authors or reconciles a companion orientation doc for a source-code file that was
  just created or substantially changed — a short sidecar `.md` (matched to whatever doc convention the
  repo already uses; a sidecar `<file>.md` next to the source if there is none) covering the file's role
  in the system, its public surface / entry points, what it depends on and what depends on it, and the
  non-obvious gotchas a reader cannot infer from the code. It is complementary to inline comments —
  comments carry the local "why" at the point of surprise, this doc carries file-level orientation — and
  it deliberately does not restate the code line by line. Two modes. Author (no doc yet — read the file,
  trace its callers and callees, fill the template, flag what cannot be determined instead of inventing
  it). Reconcile (a doc already exists — diff its claims against the current file, list the stale entry
  points / dependencies / gotchas / role drift, propose a patch, do not silently rewrite). Use when the
  user says "document the file(s) I just added", "write an orientation doc for this file", "add a
  companion doc for `parser.ts`", "I created these files, document them", "does this new module have
  docs", "the doc for this file is stale", "check `foo.md` still matches `foo.ts`", or finishes a chunk
  of new files and wants each one documented. Needs a concrete file path, not "the stuff I changed".
  NOT `explaining-my-work` (that renders completed work into words for a human audience — a post, a
  spoken script, a summary, a resume line; this writes a standing in-repo reference for a developer
  reading the code). NOT `system-design-communication` (live out-loud rehearsal, no written artifact).
  NOT `Documents/document-page-check` (an integrity pre-flight on a paginated PDF/EPUB being consumed;
  this produces a doc about source code — opposite direction). NOT `spec-drift-gate` (a spec written
  before a multi-file build and audited as it goes — forward-looking intent; this describes a file that
  already exists now). NOT `session-handoff` (an ephemeral end-of-session context dump with next steps;
  this is a durable per-file reference with none — and when a session is being wrapped up, stay out
  entirely rather than stacking a per-file-doc step onto the handoff, even if new source files were
  created this session). NOT `change-surface-audit` (reasons about what a change breaks elsewhere; this
  describes the changed file itself and traces no blast radius). NOT `commit-and-push` (a commit message
  from the diff — a VCS log entry about a change, not a standing doc about a file). NOT
  `problem-solving-gates` (Knowledge Checker) or `learning-gate` — "explain how this module works so I
  can check my understanding", "write up how X works so I can see if I got it" is a learning rep the
  user states first and Claude gap-checks; this writes a standing in-repo reference about a file the
  user just created or changed, never a study aid and never a stand-in for that rep. A bare conceptual
  question — "sidecar docs vs header comments", "how should I document files" — is answered directly, no
  procedure.
---

# Codebase File Orientation

A new source file lands in a repo carrying everything about *how* it works and almost nothing about
*where it sits*: which job it owns, what reaches for it, what it will break if its surface moves, the
constraint that isn't visible from any single line. The next person to open it — or the same person in
six months — reconstructs all of that by reading the whole file and grepping the tree. This procedure
writes that orientation down once, as a short companion doc, and later checks that the doc still matches
the file.

It is a **procedure, not a gate** — it needs a concrete file path and enough of the surrounding code to
trace edges, and then it does the work. It withholds no judgement.

It does **not** replace inline comments. The two carry different things:

| Inline comment | Orientation doc |
|---|---|
| Local "why" at the exact line — the rejected alternative, the upstream-bug workaround, the non-obvious invariant | File-level "where" — the one job this file owns, its public surface, its edges, its cross-file constraints |
| Moves in the same diff as the line it explains | Lives beside the file; Reconcile mode keeps it honest |
| Answers a question asked mid-function | Answers "what am I looking at and what touches it" before the reader dives in |

Writing this doc is not a licence to delete the "why" comments — they are the part no generator can
reconstruct.

## When to use

- The user **created one or more source files** this session and wants them documented — often just
  before committing.
- "**Write / add an orientation doc** (or companion doc, or file README) for `<path>`."
- A file was **substantially changed** — new public surface, a role that widened — and its existing doc
  is now behind.
- "**Does `<path>` still match its doc**" / "the doc for this file is out of date" / "reconcile the
  file docs with the code."

## Out of scope — hand these off

- **Turning completed work into words for a person** — a LinkedIn post, a spoken script, a standup
  update, a resume line — is `explaining-my-work`. That renders *what you did* for a human audience;
  this writes a *standing reference about one file's structure* for a developer reading the code.
- **Practising explaining a design out loud** is `system-design-communication` — a live back-and-forth,
  no written artifact.
- **An integrity check on a PDF or EPUB before Claude reads it** is `Documents/document-page-check` —
  that inspects a paginated document being *consumed*; this *emits* a markdown doc *about source code*.
- **A spec written before a multi-file build**, then audited as the build drifts, is `spec-drift-gate`.
  That is forward-looking intent for work not done yet; this describes a file that already exists.
- **An end-of-session context dump** so work resumes later is `session-handoff` — ephemeral,
  whole-session, next-steps-oriented. This doc is durable, single-file, and has no "next steps".
- **Reasoning about what a change breaks elsewhere** in the system is `change-surface-audit`. This
  documents the changed file *itself*; it traces no blast radius and classifies nothing as breaking.
- **The commit message for the change** is `commit-and-push`. That is a VCS log entry about a diff;
  this is a doc about a file that outlives the diff. They compose — document the new files, then commit
  (doc included).
- **"Explain how this works so I can check I understood it"** is `problem-solving-gates` (Knowledge
  Checker) — the user states their mental model first and Claude gap-checks it. This skill writes a
  reference *for other readers* about a file the user *authored or changed*; it is never a study aid and
  must not pre-empt that rep even when the request names one file.
- **A bare conceptual question** — "sidecar docs vs header comments", "is per-file documentation even
  worth it" — answered directly, no procedure.

---

## Inputs the procedure needs

1. **A concrete file path** (or a short list of them). "The files I touched" is not an input — resolve
   it to paths first, from `git status` / the session's edits if needed, and confirm the list.
2. **Access to the surrounding code** — the repo, or at least the module — so imports, exports, and
   callers can actually be traced. If only the file in isolation is available, say so; the "depends on"
   section will be partial and flagged as such.
3. **For Reconcile:** the existing doc's path (auto-detected from the convention if not given).

If a path is missing or ambiguous, ask and stop. If it is *also* unclear whether the user wants this
per-file doc versus a commit message or a prose summary, that ambiguity is `ambiguity-gate`'s single
question, not a second one from here.

---

## The procedure

Work `orientation-doc-format.md` alongside these steps — it holds the field-by-field template, the
"belongs in the doc / belongs in a comment / belongs nowhere" rubric, and the Reconcile checklist.

### 1. Pick the mode

- A doc for this file **already exists** (see step 2 for where to look) → **Reconcile**.
- **No doc exists** → **Author**.
- The user named the mode explicitly → honour it.

### 2. Detect the repo's doc convention

Before writing anything, look for how this repo already documents files, in this order, and **match the
first one you find**:

1. **Sidecar next to source** — a `*.md`, `*.README.md`, or `*.doc.md` sitting beside `.ts` / `.py` /
   `.go` / … files in this directory or its siblings.
2. **A `docs/` mirror tree** — `docs/<same/path/as/source>.md`.
3. **A central index** — `docs/FILES.md`, `ARCHITECTURE.md`, or similar with one section per file.
4. **Header banners** — a structured `@file` / `Module:` / `Purpose:` block at the top of sibling
   source files.

If none is found, **default to a sidecar `<file>.md` next to the source**. State which convention you
detected (or that you are defaulting) and where the doc will go, in one line, before writing.

### 3a. Author

1. **Read the whole file.** Identify the single job it owns — not a paraphrase of its first function.
2. **Trace the surface out** — every export, the CLI command / route / subscription it registers, the
   public types. This is "entry points".
3. **Trace the edges** — imports that matter, services / tables / queues / env vars / files it touches,
   and (grep the tree) the callers that would break if its surface changed. This is "depends on".
4. **Find the gotchas** — ordering constraints, mutated globals, swallowed errors, a value that must
   stay in lockstep with another file, a workaround for an upstream bug. If there are genuinely none,
   write none; do not pad.
5. **Fill the template** from `orientation-doc-format.md`. Anything you could not determine from the
   code available (a caller you can't see, an env var whose origin is unclear) goes in the doc as an
   explicit `TODO(author): …` line — **never invent an answer to fill a field**.
6. Write the doc at the path from step 2. If step 5 produced any `TODO(author)` lines, list them back
   to the user.

### 3b. Reconcile

1. **Load the existing doc and the current file.**
2. **Walk each section** against the file, using the Reconcile checklist in `orientation-doc-format.md`:
   - **Role** — still accurate, or has the file taken on a second job?
   - **Entry points** — every listed export still exists with that signature; every new public symbol
     is listed.
   - **Depends on** — listed dependencies still imported/used; new ones added; removed ones deleted
     from the doc.
   - **Gotchas** — each still true (a "must call `init()` first" that is no longer required is stale);
     any new one.
   - **Keep in sync** — the named counterpart files still exist and still coupled.
3. **Emit the drift report** (shape below). Propose the patched doc or the specific edits.
4. **Do not apply the patch silently** — show it, let the user confirm. Applying it is the next step,
   not part of this one.

---

## Output

**Author** — a doc file written at the detected/defaulted path, plus a one-line note of where it went
and any `TODO(author)` lines that need the user.

**Reconcile** — this block, then the proposed patch:

```
Doc:     <path/to/file.md>   vs   <path/to/source>
Checked: <mtime / last doc-touching commit of each>
Role:    <unchanged | drifted — was "<x>", file now also "<y>">
Stale:
  - Entry points: <doc lists `parseSync`; file exports `parse` (async) only>
  - Depends on:   <doc omits `./cache`; lists `./legacy-fs`, which is gone>
  - Gotchas:      <"call init() first" — untrue since <commit/date>, init is automatic>
  - Keep in sync: <names `schema.ts`; that file was split into `schema/`>
New (missing from doc):
  - <exported `flush()` added, not documented>
Verdict: <doc is current | doc needs the patch below>
```

Then stop. Applying the patch, and committing it, are separate started steps.

---

## Offering it unprompted

When this session has **created new source files** and the user moves to commit them, offer once to
author orientation docs for the ones that have none — then drop it if declined. Never block or delay
the commit for this.

---

## Example invocations

> "I just added `src/pricing/discount-engine.ts` and `src/pricing/rules.ts` — document them."

Author mode, two files. Detect the convention (say the repo already has `src/pricing/index.md` beside
the code → sidecar convention → write `discount-engine.md` and `rules.md` there). For each: the job it
owns, its exports, what it imports and what calls it, the gotchas. Flag anything untraceable as
`TODO(author)`. Report the two paths written.

> "Does `parser.md` still match `parser.ts`? I reworked the export surface."

Reconcile mode. Diff the doc's Entry points / Depends on / Gotchas / Role against the current file,
emit the drift block, propose the patched doc, wait for confirmation before writing it.

> "Help me write up what I built this sprint for my manager."

Not this skill — `explaining-my-work`. That renders completed work for a human audience; this writes an
in-repo structural reference for someone reading the code.

> "What could removing `discount-engine.ts` break?"

Not this skill — `change-surface-audit`. That traces blast radius across the system; this only describes
a file that exists.

> "Should we document files with sidecar `.md` or header comments?"

A bare conceptual question — answer it directly (trade-offs: drift risk vs. file noise, tooling, review
locality), no procedure.

---

## Portability

Repo-agnostic. Reads source and writes one `.md` per file at the repo's detected doc convention (or a
sidecar beside the source). Touches no fixed `docs/` path of its own. Copy the directory into another
repo's `.claude/skills/`. See `README.md` for where it sits among the siblings.

```
cp -r ".claude/skills/Documents/codebase-file-orientation" /path/to/other-repo/.claude/skills/
```
