---
name: disclosure-gap-audit
description: Pre-flight audit of a shipped-or-shipping product against its public commitments (privacy policy, terms, cookie banner, marketing claims), producing a findings register of disclosure and security gaps; gates on a data inventory. Use for "does our privacy policy cover what we actually do", "GDPR / CCPA exposure review". Not for code vulnerabilities (`security-review`) or one proposed change (`change-surface-audit`).
---

# Disclosure Gap Audit

Two things drift apart in a live product. The **practice** moves fast — a new analytics
SDK, an LLM call added to a form, a scoring model, a data export to a new vendor. The
**public commitments** — the privacy policy, the cookie banner, the marketing page — move
slowly or not at all. The gap between them is where a regulator's inquiry, a plaintiff's
complaint, or a due-diligence finding starts. This skill takes the product as it actually
is and asks, three ways: **what does it do that it hasn't told anyone, and what did it skip
that it should have built?**

It is a mechanical audit walk, not a Socratic gate — it doesn't withhold judgment pending a
user rep. But it has a hard input rule: it **will not infer what the product does** to fill
a hole in the **data inventory**. Every element of the inventory that is missing becomes a
finding in its own right and caps the pass that depends on it; with a partial inventory the
audit still runs on what's known, and with nothing at all the register is a list of those
gaps. You cannot audit the disclosure of a data flow nobody has written down — so the
un-written-down flow is the finding.

It is **non-authoritative on every legal question**. The spine pass produces factual gap
statements ("the product does X; the policy does not mention X"). The legal/compliance pass
produces *flags* that name a regime and route to counsel. Neither produces a verdict that
something is unlawful — that is not this skill's call, and jurisdiction makes it not a
call that can be made from a checklist.

## When to use

- A privacy policy or terms document exists and someone wants it **checked against what the
  product actually does** — "does our policy cover this", "we're about to publish this,
  pressure-test it first".
- An **AI or ML feature was added** to an existing product and the question is what now has
  to be disclosed — third-party LLM processing, training on user input, an automated
  decision that affects users.
- Someone asks for a **privacy / compliance risk review** of an app, a design doc, or a
  data-flow diagram, and wants the exposure surfaced and ranked.
- A **data-sharing or vendor change** happened (a new analytics tool, ad pixel, export
  pipeline) and the question is the disclosure obligation it created.
- Due diligence, a security questionnaire, or an audit is coming and the team wants to find
  the gaps before someone external does.

## Out of scope — hand these off

- **The changed code's own vulnerabilities** — an injection bug, an unsafe deserialize, a
  broken crypto call in the diff → `security-review`. That reads the code as written; this
  skill reads the whole product and its public commitments and asks what's undisclosed or
  un-built. The security pass here is design-review depth (is there *an* authz check on this
  resource), not a code audit.
