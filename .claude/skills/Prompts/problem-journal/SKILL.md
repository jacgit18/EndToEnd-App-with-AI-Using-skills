---
name: problem-journal
description: Two modes, picked by what's being asked for. Mode Capture — the moment an error/exception/stack trace appears, whether or not it's resolved yet, save it verbatim as its own file in `Finance/Error Log/` using the vault's existing `Language Error.md` template (Error Details, Steps to Reproduce, Expected/Actual Behavior, Environment, Error Messages, Resolution Steps) — "log this error", "save this error", "capture this". Mode Journal — after a coding problem is resolved and the user wants a learning-worthiness read — "log this problem", "was that worth learning from", "have I hit this before" — write a curated entry to `.claude/_Prompts/problems-log.md`: symptom/cause/fix, a recurrence count grepped from BOTH the prompt-archive logs (`.claude/_Prompts/logs/*.md`) and the `Finance/Error Log/` files (a far more precise signal, since it holds the actual error text, not just what the user typed), a classification (recurring pattern vs. one-off; fundamental concept vs. environmental fluke), and a worth-learning verdict tied to that count — never asserted without it, the same discipline `technical-cost-decision` forces for dollar figures. Neither mode is a live gate: Capture is mechanical recording (like `prompt-archive`'s Log mode, for errors instead of prompts), and Journal is a retrospective procedure that runs *after* a problem is already resolved. Neither replaces `learning-gate` (which sets how much help Claude gives on the *current, live* request) or `problem-solving-gates`' Rubber Duck (which forces the hypothesis *during* the debugging itself — this skill assumes that already happened, however it happened, and records the before/after). Once a Journal entry's verdict is "worth learning," this skill names the next step and hands it off — it does not teach the concept itself; that's `learning-gate` (S0, teach the minimum) or `problem-solving-gates`' Knowledge Checker (verify after self-study). Not for archiving a reusable prompt or logging a session's raw prompts verbatim — that's `prompt-archive`, whose dated logs this skill's Journal mode reads as one recurrence-search corpus but never writes into. Not for evaluating whether a prompt performs well — that's `prompt-tester`.
---

# Problem Journal

An error appears and either gets fixed in the next five minutes or eats an hour — and either
way, nothing records it unless someone stops to write it down. This skill has two jobs, kept
deliberately separate: **capture** the error the moment it happens, no judgment attached; and
**journal** it once resolved, with an actual recurrence count behind any claim that it's worth
learning from. Capture never guesses a verdict. Journal never guesses a resolution.

| Ask | Mode |
|---|---|
| "log/save/capture this error", an error just appeared and is worth keeping a record of (resolved or not) | **Capture** — one file in `Finance/Error Log/` |
| "log this problem", "was that worth learning from", "have I hit this before" — after a fix | **Journal** — one entry in `.claude/_Prompts/problems-log.md` |

If the ask is ambiguous, ask which one in a single line. Don't run both unless asked — though
the natural chain (capture while debugging, journal once fixed) is common and covered below.

---

## Out of scope — hand these off

- **How much help Claude gives on the *current* request** — `learning-gate`. Neither mode
  decides live assistance level.
