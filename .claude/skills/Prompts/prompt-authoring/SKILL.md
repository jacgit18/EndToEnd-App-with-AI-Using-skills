---
name: prompt-authoring
description: Use when the user wants a finished, ready-to-use prompt produced from a rough idea, a half-formed task description, or a draft they want sharpened — "write me a prompt that…", "turn this into a prompt", "rewrite / improve / optimize this prompt", "help me prompt this", "I want to ask Claude to…", or a pasted draft prompt with a request to make it better. Output is always a single copy-paste-and-send prompt in one code block, never a template with blanks to fill. The authoring half of the Prompts pipeline — this writes the prompt, `prompt-tester` checks whether it works, `prompt-archive` files a keeper. NOT for testing or judging an existing prompt (that is `prompt-tester`, which reports and does not rewrite). NOT for filing or logging a prompt (that is `prompt-archive`). NOT for resolving an ambiguous request to *act* — where the question is which of several readings the user meant before Claude does the work — that is `ambiguity-gate`; this skill resolves only the ambiguity that stops it producing a finished prompt, then produces one. Model IDs, pricing, and thinking / effort / streaming / tool-schema configuration around the prompt are `claude-api`'s domain, not text this skill bakes into the prompt body.
---

# Prompt Authoring

Turn whatever the user brings — a rough idea, a vague task, a paragraph of context, a draft that
isn't landing — into one finished prompt they can paste and run as-is.

Pipeline position: **author (this) → `prompt-tester` (does it work?) → `prompt-archive` (keep it)**.
Offer the next step; don't assume it.

## Two hard rules

These override everything else below.

### Rule 1 — No placeholders

Never hand back a prompt containing `[paste X here]`, `[your content]`, `{topic}`, `<your_input>`,
`[INSERT Y]`, `___`, or any other blank the user is expected to fill. The user copies the output,
sends it, and it works. If you catch yourself putting square brackets around a noun, stop and
rewrite — either bake the real content in (Rule 2, Case A) or make the prompt gather it (Case B).

### Rule 2 — Ship a finished prompt whatever you were given

**Case A — the user gave real content** (a draft, a list of items, real numbers, an actual
question, a document). Bake it directly into the prompt. Content and instructions both go inside
the one code block. Nothing left to assemble.

**Case B — the user described only a class of task** ("a prompt to triage my emails", "something
to review my contracts"). Write a complete, self-contained instruction that works on its own, and
end it by having the prompt itself collect what it needs — "Before drafting, ask me for the
product name, the audience, and one example" — or define a sensible default for a missing input.
The user still copies and sends one finished thing.

## Step 1 — Read what you were given, pick the case

State back in one line what the prompt is for, who runs it, what it takes in, and what it should
produce. Classify A or B. If a draft was pasted, name the two or three things keeping it from
working — unstated scope, no output format, an instruction the model will read too literally or
too loosely.

## Step 2 — Ask only what changes the prompt, then write

Ask the smallest set of questions whose answers would actually change what you write — output
format, length, tone, the one example that pins down intent, a hard constraint. Batch them. Skip
anything inferable from what's already on the table.

Then stop asking and produce the prompt. This skill does not end on a list of questions — that is
`ambiguity-gate`'s move and a different job. If the user won't answer, state the assumption you're
making and write anyway.

## Step 3 — Write the prompt

- **Scope every instruction explicitly.** "Rewrite every section" not "rewrite the section"; "for
  all 12 rows" not "for the rows". The model will not generalize a one-item instruction to the
  whole set, and will not infer a step you didn't write.
- **Name the output shape when it matters** — prose vs. list vs. table, length or item count, what
  to leave out. Leave it open only when open is genuinely fine.
- **One idea per instruction.** A wall-of-text paragraph hides half its own requirements.
- **Give an example only when it disambiguates**, and say whether it's a pattern to match or just
  one case.
- **Reasoning nudge, conditionally.** If the task needs real multi-step work and the target
  surface exposes no thinking / effort control, add one explicit line telling the model to reason
  through it before answering. Don't add it to a lookup or a short transform. If the surface *does*
  expose thinking / effort config, that setting is `claude-api`, not a sentence here.

## Step 4 — Fit the surface

Ask or infer where this runs, because the shape differs:

- **Chat app** (claude.ai, desktop, mobile) — one message, no system prompt, no params. The prompt
  text carries everything, including any role framing.
- **API, or a skill / agent file** — a system prompt, tools, and parameters exist around it. Keep
  role and standing rules for that layer; the prompt body is the task. For which model, what it
  costs, or how to set thinking / effort / streaming / tool schemas, hand to `claude-api` — this
  skill writes instruction text, not configuration.

## Step 5 — Deliver

Output the finished prompt as a single fenced code block, nothing the user has to edit out. Two
lines under it: what you assumed (if anything), and the offer — "run it through `prompt-tester` on
a few inputs?" / "archive it with `prompt-archive`?".

## Out of scope

- **Judging whether a prompt works** — `prompt-tester` (it reports; it doesn't rewrite).
- **Filing or logging a prompt** — `prompt-archive`.
- **Deciding which reading of a request to act on** before doing the work — `ambiguity-gate`.
- **Model choice, pricing, API / thinking / effort configuration** — `claude-api`.
- **Building a whole skill or agent around a prompt** — a container decision; `prompt-tester`
  Step 7 makes the call, `writing-skills` builds it.
- **Teaching prompt-writing principles** — "help me get better at prompts", "teach me the
  principles" — `learning-gate`. This skill produces one finished prompt; it does not teach the
  skill of prompting.

## Before returning — check

1. No placeholders, no fill-in blanks, no `[ ]`.
2. Every instruction states its own scope.
3. Output format named wherever it matters.
4. Real content baked in (Case A), or a gathering step included (Case B).
5. One code block, copy-and-send.
