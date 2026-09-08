---
name: disclosure-gap-audit
description: A pre-flight audit run against a shipped-or-shipping product and its public commitments — the privacy policy, terms, cookie banner, marketing claims — that produces a findings register of the gaps between what the product does and what it discloses or secures. Three passes, deliberately unequal. Spine: policy-vs-practice disclosure gaps (a practice the policy omits or discloses vaguely) walked across 15 probes — AI/LLM processing of user input, model training on user data, automated decisions / profiling / scoring, named third-party subprocessors, retention windows and deletion timeline, categories of data collected (incl. inferred / fingerprinting / location), cross-site and cross-app tracking, children's data, international transfers, cookie categorization and a preference center, biometric data called out separately, right-to-know mechanics, policy-vs-practice drift from bolt-on features, the CCPA/CPRA "sale" vs "share" distinction for ad-tech flows, and a missing effective-date / changelog. Secondary: security design anti-patterns at design-review depth — secrets in version control, missing auth checks, IDOR, insecure defaults, missing rate limiting, PII in logs. Flag-only: legal/compliance exposure — age gate, accessibility, dark patterns, consent flow, IP/licensing — where the output names the regime and defers to counsel, never rules. It gates on a data inventory (data flows, subprocessors, retention config, tracking tech, AI features and where user input goes): it will not infer the product's behaviour to fill a gap, and every missing inventory element becomes a finding that caps the passes depending on it — with no inventory at all, the register is just those gaps plus "no policy / no inventory" as finding #1. Use when someone says "does our privacy policy cover what we actually do", "we added an AI feature — what do we need to disclose", "review our app for compliance / privacy risk", "audit our data handling against our policy", "GDPR / CCPA exposure review", "check this policy against the product before we publish it", or hands over a policy and a design doc and asks where they diverge. Not for the diff's own code-level vulnerabilities — that's `security-review`, which reads the changed code; this reads the whole product and its public commitments. Not for one already-proposed concrete change and what it breaks elsewhere — that's `change-surface-audit`; if the question about that change is instead what it *obligates you to disclose*, this skill takes the disclosure half. Not for stating a compliance regime as an input constraint before a design starts — that's `design-scoping`, the pre-design front door; this is the post-hoc audit of a design that already exists and already makes claims. Not for choosing the authorization / IAM / secrets model going in — that's `access-control-modeling` / `cloud-iam-boundary` / `config-and-secrets-management`; this only flags where an existing design skipped one and hands the fix to them. Not for an exhaustive design-wide failure enumeration across availability / data-loss / latency categories — that's `failure-mode-analysis`, a pre-mortem over operational failure modes, not undisclosed-practice or missing-control gaps. Not for the dollar cost of a compliance program — that's `technical-cost-decision`. A bare conceptual question — "what is GDPR Article 22", "what counts as a sale under CPRA" — is answered directly, no audit.
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
   Paste the text or point to it. If **none exist**, that is itself a High finding and the
   audit proceeds against "what a policy would need to say."
2. **Jurisdictions in play.** Where the users are, where the data is processed and stored,
   whether the product is offered to the EU/UK, California, or other US states with privacy
   statutes. This scopes which regimes the flag pass names — it does not change the spine
   pass, which is factual regardless of jurisdiction.
3. **The data inventory — the gate.** The register is withheld until these are on the table:
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
date. If no policy exists, log finding #1 (High) now and continue. **If the product is B2B
and its records are about the customer's employees**, note it here — the data subjects
include those employees, some regimes cover worker data, and per the controller/processor
split several fixes will land in the customer-facing DPA and subprocessor list rather than
the public website policy (see `disclosure-checklist.md` "B2B / workforce products").

### 2. Gate on the data inventory

Check input 3 is present. For any missing element, write the gap as a finding
(`inventory-incomplete`, severity by what's unknown — a missing subprocessor list is High,
a missing backup-retention number is Medium) and mark the passes that depend on it capped.
Do not guess the product's behavior to fill a hole. Proceed with what's known.

