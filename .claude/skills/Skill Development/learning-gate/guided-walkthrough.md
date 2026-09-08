# Guided walkthrough

The delivery protocol for when intent is **learning**, the state is **S0–S2**, and the rep is a
multi-step task the user is going to perform themselves — "walk me through doing X", "give me the
exact steps", setting something up, wiring two tools together, a procedure they'll repeat. The
point is that they can do it again without you, so they make every move; you map and verify.

Operate at the assistance level Step 4 set. This is *how* you run levels 2–4 on a procedure — it
doesn't lift the ceiling.

## Core rule

Map the whole path first. Then coach one step at a time. Don't reveal or start the next step
until the current one is done and the user understands it. A beginner who sees every step at once
freezes; one who finishes a step and feels it work keeps going. If you've put more than one step
in front of them, pull back to one.

They do the work — even where you could finish it yourself in seconds. Show the exact move and
let them make it.

If instead the user wants Claude to write the code and only owns the *understanding* — a
multi-file build they follow file by file, not a procedure they run keystroke by keystroke —
that's `incremental-build-pacing`, not this file.

## Phase 0 — pin the goal and the starting point

Two things, one question at a time (not a wall):

1. The real finish line, in their words. People name a tool when they mean an outcome — dig until
   it's concrete.
2. What they already have and know: which tools or surface, what they've tried, what's on their
   machine that matters here.

If the goal is already clear, skip to the map.

## Phase 1 — map the path

A short numbered checklist, milestones in plain words. Write it to a file when you can (named for
the goal, updated live); otherwise keep it in chat and repaste the updated version as steps
close.

```
# Goal: [their words]
Starting point: [what they have now]

- [ ] 1. [step]
- [ ] 2. [step]

Notes: [one line per step on what they learned, added as you go]
```

Show the whole map once, say how many steps it is and where the real work sits, then say you'll
go one at a time. Keep the count honest — don't shrink it to look easy or pad it to look
impressive.

## Phase 2 — one step at a time

Present each step in this shape:

```
Step [n] of [total]: [what they're doing, one line]
Why: [what it's for, what it sets up next]
Do this:
1. [exact action]
2. [exact action, with any text to paste in a code block]
You'll know it worked when: [what they should see]
When that's done, come back and [show me X / paste Y].
```

Then the loop:

- **Stop and wait.** Don't narrate the next step or assume it worked. The turn is theirs.
- **Verify it's really done.** Check when you can — open the file, read what got produced, confirm
  the thing exists. If it happened elsewhere, have them paste the result or describe exactly
  what's on screen. Catch a problem here, not three steps later.
- **Check they get it.** Have them say back what they did and why. Test two layers: do they
  understand why the step mattered, and could they redo or adjust it if something changed. If they
  only parrot the clicks, ask another "why". Use `AskUserQuestion` for a checkpoint quiz before a
  step that builds on this one — one good question about the step they just did, correct answer's
  position varied, answer not revealed until they submit.
- **If stuck or wrong, stay on this step.** Try a smaller sub-step or a simpler version. One step
  done right beats five done halfway.
- **Then close the step.** Check the box, add a one-line note of what they learned, and only now
  reveal the next step.

Name the one thing that usually goes wrong on a step, so they catch it coming.

## Coaching register

- Define any word that isn't everyday English the first time you use it.
- Show, don't describe: the exact thing to click, the exact words to type, the exact text to
  paste in a code block.
- Never call a step obvious. If it has three sub-actions, write all three.
- On request, drop to eli5 / eli14 / eli-intern and match the level asked for.

Prose style itself — sentence length, banned words, no "not X but Y" reframes — is
`delete-ai-words`' job, not this file's.

## Ending

End only when both are true: the result exists and you've seen it work, and the user could do it
again without you. Understanding the idea alone isn't done. Show the finished checklist with every
box ticked and their notes, say in one line what they can now do that they couldn't before, and
stop.

If time runs out first, save the checklist with their place marked and the exact next step.
