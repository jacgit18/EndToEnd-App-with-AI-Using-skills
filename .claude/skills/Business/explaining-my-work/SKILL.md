---
name: explaining-my-work
description: Use when work that just happened needs to become something the user can say out loud or post publicly — "help me talk about this," "turn this into a LinkedIn post," "how do I explain this to a non-technical person," "what do I say at the meetup," "write this up for my resume," "summarize what I built." Also use when preparing for an interview, standup, recruiter call, networking event, or stakeholder update, and when an existing draft needs an audience check — jargon a business reader can't parse, or vagueness a technical reader can't grab onto. This skill drafts the words — a script, talking points, a summary you can read or rehearse solo. Actually rehearsing a system-design interview live — Claude asking follow-ups, pressing on assumptions, a real back-and-forth with a debrief at the end — is `system-design-communication`, which this skill's draft can feed into rather than duplicate (draft the talking points here, then pressure-test them there). Not a standing in-repo reference about what a specific source file contains and how it fits the codebase, for the developers who read the code — concrete file paths plus "what does this file do / document this file I just added" is `codebase-file-orientation`; this skill faces a person, that one faces the codebase.
---

# Explaining My Work

Two failures, opposite directions, one cause: writing at the altitude that is comfortable to the author instead of the one the reader is standing at. To a business reader, unexplained mechanism is noise. To a technical reader, business framing with the mechanism stripped out is nothing to ask a follow-up question about.

The fix is not to write three things. It is to build **one evidence base** and render it three times — plain summary, spoken script, public post. The facts stay identical across renderings. Only the altitude changes.

## Out of scope

- **Publishing.** This skill drafts. It never posts, sends, or submits anything anywhere. The draft goes to the user; distribution is their call.
- **Self-understanding / psychology framing.** A different concern with a different standard.
- **Personal-brand voice and career-wide honesty constraints.** This skill's Evidence Block is scoped to *this piece of work* — it has no notion of the user's total years of experience, which environments were pre-prod vs. production, or a fixed brand device. When the LinkedIn Draft or resume line is going out under the user's personal brand, run it through `software-carpentier-brand` afterward for the voice pass and those career-wide checks.

---

## The one hard rule

**Every claim traces to something that actually happened in this session or in the repo.**

Not "roughly happened." Not "would plausibly have happened for work like this." Public posts and interview answers are things the user will be held to by someone who can check.

**No exceptions:**
- No invented percentages. "Reduced defects by 40%" needs a defect count from before and after.
- No borrowed benchmarks. What that pattern typically yields is not what this work yielded.
- No rounding a qualitative outcome into a quantitative one.
- If a number does not exist, use the **named risk reduced** form instead (below). Do not manufacture one to fill the slot.

Unverifiable claims get **cut**, not softened. A softened invention is still an invention.

---

## The output contract

Your response has these parts, **in this order**.

1. **Evidence Block** — always first
2. **Plain-Language Summary** — business register
3. **Conversation Script** — spoken, mixed audience
4. **LinkedIn Draft** — written, public, mixed audience
5. **The saved file**

**Nothing in parts 2–4 may contain a fact absent from part 1.** The Evidence Block is not a preamble to the real deliverable; it is the constraint the deliverables are built against.

---

## Part 1 — Evidence Block

Gather from the conversation first, then verify against the repo. Do both where both exist; skipping either produces a predictable failure — conversation-only invents specifics, repo-only loses the intent that only exists in the chat.

**Scope the git history to the work, not to a fixed number of commits.** A commit window guesses; a path filter does not. Real repos interleave the work with unrelated commits, so `HEAD~5` will silently drop things.

```bash
git log --oneline -- <path/to/the/work>     # every commit that touched it, however far back
git show --stat <sha>                       # per commit, what actually changed
git status --short                          # uncommitted and untracked work counts too
```

Then open the files themselves, plus any handoff or notes files the work produced. Where the chat does not cover earlier sessions, the commits are the record.

**If there is no conversation history** — a fresh session, or the request arrives cold — say so in one line above the table and build from the repo alone. Repo-derived drafts can recover *what* was built but not *why it was built in that order*; READMEs and design-rationale files partially substitute. Flag the limit rather than writing around it, so the user knows which reasons are missing before they say any of it out loud.

Then fill this table. **One row per shippable unit** — the thing the user would name out loud as a thing they built (a skill, a feature, a service, a migration), not per commit and not per file.

**Plus one final row for the set as a whole.** Cross-cutting facts — the shared pattern across the pieces, the total count, what holds them together — are usually the strongest material and belong to no single row. Without this row they end up homeless and get dropped or, worse, invented later.

| What was built | Mechanism (technical register) | What it's worth (business register) | Outcome: number or named risk | Source |
|---|---|---|---|---|

- **Mechanism** — the actual system, workflow, or failure mode. Named precisely enough that an engineer could ask a sensible follow-up.
- **What it's worth** — cost, time, risk, or the customer. Answers "so what, for the business," not "so what, for the codebase."
- **Outcome** — exactly one of two legal forms:
  - **A number you can point at.** Files covered, workflows tested, steps removed from a manual process, decisions now captured before code gets written. Countable, and you know the count.
  - **A named risk reduced.** Not "reduced risk" — *which* risk. "A schema decision getting locked in across 40 files before anyone questioned it" is a named risk. "Improved architecture quality" is an adjective wearing a lab coat.
  - **A design property now in place**, for work that has no footprint in the world yet. Tooling, processes, and internal standards produce nothing measurable until someone runs them, and forcing that work into an effect-shaped number is exactly how invented metrics get in. The property must be **countable and checkable in the artifact** — "nine fields must be filled before a service name may appear" — and it must be **marked as not yet measured**, in the draft as well as the table. This is the honest form, not the weak one. Do not use it to dodge a measurement that actually exists.
