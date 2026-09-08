---
name: software-carpentier-brand
description: Use when copy needs to represent the user professionally under their personal brand — LinkedIn headline/About, LinkedIn feed posts (reacting to news, or writing up your own work), resume bullets, cover letters, elevator pitches, interview self-intros, portfolio/personal-site copy, or a description of the DevHiveMind Obsidian vault for an external audience. Also use to run a "check my brand consistency" pass on something already written. Applies a fixed identity (carpenter→architect device, target positioning in regulated/high-stakes systems, named proof points) and a hard honesty-calibration layer specific to this user's career facts (total relevant experience, pre-prod vs. production scope, execution vs. ownership, feature-count inflation) — constraints a generic writing pass won't know to check. Not for gathering evidence from work that just happened in this session or repo — that Evidence Block belongs to `explaining-my-work`; hand off there first, then run its output back through this skill's voice and honesty layer. Not for job-search strategy, salary negotiation, or which jobs to apply to — that's a different decision, not a voice/copy one.
---

# Software Carpentier Brand

A personal brand is not a slogan repeated on every document — it's a small set of facts, held to a
fixed honesty bar, rendered in a consistent voice. This skill holds three things constant across
every piece of self-representing copy: **the device** (carpenter → architect, shown in word choice,
not stated as a tagline), **the proof points** (real, finite, don't invent a fourth), and **the
honesty constraints** (career facts specific enough that a generic writing pass would get them
wrong by default).

## Out of scope

- **Evidence-gathering from work that just happened.** If the ask is "turn this thing I just built
  into a LinkedIn post" or "write this up for my resume," the facts come from the repo and the
  session — that's `explaining-my-work`'s Evidence Block. Get that first, then run the resulting
  draft through this skill's voice pass and the honesty-calibration constraints below (which
  `explaining-my-work` doesn't track — it doesn't know this user's total years of experience or
  which environments were pre-prod).
- **Job-search strategy.** Which roles to target, when to apply, how to negotiate an offer. This
  skill governs how something is *said*, not what to *do*.
- **Technical writing that isn't self-representing.** A design doc, a PR description, a Slack
  update to a teammate — no brand voice needed there.
- **De-AI-ing prose.** "Make it sound less like AI" on an existing draft (a LinkedIn post
  included) is `delete-ai-words`, not this skill. The "check my brand consistency" pass here only
  checks identity, proof points, and the honesty calibration — run `delete-ai-words` for the
  prose, then add these checks after only if the draft also makes career claims.

---

## The identity (fixed — don't renegotiate per draft)

**Name device.** Carpentier → "Software Carpentier": someone who builds things by hand, joint by
joint, currently working toward Software Architect. The metaphor is a *lens on word choice* —
built, joined, load-bearing, structural, framed, reinforced — not a tagline. It should be possible
to read a piece of copy, notice the device was used, and never see the words "Software Carpentier"
appear literally. Most pieces of copy use it in zero or one place. A LinkedIn About section might
carry it once, structurally, in how a project is described; an elevator pitch has no room for it at
all. If it shows up more than once in a single piece, that's overuse — cut it back to the strongest
instance.

**Proof-of-work anchor.** DevHiveMind (the Obsidian vault) is a running, dated record of what's
been built and learned — describe it as evidence of continuous building, never as a static
portfolio or credential. "A dated log of every architecture decision and skill built, going back
to [date]" is the right shape. "A portfolio showcasing my projects" is not — it's a snapshot word
for a thing that is explicitly not a snapshot.

**Target positioning.** Engineer for regulated, high-stakes systems — banking, fintech, payments,
collections. Not "full-stack." Not generic "fintech." The regulated/high-stakes framing is what
makes the compliance-adjacent proof points (test coverage on citizenship/document workflows) land
as relevant rather than incidental.

---

## The proof points — real, finite, don't invent a fourth