- **Forcing the hypothesis during an active debugging session** — `problem-solving-gates`
  (Rubber Duck). Capture mode can run *alongside* an active debug (it's just recording the
  error as it stands right now); it does not substitute for forming a hypothesis, and Journal
  mode still requires the problem to be actually resolved before it runs. If the user has
  stated a hypothesis that Rubber Duck hasn't confirmed yet, Capture mode records it labeled
  explicitly as **unconfirmed** (e.g. under Additional Notes: "user's working hypothesis,
  not yet confirmed: ...") — never as a stated root cause. Writing an unconfirmed guess into
  the file as if settled is the same diagnosis-leak Rubber Duck's gate exists to prevent,
  just moved from chat into a written artifact.
- **Teaching the flagged concept** — once a Journal verdict is "worth learning," name the next
  step (`learning-gate` S0, or `problem-solving-gates`' Knowledge Checker) and stop. Don't
  teach it inline in the same turn.
- **Archiving a reusable prompt, or logging a session's raw prompts verbatim** —
  `prompt-archive`. Journal mode reads that skill's dated logs as one recurrence-search
  corpus, but writes a different, curated artifact, and Capture mode writes yet another
  (an error file, not a prompt).
- **Evaluating whether a prompt performs well** — `prompt-tester`. Unrelated.
- **Screenshots or non-text attachments** — the template has a slot for them; leave it as
  `N/A (text-only session)` rather than fabricating a description of an image that wasn't
  provided.

---

## Mode: Capture a raw error

Use the moment an error, exception, or stack trace appears and is worth a record — whether
or not it's fixed yet. This is mechanical: no recurrence check, no learning verdict, just an
accurate record of what happened.

### 1. Get the error text

Use the actual error message / stack trace / exception verbatim — do not paraphrase or
summarize it away. If it's long, keep the parts that identify it (exception type, the
top few frames, the failing assertion) rather than truncating to a vague description.

### 2. Decide the filename

Title Case, describing the error, `.md` extension, placed directly in `Finance/Error Log/`
(matching the existing `Language Error.md` file already there) — e.g. `Stale Cache Read On
Deploy.md`. Create a subfolder only if a clearly distinct topic cluster forms; don't
subfolder for a single file. Check for a name collision first; if one exists, ask whether to
append under a new heading or use a distinct filename.

### 3. Write the file

Use the vault's own template (`Finance/Error Log/Language Error.md`) exactly — same sections,
same order. Fill only what's actually known; leave the template's bracketed placeholders
untouched for anything not known. Don't invent a reproduction step, an environment detail, or
a root cause that wasn't stated or observed.

```markdown
---
tags:
  - error
author:
  - jacgit18
Description: "<one-sentence description>"
Comments:
Purpose: This documentation discusses this error in this context.
Status: Capture
Started:
EditDate: <today, YYYY-MM-DD>
Relates:
Peer Reviewed:
dg-publish:
---
## Error Details
```dataviewjs
const { Description } = dv.current();

dv.header(3, "Description");
dv.paragraph(
  `${Description}`,
);
```

### Steps to Reproduce

1. `[Step 1]`

### Expected Behavior

`[Describe what the expected behavior should be.]`

### Actual Behavior

`[Describe the actual behavior observed during the error.]`

## Environment

- Operating System: `[Enter OS or Environment]`
- Software Version: `[Enter Software Version]`
- Relevant Settings/Configuration: `[Specify any relevant settings or configuration]`

## Error Messages

<the actual error text/stack trace, verbatim>

## Screenshots

N/A (text-only session)

## Additional Notes

`[Add any additional notes or context that might be helpful.]`

## Resolution Steps

`[Document steps taken or proposed resolutions.]` — leave as-is if not yet resolved.

## Related Issues/References

`[Link to any related issues or external references.]`
```

- `Status` — `Capture` while unresolved; update to `Resolved` in place once the fix lands
  (don't create a second file for the same error).
- Steps to Reproduce / Environment — fill in only what's actually known; a single known step
  is fine, don't pad the list to look complete.
- Resolution Steps — fill in if the fix is already known at capture time; otherwise leave the
  placeholder. This is not where a learning verdict goes — that's Journal mode.

### 4. Index it

Append a row to `Finance/Error Log/INDEX.md` (create with an `# Error Log Index` heading and
a table header if absent):

```markdown
| Date | Error | Status | File |
|---|---|---|---|
| 2026-09-05 | Stale cache read after deploy | Capture | [Stale Cache Read On Deploy](Stale%20Cache%20Read%20On%20Deploy.md) |
```

### 5. Report

One line: the path written and that it was indexed. Don't dump the file contents back.

---

## Mode: Journal a resolved problem

Use after a coding problem (a bug, an unexpected error, a "why doesn't this work") gets
resolved and the user wants a learning-worthiness read.

### What counts as a problem

A bug, an unexpected error, a "why doesn't this work," a debugging session, a misunderstood
API/library behavior. **Not** a routine feature request, a style preference, or a design
decision — those aren't problems in this sense, even if they took a while to work through.
If it's unclear whether something qualifies, ask in one line rather than journaling a
feature build as if it were a bug.

### The gate

Two things must come from the actual record, not be invented:

1. **The problem itself** — symptom, root cause (if known), and the fix. Source this from
   **the current session's actual resolved context** whenever the problem was just worked
   through in this conversation — that's the only place the *resolution* is reliably known.
   If a matching `Finance/Error Log/` Capture-mode file exists for this problem, use it and
   update it (see "Closing the loop" below) rather than starting from nothing. If asked to
   journal a problem from an **old session** with no Capture file and no resolution in the
   record, do not reconstruct the fix from guesswork — ask the user to state what the problem
   and fix actually were.
2. **The recurrence count** — grep **both** `.claude/_Prompts/logs/*.md` (prompt-archive's
   raw prompt logs — a weak signal, since it only ever has what the user typed) **and**
   `Finance/Error Log/*.md` (the `Error Messages` and `Description` fields — a much stronger
   signal, since it holds the actual error text) for the error signature, the concept name,
   or a close paraphrase. Report the actual count and which files it appeared in — "3 hits:
   2 in `Finance/Error Log/` (`X.md`, `Y.md`), 1 phrasing match in
   `.claude/_Prompts/logs/2026-08-29.md`" — never "this comes up a lot" without having
   actually searched both.

### Classifying and judging

With the problem and the count in hand:

- **Recurring pattern (2+ hits of the same shape) vs. one-off.** A pattern is not "you asked
  about databases three times" — it's the same *kind* of mistake or gap (an off-by-one, a
  missed `await`, a misunderstood cache-invalidation rule) showing up across otherwise
  unrelated tasks.
- **Fundamental concept vs. environmental fluke.** A misunderstood language/library semantic
  recurs because the gap in understanding is still there. A broken dependency version or a
  typo doesn't recur in any meaningful sense even if superficially similar errors appear —
  don't count coincidental error-message similarity as a pattern.
- **Delegated fully vs. attempted first**, if it's known from the original exchange (e.g.
  `learning-gate` was engaged and classified the original request as execution intent, so no
  attempt was expected) — this shapes *how* the learning gap formed, not whether it exists.