- **Source** — the commit, file, or moment in the conversation. If this cell is empty, the row does not exist.

State plainly what you could not verify rather than filling it in.

---

## Part 2 — Plain-Language Summary

3–5 sentences, business register. What the work is, what it changes, why it exists. One idea per sentence. No unexplained jargon.

This is the answer to "so what have you been working on?" from someone who will not ask a follow-up.

---

## Part 3 — Conversation Script

Spoken language, not written language. Short sentences, contractions, nothing that needs a second read. A line the user cannot say out loud without stumbling is a failed line.

Produce these five pieces, labeled:

**Opener (2 sentences max)** — what you do plus one specific, plain-language proof point. Business register by default. No dash-clause detail; that is follow-up material, not opening material.

**Their question, your read** — one clarifying question the user can ask to find out who they are talking to ("what do you work on?"). Then the two branches:

**If they go technical** — the same claim at technical altitude. Name the mechanism, the tradeoff, the failure mode it prevents. Precision over polish. Once they have signaled depth, stay there; holding the business framing out of habit reads as checking whether they can keep up.

**If they stay non-technical** — hold the business register, *including* when they use technical-sounding buzzwords. Buzzword use is not the same signal as technical fluency.

**Follow-up line** — one or two sentences for a LinkedIn message or email afterward, in the register the live conversation ended in. Not reset to generic-safe business-speak.

For resume or interview lines specifically, the structure is: **action verb + plain business context + dash clause naming specifics + measurable outcome + plain consequence.**

> "Built test coverage across compliance-sensitive customer workflows — citizenship updates and secure document requests — increasing coverage by 75% and reducing production defect risk."

The dash clause carries specificity, not jargon. "Citizenship updates and secure document requests" is specific *and* plain. "Data paths" is neither.

---

## Part 4 — LinkedIn Draft

LinkedIn is mixed audience, public, and permanent. Engineers and recruiters read the same post.

**Shape:**
- **First two lines carry the whole post.** Everything after them is behind a "see more" click. Lead with what changed or what it's worth — never with setup, never with "I'm excited to share."
- **Middle: 2–4 lines of concrete specifics.** This is where the dash-clause content lives — the actual thing built, in plain words. This section is why the post is worth reading; without it the post is a status update about having been busy.
- **The outcome**, in one of the two legal forms.
- **One line of consequence** — what it means for someone other than the author.
- **Optional:** one genuine question or invitation. Only if there is a real one.

**Constraints:** 120–200 words. No hashtag padding — three at most, or none. No emoji bullets.

**Caveats go at the close, and are not optional.** A limit the work genuinely has — untested, no users yet, one team's results — cannot lead, because it is setup. It also cannot be cut to hit the word count. Those closing lines are load-bearing honesty, not modesty; removing them converts a defensible post into a claim the author cannot support. Trim the middle instead.

---

## Part 5 — Save it

Write parts 1–4 to a markdown file named `talking-points-<short-topic>-<YYYY-MM-DD>.md` — descriptive, not generic.

**Where it goes:** the repository root, unless the user named a location or the repo has an established place for working documents (wherever handoff files already live). If the work spans no repo, use the working directory. Ask only if none of those apply.

Tell the user in one line where it is. Do not re-explain the contents.

---

## Pre-delivery checks

Run both before handing anything over.

**Jargon check** (applies to parts 2, 3-business-branch, and 4) — for each technical term:
1. Would a hiring manager or exec parse this without asking a follow-up?
2. If no: can it be cut without losing the claim, or does it need a plain-language substitute?
3. Does the substitute still name something specific — a workflow, a system, a number? **Vague is a failure mode too.** The fix for jargon is precision in plain language, not abstraction.

**Accuracy check** (applies to part 3's technical branch, and to any technical line in part 4):
1. Is the mechanism actually named, or is this a business sentence wearing technical vocabulary?
2. Could another engineer ask a sensible follow-up question from what is written, or is there nothing to grab onto?

---

## Talking about AI and agent tooling

Work done with Claude — skills, agents, prompts, internal tooling — attracts buzzword slop harder than any other category, because the vocabulary is available to people who have not built anything. "Leveraging AI to build robust automation" survives both checks by describing nothing.

The mechanism is the part worth saying. Not "I used AI" — *what the thing does and what it prevents.*

| Slop | Grounded |
|---|---|
| "Leveraged AI to streamline my workflow" | "Wrote a decision gate that stops me from generating a schema before I've answered where the source of truth lives" |
| "Built AI-powered developer tooling" | "Packaged the checklist I kept skipping into something the assistant runs before it writes code" |
| "Using agents to boost productivity" | "Turned five recurring architecture arguments into gates that get answered before the code exists" |

The second column is *also* the business framing. Naming the specific failure a tool prevents is what makes it legible to a non-engineer — the vagueness was never making it more accessible.

---

## Red flags — stop and rebuild the Evidence Block

- A percentage appears that no one measured
- "Significantly," "robust," "seamless," "cutting-edge," "leveraged"
- A LinkedIn draft that would read identically for a completely different project
- The technical branch and the business branch make claims that are not the same claim
- A row in the Evidence Block with an empty Source cell
- Reaching for what work like this "typically" achieves

**All of these mean: go back to what actually happened and write from that.**