| Proof point | The real shape of it | Safe framing | Unsafe framing |
|---|---|---|---|
| **TracFlo migration** | Reverse-engineered a legacy PHP/WordPress schema; led a 30+ file Knex migration with rollback logic; unblocked a 9-person team. | "Led a 30+ file schema migration with rollback logic, unblocking a 9-person team." | Implying the reverse-engineering or migration design was a shared/committee decision if it wasn't — check ownership vs. execution before writing "led." |
| **TracFlo — 13 features** | 13 features shipped on top of the migration, but largely the *same layered pattern* applied across different domains, not 13 distinct technical problems solved. | "13 features shipped on the new schema" (a count) or "applied the same layered pattern across 13 features" (names the repetition honestly). | "13 different technical challenges solved" / anything implying variety of approach, not just count. |
| **Capital One — Promises-to-Pay / Arctic** | Built the Promises-to-Pay Step Function and the Arctic offers system for collections. Ran in **pre-production/staging**, not live production. | "Built the Promises-to-Pay Step Function for a collections offers system (Capital One, pre-production)." | Any phrasing that implies the code is live/serving real customer traffic — "deployed to production," "in production today," "customers use this daily." |
| **Capital One — test coverage** | Raised test coverage 70% → 75% on compliance-sensitive workflows: Update Citizenship, Secure Documents. | "Raised test coverage from 70% to 75% on compliance-sensitive workflows (citizenship updates, secure document requests)." | Rounding the 5-point gain up, or dropping the workflow names for a vaguer "improved test coverage." |
| **TD Bank — BSA role** | Upskilling-heavy, not classic requirements-gathering. | "BSA role focused on upskilling into engineering-adjacent work" or similar — honest about what the role actually was. | Default BSA language ("gathered requirements from stakeholders," "wrote user stories for the dev team") applied because it's the generic template for the title, not because it's what happened. |
| **Cross-functional range** | QA → BSA → SWE, with domain depth concentrated in payments/collections. | "QA to BSA to SWE, with depth built specifically in payments and collections." | Framing the range as generalist breadth ("versatile across the full SDLC") when the actual asset is the domain concentration, not the breadth. |

**Total directly-relevant engineering experience: ~2.75 years.** Any copy that would let a reader
infer more than that (job-title stacking without dates, "years of experience building X" language,
a resume date range that reads longer than it is) gets flagged before output, not silently
softened.

**Execution vs. ownership.** Before writing "built," "led," "designed," or "owned" anywhere, check:
did this user make the call, or execute a call someone else made? Both are legitimate to state —
"built to spec" and "made the call to structure it this way" are both honest — but the verb has to
match which one actually happened. Don't let a strong verb quietly upgrade execution into
ownership.

### Picking which proof points to use — don't default to the same one or two

With six proof points and many possible formats (LinkedIn About, resume bullet, cover letter,
elevator pitch, interview intro), the failure mode isn't inventing new material — it's
**over-relying on TracFlo and the Step Function every time** because they're the two most
quotable. Before drafting, name out loud which proof point(s) fit this specific format and
audience:

- **Short formats** (elevator pitch, LinkedIn headline, interview opener) — exactly one proof
  point, the one most relevant to who's listening. A collections-domain interviewer gets the
  Capital One workflow; a data-migration-heavy role gets TracFlo.
- **Longer formats** (LinkedIn About, cover letter, resume) — two to three, chosen for coverage,
  not repetition. Don't restate the same proof point in three different sentences of one document.
- **If asked to describe experience with something not covered by any proof point** (a technology,
  a domain, a scale) — say so. Don't stretch an existing proof point to cover a gap it doesn't
  actually cover.

---

## Honesty calibration — run every draft against this, every time

This is a check, not a style note. Before handing back a draft, walk each line against:

1. **Production claim check.** Does any line imply the Capital One work is live/serving production
   traffic? It ran in pre-production/staging only.
2. **Variety-inflation check.** Does any line imply the 13 TracFlo features were 13 distinct
   technical problems, rather than one pattern applied 13 times?
3. **Role-language check.** Does the TD Bank BSA description default to generic requirements-
   gathering language instead of the actual upskilling shape of the role?
4. **Tenure check.** Would a reader infer more than ~2.75 years of directly-relevant engineering
   experience from job-title stacking, date-range framing, or "years of experience" language?
5. **Ownership check.** Does any verb (built/led/designed/owned) imply a decision was made rather
   than executed, where the real shape was execution from someone else's spec?
6. **Number check.** Is every number in the draft one that's actually confirmed (70%→75%,
   30+ files, 9-person team), with nothing rounded up for effect?
7. **Soft-skill check.** Any unattached claim like "strong communicator" or "team player" with no
   specific instance behind it — cut it or tie it to a real example.
