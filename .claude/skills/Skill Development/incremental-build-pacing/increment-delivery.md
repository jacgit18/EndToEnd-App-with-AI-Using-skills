# Increment delivery

The per-increment protocol for when the pacing contract is set (SKILL.md Step 2) and the
increment map is agreed (Step 3). This is *how* you run the loop — it doesn't change the
increment size or cadence the user chose.

## Core rule

Map the slice first. Then deliver one increment at a time. Don't write or reveal the next
increment until the current one exists, is explained, and the user can say back what it does and
how it connects. If you've put more than one increment in front of the user in a single turn,
pull back to one.

Claude may write the code — that's the difference from `guided-walkthrough.md`, where the user
makes every move. What the user owns here is the *understanding*, verified before each advance.

## Sizing: batch vs. slow down

| Increment kind | Examples | How to deliver |
|---|---|---|
| **Plumbing** — no mental model at stake | empty `__init__.py`, `.gitignore`, lockfile, `tsconfig.json`, `postcss.config.js`, generated scaffolding, a bare `main` that just wires a router in | One "skim these" step. List them together, one line each on what each is for. No stop, no check. |
| **Structural** — shape matters, mechanism doesn't | a Pydantic schema, a plain CRUD router, a React list component, a config object read from env | One per turn or grouped into a unit. Short explanation. Light check — one "why is it shaped this way". |
| **Load-bearing** — a wrong model costs later | money / `Decimal` round-trip, JWT/auth dependency, ORM session & transaction lifecycle, a dedupe hash, dev-server proxy / CORS, an FK that forces build order, a migration hard to reverse | One per turn, always. Full explanation. `AskUserQuestion` checkpoint before anything builds on it. |

Tie-breaker: if the increment introduces a framework primitive the user hasn't met yet
(multipart `UploadFile`, a FastAPI dependency, a React context, a migration op), it's
load-bearing even if the code is short. When still unsure, treat it as load-bearing — the cost
of over-explaining one schema is a minute; the cost of the user not understanding the session
lifecycle is every bug after it.

On a slice added to an existing codebase, the plumbing row is often nearly empty — one or two
wiring lines. That's expected; don't manufacture a "skim these" step for a single `include_router`
call, just show it with the increment it belongs to.

## The loop, per increment

Present each increment in this shape:

```
Increment [n] of [total]: [file or unit, one line]
[the code — written in full, or shown for the user to type per the contract]

What it does:   [plain-language, 2–4 sentences]
Why this shape: [the decision this file embodies, tied back to the spec / ADR if there is one]
Connects to:    [what already exists that this uses or is used by]
Watch out for:  [the one thing that usually goes wrong on this kind of file]
Docs:           [link to the primary documentation for the framework primitive this increment
                introduces, if one exists — skip on plumbing or a primitive already linked]
```

The `Docs:` line matters most when the contract has the user typing the increment themselves, or
the increment is tagged load-bearing because it introduces a framework primitive they haven't met
yet (Step 3's tie-breaker) — that's the moment they're most likely to need the primary source
later, not a tutorial or blog post. Skip it on plumbing and on a primitive already linked earlier
in this slice.

Then:

- **Stop and wait.** Don't narrate the next increment. Don't assume it landed. The turn is the
  user's.
- **Verify it's real** when the user was the one typing — read back what they have, confirm it
  matches, catch a divergence now rather than three increments later. When Claude wrote it, this
  step is just confirming they've read it.
- **Check understanding.** The user says back what the increment does and how it connects — in
  their own words, not the code re-narrated. Two layers: do they get *why* it's shaped this way,
  and could they change it if a requirement shifted. If they only restate the code, ask one
  sharper "why". Before an increment that builds directly on this one, run an `AskUserQuestion`
  checkpoint: one question about the increment just delivered, the correct answer's position
  varied between calls, nothing revealed until they submit.
- **If shaky, stay on this increment.** Take a smaller sub-piece, or re-explain plainly. One
  increment understood beats five delivered.
- **If the user isn't attempting the explain-back at all** — "next" / "next step" with nothing
  said back, repeatedly — that's a different case from shaky, and the loop has no default for
  it: continuing to run the full loop is offering a check nobody is taking, but silently
  dropping it isn't a call to make unilaterally either. After a few increments of this, say so
  once, plainly, and let the user choose: keep the full loop, or lighten it (shorter
  explanations, bigger batches) without dropping pacing entirely. Don't just keep re-offering
  the same unconfirmed explanation forever, and don't stop offering it without saying you're
  doing that.
- **Close it.** Tick it on the map, add a one-line note of what the user learned, and only now
  move to the next.

Name the common failure for each load-bearing increment *before* it bites — "the trap here is
returning a `float` from this function; every caller assumes `Decimal`" lands better as a warning
than as a bug hunt later.

## Coaching register

- Define any term that isn't everyday English the first time it's used.
- Show the exact code, the exact file path, the exact command — never "add the usual imports".
- Never call an increment obvious or trivial. If it's trivial it's plumbing — batch it and move
  on; don't single it out with a dismissive aside.
- On request, drop to eli5 / eli-intern and match the level asked for.

Prose style itself — sentence length, banned words, no "not X but Y" reframes — is
`delete-ai-words`' job, not this file's.

## Keeping the map visible

Write the increment map to a file when you can (named for the slice, updated live); otherwise
keep it in chat and repaste the updated version as increments close.

If `Prompts/session-handoff` fires mid-build (a context-length nudge, or the user ending the
session), that handoff file *is* your persisted map going forward — capture the increment list
in the checklist format below, not a prose "next steps" paragraph, so a fresh session can lift
it verbatim. And on the resuming side: treat that file's list as canonical. Don't reconstruct
the map from memory of the pattern the build has been following — a plausible-sounding guess at
"what's probably next" is exactly how a real ordering slip happens (confirmed the hard way:
misnaming the next file after a reset, because the general shape of the build was remembered but
the literal list wasn't re-read).

```
# Slice: [name] — from [spec / backlog ref]
Contract: [increment size] · [cadence] · [who writes]

- [x] 1. [increment]  — note: [what the user learned]
- [ ] 2. [increment]  ← here
- [ ] 3. [increment]
- [ ]    plumbing: [file, file, file]  (skim, no check)
```

Keep the count honest — don't shrink it to look quick or pad it to look thorough.

## Ending

End only when all three hold: every file in the slice exists and runs, the user can walk the
slice end to end without looking, and the user could modify one increment without breaking its
neighbours. Understanding each file alone is not the finish line — the wiring between them is
what the slice was for.

Show the finished map with every box ticked and the notes, say in one line what the user can now
do that they couldn't before, and stop. If time runs out first, save the map with the current
place marked and the next increment spelled out.