- **One concrete proposed change and its blast radius** — "we're adding a `suspended` status,
  what breaks", "we're removing this endpoint" → `change-surface-audit`. If the question
  about that same change is instead *what it obligates the policy to say* (the new SDK's
  data sharing, the new field's retention), that disclosure half is this skill.
- **Stating a compliance regime as a design input** — "we're building X, GDPR applies, where
  do I start" → `design-scoping`, the pre-design front door. This skill runs *after* a
  design exists and already makes public claims, and audits the divergence.
- **Choosing the authorization, IAM, or secrets model** — "flat vs hierarchical RBAC",
  "where should this secret live", "what's the least-privilege policy for this role" →
  `access-control-modeling` / `cloud-iam-boundary` / `config-and-secrets-management`. This
  skill only flags that an existing design skipped one ("this resource has no authz check",
  "this API key is in the repo") and hands the fix to them.
- **Exhaustive design-wide failure enumeration** — "what could go wrong with this
  architecture" across availability / data-loss / latency / dependency categories →
  `failure-mode-analysis`. That is a pre-mortem over operational failure modes; this skill
  is about undisclosed practices and missing controls, and its security pass is a fixed
  short list, not a nine-category walk.
- **The dollar cost of a compliance program** — tooling, headcount, an audit engagement →
  `technical-cost-decision`.
- **Drafting the privacy policy or terms text** — this skill audits and names sections to revise.
- **A bare conceptual question** — "what is GDPR Article 22", "what makes something a
  'sale' under CPRA", "what's WCAG AA" — answered directly, no audit.

---

## Inputs the procedure needs

Don't invent the product or its policy. If the inventory (input 3) is missing, the audit
still starts — but every pass that depends on a missing item is capped at
`inventory-incomplete` and that gap is finding #1.

1. **The public commitments that exist.** Privacy policy, terms of service, cookie
   banner/consent UI text, any marketing or product-page claims about data handling
   ("we never sell your data", "your data is encrypted", "AI-free"), a DPA if there is one.
   Paste the text or point to it. If **none exist** (and it isn't Step 1's single-operator case), that is itself a High finding and the
   audit proceeds against "what a policy would need to say."
2. **Jurisdictions in play.** Where the users are, where the data is processed and stored,
   whether the product is offered to the EU/UK, California, or other US states with privacy
   statutes. This scopes which regimes the flag pass names — it does not change the spine
   pass, which is factual regardless of jurisdiction.
3. **The data inventory — the gate.** The *complete* register is withheld until these are on the table; if they never arrive, Step 2 still produces the conditional, `inventory-incomplete`-led register (the inventory rule above and Step 2), never a clean all-clear:
   - **Data flows** — what personal data is collected (fields the user provides *and*
     data derived or inferred), from what surfaces, into what stores.
   - **Third parties / subprocessors** — every external service that receives user data:
     analytics, advertising, cloud/hosting, email, support, payment, and **AI/LLM
     providers**. Named, not "some vendors."
   - **Retention** — how long each category is kept, and the deletion path and timeline
     (including backups).
   - **Tracking technology** — cookies by purpose (necessary / functional / analytics /
     advertising), pixels, SDKs, device fingerprinting, and any cross-site or cross-app
     tracking.
   - **AI features** — every place user input reaches a model; whether the model is a
     third-party API; whether inputs are used to train or fine-tune; whether any automated
     score or decision affects a user (eligibility, pricing, ranking, moderation).
   - **Minors** — does the product knowingly have, or foreseeably attract, users under 13
     (COPPA) or under 16 (GDPR)?

---

## The procedure

Work `disclosure-checklist.md` (the spine) and `security-and-legal-passes.md` (the
secondary and flag passes, and the register format) alongside these steps.

### 1. Set scope and the "current as of" caveat

Restate the jurisdictions (input 2) and list which public documents exist (input 1). Record
today's date and note that the volatile items — the US state-law patchwork, the CCPA/CPRA
"sale/share" treatment, the EU AI Act's disclosure duties — are current only as of that
date. If no policy exists (and it isn't the single-operator case below), log finding #1 (High). **If the product is B2B
and its records are about the customer's employees**, note it here — the data subjects
include those employees, some regimes cover worker data, and per the controller/processor
split several fixes will land in the customer-facing DPA and subprocessor list rather than
the public website policy (see `disclosure-checklist.md` "B2B / workforce products").

**If the product only ever holds its operator's own data** (personal tool, no one else's
records; confirm nobody else can sign up), skip the spine and Step 2: mark it `n/a` in one line
with that reason, write no register of n/a rows, run only the Step 4 security pass (an exposed
login matters regardless), list the **triggers** that end this (a second user or sign-up,
someone else's records, any child's data), and stop. A bank or aggregator connection re-runs
probe 3 (judged against the aggregator's terms if no policy), the retention probe and Step 4.

### 2. Gate on the data inventory

Check input 3 is present. For any missing element, write the gap as a finding
(`inventory-incomplete`, severity by what's unknown — a missing subprocessor list is High,
a missing backup-retention number is Medium) and mark the passes that depend on it capped.
Do not guess the product's behavior to fill a hole. Proceed with what's known.

**If the user declines the inventory** (or says "legal already signed off"): do not refuse and do
not assume values -- still produce the conditional, probe-keyed register with `inventory-incomplete`
rows at worst-case severity. **A missing verbatim policy is not a "no policy" finding** when the user
says one exists: ask once for the text and proceed. Read "Inventory declined or policy text missing"
in `disclosure-checklist.md` for the full handling.

### 3. Spine pass — policy vs practice

Walk the **15 probes** in `disclosure-checklist.md`. For each: state what the product does
(from the inventory), then what the policy says. Classify the row:

- `disclosed-adequately` (specific, current, complete) — no finding.
- `disclosed-inadequately` (vague, incomplete, or outdated) → `policy-vs-practice-gap`, usually Medium.
- `not-disclosed` (practice real, policy silent) → `policy-vs-practice-gap`, Medium or High per
  `disclosure-checklist.md`'s per-probe severity notes.
- `n/a` — the product genuinely does not do this. State why, don't skip silently.

The full test per class (plus `inventory-incomplete`) is under "Classifying a row" in `disclosure-checklist.md`.

### 4. Security pass — design-review depth only

Walk the fixed probe list in `security-and-legal-passes.md` (secrets in VCS, missing authz, IDOR,
insecure defaults, missing rate limits, PII in logs, no encryption, over-broad scopes).
Each hit is a `security-anti-pattern` finding with a fix handoff — this skill flags that
the control is missing, it does not design the control. **When no design doc or
architecture description was supplied**, don't emit eight near-identical
`inventory-incomplete` rows — bundle them into the four themed findings
`security-and-legal-passes.md` defines (tenant isolation & object scoping · data egress ·
abuse & cost controls · key & crypto hygiene), each written as the questions to answer.

### 5. Legal/compliance pass — flag only, never rule

Walk the flag list in `security-and-legal-passes.md` (age gate, accessibility, dark patterns, consent
mechanics, IP/licensing, incident/breach notification). For each concern: state the **observable fact**
that raised it, **name the regime(s)** it implicates given input 2, and set *Who confirms
this* to counsel / privacy officer / an accessibility specialist. Produce a
`needs-legal-review` finding. Do **not** write "this violates COPPA" — write "the product
collects birthdates and has no age gate; COPPA and GDPR-minors implications — confirm with
counsel."

### 6. Assemble the findings register

One table, from `security-and-legal-passes.md`'s format: ID, Category, Finding (the
observable fact), Evidence (the inventory item + the policy text or its absence), Severity
(High / Medium / Low — definitions in the reference), Who confirms this, Handoff. Sort by
severity, then by category. Keep `inventory-incomplete` rows visible at the top of their
band — an unknown is not a pass.

### 7. Recommend next actions per category, then stop

- `policy-vs-practice-gap` → policy revision (name the sections) **or** a product change to
  stop doing the undisclosed thing. State which, per row.
- `security-anti-pattern` → the handoff skill for the control, and `security-review` for
  the code once the control is designed.
- `needs-legal-review` → the named reviewer, with the observable fact and regime attached.

Then stop. Writing the policy language, building the missing controls, and obtaining the
legal review are separate, explicitly started steps that consume this register.

---

## Output

**1. In chat**, a summary block:

```
Scope:                <jurisdictions>  ·  docs reviewed: <policy / ToS / cookie UI / marketing / DPA, or "none">
Current as of:        <date> — volatile: US state-law patchwork, CCPA/CPRA sale-vs-share, EU AI Act disclosure
Inventory:            <complete | incomplete: which elements missing>
Spine (15 probes):    adequate <n> · inadequate <n> · not-disclosed <n> · inventory-incomplete <n> · n/a <n>  (single-operator product: one line, `n/a — single-operator`)
Findings:             High <n> · Medium <n> · Low <n>   (policy-vs-practice <n> · security <n> · needs-legal-review <n>)
Top findings:         <the 3-5 that matter, one line each>
Recommendation:       <policy revision sections | product changes | controls to build | reviewers to engage>
```

**2. A written register** to `docs/compliance/disclosure-audit-<slug>-<date>.md` when the
team wants it tracked or re-scored over time — the full table plus the scope note, the
"current as of" date, and a header stating the audit is non-authoritative on legal
questions and the `needs-legal-review` rows require counsel. A one-off check with no
tracking need gets only the chat block, same as `change-surface-audit`.

Then stop.

---

## Example invocations

Four worked invocations (an LLM-drafted support reply against an old policy, an endpoint removal that
routes to `change-surface-audit`, a pasted login diff that routes to `security-review`, and a bare GDPR
question answered directly) are in `example-invocations.md`. Read it for a model of the inventory gate
firing, sample probe hits, or the routing calls.

---

## Portability

Repo-agnostic. Writes an optional register to `docs/compliance/`. The `disclosure-checklist.md`
"current as of" note names the fast-moving regimes so a future run knows to re-check them.
Copy the `disclosure-gap-audit/` directory into another repo's `.claude/skills/`. See
`README.md` for where it sits among the sibling skills.

## Routing boundaries (full)

The frontmatter `description` is truncated in the skill listing, so the full boundary rules live here (moved verbatim from the original description):

- Not for the rate-limiting / abuse-protection design that a missing-control finding calls for — that is `resilience-strategy`.
- Not for designing what is safe to log or the audit-logging pipeline a PII-in-logs finding calls for — that is `observability-strategy`.
- Use when someone says "does our privacy policy cover what we actually do", "we added an AI feature — what do we need to disclose", "review our app for compliance / privacy risk", "audit our data handling against our policy", "GDPR / CCPA exposure review", "check this policy against the product before we publish it", or hands over a policy and a design doc.
- A bare conceptual question — "what is GDPR Article 22", "what counts as a sale under CPRA" — is answered directly, no audit.