**The verdict — worth a deliberate study pass, yes or no — must name which of the above
produced it.** "Worth learning: yes, this is the 3rd time (see count) this exact category of
bug has appeared, and it's a semantic gap (async/await), not an environmental fluke" is a
real verdict. "This seems like something you should probably learn" is not — go back and get
the count first.

A first-time, environmental, or trivially-explained problem gets **"not worth a dedicated
pass"** as a perfectly complete verdict — don't manufacture a lesson to seem thorough.

### Output block

```
Problem:              <symptom + root cause + fix, one or two sentences>
Source:               <this session | Finance/Error Log/<file> | user-stated (old session)>
Recurrence check:     <N hits — split by corpus: Finance/Error Log/ vs. prompt-archive logs>
                      — grepped for: <term(s) searched>
Classification:       <recurring pattern | one-off> · <fundamental concept | environmental
                      fluke> · <delegated fully | attempted first | unknown>
Worth learning?:       yes/no — <the one driving reason, tied to the count/classification>
Entry written:         .claude/_Prompts/problems-log.md
Closing the loop:     <Finance/Error Log/<file> Status updated to Resolved | no Capture file
                      existed for this one>
Next step:            <none | learning-gate (teach the minimum) | problem-solving-gates
                      Knowledge Checker (verify after self-study)>
```

### Writing the entry

Append to `.claude/_Prompts/problems-log.md` (create it with a `# Problem Journal` heading
if absent):

```markdown
## 2026-09-05 — <short problem title>

**Problem:** <symptom + root cause + fix>
**Recurrence:** <N hits — corpus breakdown, or "first occurrence">
**Classification:** <recurring/one-off> · <fundamental/environmental>
**Worth learning:** <yes/no> — <reason>
**Next step:** <as in the output block, or "none">
**Error Log file:** <Finance/Error Log/<file>, if one exists — or "none captured">
```

### Closing the loop

If a `Finance/Error Log/` file already exists for this problem (from Capture mode, or found
during the recurrence search), update it rather than leaving it stale: set `Status:
Resolved`, fill in `Resolution Steps`, and add a line under `Related Issues/References`
pointing at the new `problems-log.md` entry. If no Capture file exists, don't retroactively
invent one — the problems-log.md entry stands on its own.

Report back only the paths touched and a one-line confirmation — don't dump file contents
back into chat on top of the output block already shown.

---

## Red flags — the record isn't done

- A "worth learning: yes" (or "no") verdict with no recurrence count or classification behind
  it.
- A recurrence count that only checked one corpus (just the prompt logs, or just Error Log)
  when both were available.
- A resolution reconstructed for an old session Claude wasn't present for, instead of asking
  the user what actually happened.
- Teaching the concept in the same turn instead of naming the handoff and stopping.
- A routine feature request or style choice journaled/captured as if it were a bug.
- "This comes up a lot" with no grep actually run.
- A Capture-mode file with an invented Steps-to-Reproduce or Environment that wasn't actually
  known.
- An unconfirmed hypothesis from an active Rubber Duck session written into a Capture file
  as a stated root cause instead of labeled explicitly unconfirmed.
- A resolved problem with a stale `Finance/Error Log/` file still marked `Status: Capture`.

---

## Portability

Repo-agnostic, but assumes `.claude/_Prompts/logs/` (`prompt-archive`'s automatic hook) and a
`Finance/Error Log/` folder with the `Language Error.md` template. A backup copy of that
template lives in this skill's own `references/Language Error.md` — if
`Finance/Error Log/Language Error.md` is ever missing (e.g. the vault folder got deleted and
recreated), recreate it there from the backup copy before proceeding with Capture mode,
rather than inventing a different location or a different template. Copy the
`problem-journal/` directory into another repo's `.claude/skills/` to use it there, alongside
`prompt-archive`; the bundled `references/Language Error.md` travels with it, or point the
skill at wherever that repo's equivalent error-log convention lives.
