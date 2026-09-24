# Concept Learning (State S0)

For when the user has no prior exposure and asks what something is or how it works. This is the one learning path `learning-gate` owns end to end rather than delegating.

The rule: **teach, but do not stop at the explanation.** An explanation the user reads and nods at is not a learning rep. The rep is producing something back.

## Sequence

1. **Intuitive explanation** — the core idea in plain language, no jargon-first. One or two sentences of "what problem does this solve / what does it let you do".
2. **Concrete example** — one worked example in a context the user knows. Real code or a real scenario, not a metaphor unless the metaphor is load-bearing.
3. **Contrast with a neighbor** — the nearest related concept it gets confused with, and the line between them (DI vs. service locator; index vs. constraint; process vs. thread; mock vs. stub).
4. **Small scenario** — hand them a situation and ask what applies / what would happen. This is the first rep.
5. **Retrieval question** — one question they answer from memory, not by re-reading what you just wrote. "In your own words, why would you reach for this?" or "what breaks if you don't have it?".

Stop after 4–5 and wait for their answer. Don't pre-empt it with "you might say…".

## Calibration

- Keep steps 1–3 short. The value is in 4–5. A long lecture followed by "any questions?" is the anti-pattern.
- If their answer to 4 or 5 has a gap, point at the gap with a question (`problem-solving-gates` discipline), don't fill it in.
- If they nail 4 and 5, say so plainly and move on — don't invent a harder question to keep them in the chair.
- If they ask a genuine follow-up that needs another concept, that's a new S0 loop, not a reason to abandon the rep.

## What this is not

- Not for S1 ("I think I know it") — that's Knowledge Checker, test the model instead.
- Not for reference lookups — if they know the concept and want the syntax, just answer.
- Not a place to manufacture difficulty. If two sentences and an example genuinely settle it, one retrieval question is enough.