**If the user declines to supply the inventory** (or pushes back — "legal already signed
off", "just give me the top gaps"): do not refuse, and do not fill the holes with assumed
values. Still produce the register from what's known — a **conditional, probe-keyed** list
("if the flow is X, this is a High finding"), the `inventory-incomplete` rows at worst-case
severity, and the short list of facts that would convert it into a real audit. A prior
legal review is not the same as visibility into the current data flows, and if it predates
a feature that is exactly probe 12 — say so, without ruling on the legal question.

**A missing *verbatim policy* is not a "no policy" finding** when the user has said one
exists. Treat it as `inventory-incomplete` on the policy side of the affected spine probes,
ask once for the text or a link, and proceed. Only log the finding-#1 "no policy" row
(High) when there genuinely is no public policy.

### 3. Spine pass — policy vs practice

Walk the **15 probes** in `disclosure-checklist.md`. For each: state what the product does
(from the inventory), then what the policy says. Classify the row:

- `disclosed-adequately` — specific, current, and complete. No finding.
- `disclosed-inadequately` — vague ("we may share data with partners"), incomplete (a
  subprocessor list missing the AI vendor), or outdated (written before the feature
  shipped). → a `policy-vs-practice-gap` finding, usually Medium.
- `not-disclosed` — the practice is real and the policy is silent. → a
  `policy-vs-practice-gap` finding, Medium or High per `disclosure-checklist.md`'s
  per-probe severity notes.
- `n/a` — the product genuinely does not do this. State why, don't skip silently.

### 4. Security pass — design-review depth only

Walk the fixed probe list in `security-and-legal-passes.md`: secrets in version control,
a resource with no authorization check, IDOR (object references not scoped to the caller),
insecure defaults (public-by-default sharing, permissive CORS, debug endpoints live),
missing rate limiting on auth and expensive endpoints, PII written to logs or analytics,
transport/at-rest encryption absent, over-broad OAuth scopes or third-party permissions.
Each hit is a `security-anti-pattern` finding with a fix handoff — this skill flags that
the control is missing, it does not design the control. **When no design doc or
architecture description was supplied**, don't emit eight near-identical
`inventory-incomplete` rows — bundle them into the four themed findings
`security-and-legal-passes.md` defines (tenant isolation & object scoping · data egress ·
abuse & cost controls · key & crypto hygiene), each written as the questions to answer.

### 5. Legal/compliance pass — flag only, never rule

Walk the flag list in `security-and-legal-passes.md`: age gate, accessibility (ADA/WCAG),
dark patterns in consent or cancellation flows, consent mechanics (is consent obtained
where a regime would require it), IP/licensing (training-data provenance, third-party
content, open-source license obligations). For each concern: state the **observable fact**
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
Spine (15 probes):    adequate <n> · inadequate <n> · not-disclosed <n> · inventory-incomplete <n> · n/a <n>
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

> "We just added a feature that sends the user's support message to GPT to draft a reply.
> Our privacy policy is from last year. What do we need to disclose?"

Inventory gate first: which model provider, is it their API (a subprocessor), are the
messages retained or used for training by the provider, does anything automated act on the
model's output. Spine pass hits probes 1 (AI processing of user input — not disclosed),
3 (subprocessor list — missing the AI vendor), and 12 (policy-vs-practice drift — written
before the feature). Likely findings: one High (`not-disclosed` AI processing of
user-submitted content), one Medium (`disclosed-inadequately` subprocessor list). Security
pass: is the support message scrubbed of anything it shouldn't send to a third party.
Recommendation: policy revision to the "How we use your data" and "Who we share with"
sections; confirm the provider's data-use terms.

> "We're removing the `/v1/export` endpoint, nobody uses it. What breaks?"

Not this skill — that's a blast-radius question → `change-surface-audit`. If the endpoint's
*removal* also means a data flow to a partner stops and the policy claims that flow exists,
the disclosure half of that comes back here; the "what depends on the endpoint" half does
not.

> "Is this login handler secure?" (a diff is pasted)

Not this skill — code-level review of the diff → `security-review`. This skill's security
pass asks whether login *has rate limiting and an authz model at all*, as one row in a
product-wide register, not whether this handler's code is correct.

> "What does GDPR Article 22 actually require?"

Conceptual question → answered directly. No audit, no inventory gate.

---

## Portability

Repo-agnostic. Writes an optional register to `docs/compliance/`. The `disclosure-checklist.md`
"current as of" note names the fast-moving regimes so a future run knows to re-check them.
Copy the `disclosure-gap-audit/` directory into another repo's `.claude/skills/`. See
`README.md` for where it sits among the sibling skills.