8. **Paste-language check.** Any generic resume-summary phrasing ("versatile engineer with
   experience across...") that isn't checkable against a real proof point — cut it.

Anything that fails a check gets flagged and fixed before the draft is handed over, not noted as a
caveat underneath an oversold line.

---

## Voice rules

- **Lead with what was built and its business consequence** (revenue, cost, risk, compliance) —
  not job title, not tech stack. Tech stack is follow-up material, not opener material.
- **Every sentence checkable against a real proof point.** If a sentence can't be traced to one row
  in the table above, it doesn't belong in the draft. **Exception:** content sourced from an
  `explaining-my-work` Evidence Block (work verified against the actual repo/session) counts as a
  real proof point even though it isn't one of the six fixed rows — the table is the closed set of
  *career-wide* facts, not the only facts this skill is allowed to use. Run that content through the
  honesty-calibration checks below same as anything else; don't strip it for not being in the table.
- **No generic soft-skill claims** unless tied to a specific instance from a proof point.
- **Numbers only when real and confirmed** — never rounded up for effect.

---

## Drafting a LinkedIn feed post

A feed post is a different job from profile copy: it reacts to something (a launch, a debate, a
thing just shipped) and it runs on angle + hook, not on a headline formula. The identity, the
proof points, and the honesty calibration above still bind — a public post is the *worst* place
for an oversold production claim or an inflated tenure to leak.

**Gather the raw material first — don't draft from a cold start.** Use `AskUserQuestion` to get:

- the news, topic, or event being reacted to (or "my own work" + which piece)
- the specific story, number, or example the user brings — the input the model can't invent. It
  has to trace to a proof-point row above or to an `explaining-my-work` Evidence Block; if it
  traces to neither, that gap is the thing to close before writing, not to paper over.
- the goal: reach, inbound leads, authority, or a hiring signal — this changes which proof point
  leads and how direct the ask is
- constraints: length, and text post vs. carousel

**Then:**

1. Offer 3–5 distinct angles/hooks, each anchored to a real proof point or Evidence Block fact —
   not a generic take any account could post. Name which proof point each one leans on.
2. User picks one (or more).
3. Assemble: the chosen angle, the full caption in the Voice rules above (lead with what was
   built and its consequence; every sentence checkable; no unattached soft-skill claims; real
   numbers only), and direction for the image/carousel — what it contains and what it looks like.
4. Run the honesty-calibration pass on the caption. Report pass/fail per relevant check; show the
   fixed line for any fail.
5. Close with concrete next steps to sharpen it.

**Guardrail — don't run one recipe into the ground.** If a hook pattern or angle was already used
in a recent post this conversation, flag it and vary the execution; mirroring what worked is
fine, repeating the exact move is not.

**Optional post recipe.** If the user has a content-performance report or a posting SOP, its
findings — best formats, best-performing angles ranked, hook patterns, cadence quirks — go in a
bracketed block here and override the Voice-rules defaults where they conflict. Absent that, the
Voice rules are the default. This block is user-specific, like the proof-point table — keep it
current or delete it.

---

## Output contract

When invoked, respond with these parts in order:

1. **Draft** — the requested copy (LinkedIn About, resume bullet, cover letter, pitch, etc.), in
   the voice above, using the proof point(s) selected for this format/audience.
2. **Honesty-calibration pass** — walk the eight checks above against the draft. State pass/fail
   per check that's relevant to what was drafted; for any fail, show the fixed line.
3. **Device-usage note** — one line: where the carpenter→architect device was used (if anywhere),
   and whether it's being reused from a very recent draft in this conversation (overuse flag) or
   deliberately left out because the format has no room for it.

For a "check my brand consistency" request on existing copy: skip part 1, run the existing text
through parts 2 and 3, and show the specific line edits rather than a rewritten whole.

For a LinkedIn feed post: follow **Drafting a LinkedIn feed post** above (interview, then angles,
then assemble); parts 2 and 3 of this contract still apply to the finished caption.

---

## Portability

Repo-agnostic. Writes nothing unless the user asks for a file; produces the draft in chat. Copy the
`software-carpentier-brand/` directory into another repo's `.claude/skills/` to use it there. The
proof-point table and the optional post recipe are specific to this user's real career facts as of
2026 — when a new role, a new metric, or a materially longer tenure exists, this file needs a real
update, not copy that quietly outgrows it.
