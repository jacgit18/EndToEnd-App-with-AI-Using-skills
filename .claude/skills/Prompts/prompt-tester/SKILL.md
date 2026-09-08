---
name: prompt-tester
description: This skill should be used when the user asks to "test this prompt", "does this prompt work", "try my prompt on a few examples", "check if this prompt does what it's supposed to", or pastes a prompt and asks whether it's any good. Not for writing a new prompt from scratch (that is `prompt-authoring`), and not for editing or fixing a prompt directly -- this skill reports findings, it does not rewrite. Not for merely filing or logging a prompt (that is prompt-archive) -- only use this when the ask is about whether the prompt works. It includes a built-in assessment phase that surfaces gaps and evaluates whether the prompt should stay as-is, be refined, or move to a skill/agent container.
---

# Prompt Tester

Test whether a prompt actually behaves as intended, report pass/fail findings, and assess whether
the prompt itself needs refinement or should be packaged as a skill or agent.

## When to use

- The user pastes a prompt and asks if it works, with or without supplying sample inputs.
- The user names a prompt file and asks to verify it — read the file first, then proceed.
- The user wants to know not just whether a prompt works, but whether it's in the right form
  (standalone prompt, reusable skill, iterative agent).

## Out of scope

- Do not rewrite, fix, or improve the prompt unless explicitly asked — report findings and let
  the human decide what to change.
- Do not invent success criteria the user never stated — if intent is genuinely ambiguous, ask
  before testing rather than guessing.
- Do not run tests with real destructive or irreversible side effects; use safe, simulated inputs.

## Full Workflow (4 + 4 Steps)

### Phase 1: Testing (Steps 1–4)

**Step 1 — Clarify intent and context**

Identify the target prompt's apparent intent: role/persona, task, expected inputs, output format,
and any implied success criteria. State this back briefly before testing.

**Critical**: If the prompt doesn't specify required inputs but expects them (e.g., "the situation
where I'm deliberating"), ask: "Should this prompt ask for context if the user hasn't provided it,
or assume the user will always supply it?" This determines whether the prompt is self-sufficient
or dependent on good user hygiene.

**Step 2 — Secure sample inputs**

If the user didn't supply sample inputs, generate 2–3 representative ones:
- At least one straightforward case exercising core purpose
- At least one edge case likely to expose a gap
- One "minimal input" case if the prompt has context dependencies (to test robustness)

**Step 3 — Run tests**

For each sample input, dispatch a fresh sub-instance using the target prompt verbatim plus that
input. Capture raw output.

**Step 4 — Report test results**

For each test case: input, output, verdict (pass/partial/fail), and why. Close with an overall
verdict and the 1–3 most concrete gaps.

---

### Phase 2: Assessment (Steps 5–8)

After testing, diagnose the prompt's quality and containerization using this four-step protocol.

**Step 5 — Assess the prompt itself**

Evaluate across four dimensions:

| Dimension | Questions |
|-----------|-----------|
| **Clarity** | Are role, task, and expected outputs unambiguous? Would two different people interpret this the same way? |
| **Specificity** | Does it specify output format (prose, list, structured data, length constraints)? Are examples provided? |
| **Structure** | Is there a logical step-by-step process, or is it a single paragraph? Does it handle edge cases (missing input, conflicting requests)? |
| **Consistency** | Based on test results, do multiple runs produce similar output? Or does quality depend on input richness or other unstated factors? |

List 1–3 weak spots found. Be specific: "Prompt doesn't specify output format" not "prompt is unclear."

**Step 6 — Generate targeted improvement questions**

For each weak spot from Step 5, ask *one specific question*, not generic feedback.

**Examples:**
- Weak spot: "No output format specified" → Question: "Should output be prose paragraphs, a
  numbered list, or a structured table?"
- Weak spot: "Behavior undefined when input is minimal" → Question: "If the user says 'Go ahead'
  with no context, should the prompt ask clarifying questions or provide a generic framework?"
- Weak spot: "Role boundaries vague" → Question: "When should the persona acknowledge limitations
  in-character vs. break frame to escalate?"

One or two questions per assessment. These are *for the user to answer*, not fixes to apply.

**Step 7 — Evaluate container fit**

Analyze whether this prompt should stay standalone or move to a different container. Check three
signals:

| Signal | Container | Indicator |
|--------|-----------|-----------|
| **One-off, inline, no iteration** | Stays a prompt | User gives full context once, reads output, decides. No loop. |
| **Reusable framework, static** | Becomes a skill | Same instructions/checklist would guide multiple future prompts; domain knowledge that informs many uses. |
| **Feedback loop, dynamic** | Becomes an agent | User gets output, responds/refines, system decides next step based on response. Repeats until goal met. |

If the prompt clearly lands in one category, state it. If two containers are in tension (e.g.,
"reused sometimes, but mostly one-off"), **flag as ambiguous** explicitly and ask the user which
pattern matches their intended use going forward.

**Step 8 — Recommend without implementing**

State the assessment (weak spots, targeted questions, container recommendation) and reasoning.
Stop there. No conversion or rewrite happens unless the user explicitly asks.

---

## Output Format: Full Tester Report

Structure your report as:

1. **Intent Statement** — 2–3 sentences on what the prompt aims to do
2. **Test Results Table** — Test case | Input | Output (tightly summarized) | Verdict | Why
3. **Overall Verdict** — Pass/partial/fail with summary
4. **Assessment & Recommendations** (Steps 5–8):
   - Weak spots identified (2–3, specific)
   - Targeted questions (1–2 for user to answer)
   - Container analysis (one-off vs. skill vs. agent, with reasoning)
   - Recommendation (e.g., "Refine as prompt" or "Escalate to agent if iterative use emerges")

---

## Common Patterns to Watch For

- **Input dependency**: Does output quality drop sharply if context is minimal? If yes, the prompt
  needs to specify fallback behavior.
- **Role fidelity**: Does the persona hold across runs, or does it drift/break? Test by running
  twice on the same input and comparing tone/voice.
- **Format inconsistency**: Do multiple runs produce the same structure (e.g., always a table, or
  always prose), or does it vary? Inconsistency signals underspecified output format.
- **Scope creep**: Does the prompt's stated goal match what it actually delivers, or does it
  deliver more/less? Misalignment is a signal the intent is unclear.
