---
name: context-promotion
description: Finds stable constraints and preferences in your prompts or recent prompt logs, proposes a rules file or CLAUDE.md, a spec, or memory, writes only after you confirm, and gives the short @reference for next time. Use for "add this to my CLAUDE.md", "I keep repeating this", "put that in the spec". Not `session-handoff`, `spec-drift-gate` (new spec), `prompt-archive`, or a one-off "remember X".
---

# Context Promotion

A prompt that re-explains the same background every session is a rule or spec that has not been written yet. This skill finds the stable parts, decides where each one belongs, and writes it down once — after the user approves — so the next prompt can say `@path` instead of pasting the blob again. It is a **procedure with one confirmation stop**, not a gate: it withholds nothing except the write.

## When to use

- The user says "add this to my CLAUDE.md", "I keep repeating this", "put that in the spec", "make this a rule", "stop me re-explaining this", or asks where a piece of context should live.
- You notice the same background, constraint or preference restated across prompts or pasted at the top of a long prompt — offer once, in one line ("Want me to promote that into a rules file so you can stop pasting it?"). Do not offer twice in a session.

## Out of scope — route these instead

- **Context needed to resume unfinished work** (state, files touched, next steps) → `session-handoff`. That is ephemeral; this skill is for what stays true.
- **Drafting a spec for a new multi-file build from scratch** → `spec-drift-gate`. This skill adds to a spec or rule that exists.
- **A judgment call with a prediction and a review date** → `decision-journal`. **The prompt text itself, kept for reuse** → `prompt-archive`.
- **A plain "remember that I prefer X"** → just save it to memory; the skill adds nothing when the destination is not in doubt.
- **Generating a CLAUDE.md from the codebase** → the built-in `init`. **Settings, hooks, permissions** → `update-config`.
- **One-off instructions** ("this time, do X") are not promoted. Say so.

## Step 1 — Find the candidates

Sources, in order: the prompt in front of you; if the user asks about repeats or says "look at my recent prompts", the newest few files in `.claude/_Prompts/logs/YYYY-MM-DD.md` (local, gitignored, the user's own prompts). Read the logs only to find statements that recur; never quote them at length, and skip anything that looks like a secret, token, credential or private personal data. If no logs exist or nothing recurs, say so and work from the current prompt only. List each candidate as one line: the statement in the user's words, whether it appeared once or repeatedly, and its type (rule, requirement, preference, fact).

## Step 2 — Filter: promote only what is stable

Keep a candidate only if it is (a) true beyond this task, (b) not derivable from the code or git history, and (c) not already written down. Check (c) before proposing: grep `.claude/rules/`, any `CLAUDE.md`, the spec, and the memory index for the substance. If it already exists, say where and drop that item. If it **contradicts** an existing decision (a rule, an ADR, a memory), do not write it: flag the conflict, quote both, and ask which one wins — the new statement may belong to a different project or service. If a statement names a module or service and you cannot tell whether it is project-wide or feature-scoped, ask one question instead of guessing. Skip: task state, one-off instructions, guesses, and anything the user did not actually say. Never invent a rule; if you paraphrase, say so.

## Step 3 — Pick the destination

Read `destinations.md` for the decision table, entry formats and this repo's specifics. In short: a standing instruction for every session on this project → a rules file (or one line in `CLAUDE.md` if tiny); a requirement scoped to one feature or build → that feature's spec; a fact about the person or how they like to work → memory. One line of reasoning per item. A feature requirement with **no spec and no build to spec** goes to a small topic rules file (`.claude/rules/<feature>.md`) or memory — or is dropped — never to a spec you invent; ask the user for the spec path if they have one.

## Step 4 — Confirm, then write (the gate)

Show the exact text to add and the exact file, all in one batch. **Do not write until the user approves** — "all", "1 and 3", or "no" is enough. Keep each entry short: the rule, why it exists, how to apply it (about four lines); never paste the original blob. Append to the relevant existing file or section instead of creating a near-duplicate. After writing, re-read the changed section to confirm it landed. Memory entries follow the memory file format and get their index line.

## Step 5 — Hand back the reference

Tell the user what to say next time: for a rules file or `CLAUDE.md`, nothing (auto-loaded); for a spec, `work on X per @path/to/spec.md`; for memory, nothing. Say which prompt text can now be deleted.

## Never

- Write to `CLAUDE.md`, a rules file, a spec or memory without the Step 4 confirmation.
- Store secrets, credentials, tokens, private personal data or another person's details.
- Promote task state or a transient instruction, or turn a stated preference into a broader rule than the user gave.
- Read prompt logs for anything but recurring statements.

## Escape hatch

"Just put it in CLAUDE.md" → skip the destination discussion, still show the text and placement once. The write confirmation is the single stop.

## Example invocations

> "I keep pasting 'Postgres, no ORMs, tests first, small PRs' at the top of every prompt — put it somewhere."

Fires. Three stable rules, none written yet → rules file `.claude/rules/stack.md`, show the text, confirm, write, tell them the paragraph can go.

> "Add the retry-limit decision to the invoicing spec."

Fires. Destination is the existing spec; show the line and placement, confirm, write.

> "Put 'no ORMs, raw SQL only' in my rules" — while an ADR in the repo chose an ORM.

Fires, but stops at the conflict: quotes the ADR and the new rule, asks which wins (or whether the rule belongs to a different service), and writes nothing until answered.

> "Summarize where we are so I can continue tomorrow."

Does not fire → `session-handoff`. Likewise "write a spec for the invoicing service" → `spec-drift-gate`, and "remember that I like short answers" → save to memory directly.

## Portability

Repo-agnostic except the paths in `destinations.md` (`.claude/rules/`, `.claude/_Prompts/logs/`, the memory index). Copy the `context-promotion/` directory into another repo's `.claude/skills/` and adjust those paths.
