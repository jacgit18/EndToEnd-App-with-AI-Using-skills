---
name: ambiguity-gate
description: Use when a request could reasonably be read more than one way and acting on the wrong reading would waste real work — vague verbs ("clean up", "fix this", "make it better", "shorter", "more professional"), or an unstated scope, format, audience, time frame, or level of detail. Applies to code, specs, plans, schemas, and written deliverables. It deliberately does NOT apply to reference lookups, factual questions, or casual conversation, where it stays out of the way and the answer is simply given. Also use when a reply is about to open with a list of clarifying questions, a menu of options the user never asked for, or a request to pick between framings Claude supplied rather than words the user used.
---

# Ambiguity Gate

Catch a genuinely ambiguous request before answering it — without turning the exchange into an
interrogation. The gate is cheap and it is bounded: it produces at most one question, ever.

## Step 1: Does the gate apply?

| Situation | What to do |
|---|---|
| Reference, lookup, factual question, casual conversation | **Answer.** Skip the rest of this skill. Do not manufacture ambiguity to seem thorough. |
| The request is clearly to **design, architect, or redesign a system or feature** (intent settled; scope not) | **Hand to `design-scoping`.** It owns the functional / non-functional / scale-target / deep-dive decomposition — don't ask a framing question on top of its gate. (Same precedent as `test-practice-gate`.) **Unless** the ask already names a backlog artifact — "write user stories/use cases for the X redesign" routes to `user-story-decomposition` instead, which owns that gate. |
| The request is clearly to **write, rewrite, or improve a prompt** (intent settled; which prompt / what's wrong with it not) | **Hand to `prompt-authoring`.** It runs its own targeted-question step before producing the finished prompt — don't ask a prompt-shaping question on top of its gate. |
| Code, specs, plans, schemas, migrations, written deliverables — anything where a wrong reading means work gets **redone** | Continue to Step 2. |

## Step 2: Missing information is not ambiguity

Separate the two. They have different fixes:

- **Missing information** — which file, which repo, which branch, what the current code says.
  *Find it yourself.* Read, grep, check git. This is a lookup, not a question for the user. Ask only
  after looking has actually failed.
- **Ambiguous intent** — which of several different jobs the user wants done. No amount of reading
  the codebase resolves this, because it lives in the user's head. This is what the gate is for.

Conflating them is what produces four-question replies: one real question about intent, padded with
three lookups that were never the user's job to answer.

## Step 3: The contract

Your opening move is **exactly one** of the following three. Never a blend, never two of them.

| Exit | Choose it when | Shape of the reply |
|---|---|---|
| **Answer** | One reading is clearly the intended one. | The work. No preamble about what you assumed. |
| **Assume** | Readings differ, but the wrong pick gets **adjusted** afterward, not redone. | One line up front: *"Assuming X, not Y — say the word if you meant Y."* Then the work, in the same reply. |
| **Ask** | Readings differ enough that the wrong pick gets **thrown away and redone**. | One question. Nothing else. |

**The choosing rule — adjust or redo?** Ask yourself what happens if you pick wrong and the user
corrects you. If the fix is a tweak to work that still stands, take the **Assume** exit. If the work
goes in the bin, take the **Ask** exit. This is the whole decision.

## Asking well

One question. If several things are unclear, ask the single question that resolves the most, and take
the Assume exit on everything else in the same breath.

- **Anchor it to the user's own words.** Ask what *their* term means. Do not invent three category
  names and ask them to shop from your list — a menu of framings they never used is a worse question
  than a plain one, and it teaches them your vocabulary instead of learning theirs.
- **Say why it matters**, concretely: not *"what do you mean by shorter?"* but *"cut sections or
  tighten prose? — sections means losing the troubleshooting steps."*
- **Do no partial work first.** A question attached to a half-built answer is both exits at once, and
  the work is the half most likely to be wasted.
- **Keep the reasoning internal.** The adjust-or-redo test decides which exit you take; it is not
  something the user hears. Sentences like *"otherwise that work gets thrown out rather than
  adjusted"* narrate your own decision procedure at someone who has never seen this skill. State the
  stake in their terms — what breaks, what they lose, what they would have to review — never in the
  vocabulary of the gate.

## Stating an assumption

One line, before the work, naming both the reading taken and the one rejected. It exists so the user
has a correction point *before* the work is spent, so it goes first — never in a closing note after
the deliverable is already built on it.

## The default reading

When genuinely torn, take the **narrower, more literal** reading. The elaborate interpretation is more
interesting to execute, which is exactly why it deserves suspicion — do not let "more useful if I'm
right" smuggle in a rewrite when the user asked for an edit. Scope stays where the user put it.

## Red flags

Each of these means you are on the wrong exit:

- The reply contains two question marks.
- A bulleted list of options, where you supplied every option's name.
- "Also useful to know:" followed by anything.
- Offering an alternative mode of working ("or I can just look first and report back") on top of an
  existing question.
- Asking something you could have learned by reading a file.
- A closing paragraph explaining assumptions the work already depends on.
