---
name: legal-readiness-gate
description: Gate for what an app owes users and customers as it ships and grows: states data classes, jurisdictions, role and stage, then outputs a flag-only obligations checklist (consent, user rights, vendors/DPAs, SLA and contract terms, health data). Use for "what do I need legally before launch", "do I need HIPAA", "what SLA can we promise". Not auditing a live policy (`disclosure-gap-audit`), scoping a build (`design-scoping`).
---

# Legal Readiness Gate

Before launch, and again at each growth step, answer one question: **given the data this
app holds, who its users are, and who pays, what must it build, sign, and publish — and by
when?** Obligations are not one list. They depend on data class (a to-do title is not a
symptom log), user location (one EU user brings GDPR), the operator's role (controller,
processor, HIPAA business associate), and stage (a side project owes less than a product
with an enterprise customer asking for a DPA and an SLA).

The skill makes the user state those inputs in their own words, then produces an
obligations checklist sorted by stage. It is **non-authoritative on every legal question**:
each item names a regime and a human who confirms it (counsel, privacy officer, security
lead) and never asserts that something is or is not lawful. Jurisdiction, facts and
statutes move, so it flags and routes; it does not give a verdict.

## When to use

- A build is heading toward real users and someone asks **what legal / privacy groundwork
  it needs** — "what do I need before launch", "do I need a privacy policy, terms,
  a cookie banner", "what do we owe users who ask us to delete their data".
- The app touches **health, financial, children's, biometric, or location data** and the
  question is which regime applies and what that forces in the design.
- Someone asks **"do I need HIPAA / GDPR / CCPA / SOC 2"** for a product that is not live
  yet, or about to take on a new user group or market.
- A **first paying or business customer** is asking for an SLA, a DPA, a security
  questionnaire, or a BAA, and the team wants to know what is promisable and what to sign.
- The user base is **growing** (a new region, a first enterprise deal, an AI feature) and
  the question is what changed in what they owe.

## Out of scope — hand these off

- **A live privacy policy / terms / cookie banner checked against what the product really
  does** → `disclosure-gap-audit`. That audits the divergence after the fact; this skill
  works out what to build and publish before or while shipping. When a shipped product has
  both questions, run this first for the target list, then that for the gap.
- **Scoping a system** (purpose, audience, numeric targets, the compliance line in
  constraints) → `design-scoping`. It records "GDPR applies"; this skill unpacks what that
  means once the regime is named. Scoping hands compliance questions here.
- **Computing an SLA's achievable uptime** — done here in outline (series availability from
  the components, `sla-and-contracts.md`). `reliability-math` takes over once there is live
  telemetry (SLO burn, percentiles); single points of failure are `failure-mode-analysis`.
  This skill decides *which commitments to make and what the contract must say*.
- **Choosing the access model, secrets store, or IAM boundary** a regime requires →
  `access-control-modeling`, `config-and-secrets-management`, `cloud-iam-boundary`. This
  skill names the control; those design it.
- **What to log and alert on** (audit logging for PHI, breach detection) →
  `observability-strategy`. This skill says an audit trail is required; that one designs it.
- **The code's own vulnerabilities** → `security-review`.
- **Dollar cost of a compliance program** (SOC 2 audit, pen test, cyber insurance) →
  `technical-cost-decision`.
- **Drafting the policy, terms, DPA, or BAA text** — not this skill; it names which
  documents exist and what each must cover. Counsel drafts or reviews the text.
- **An internal tool with no outside users and no personal data** — nothing to flag; say so.
- **A bare conceptual question** ("what is GDPR Article 22", "what does a BAA cover") —
  answered directly, no gate.
- **Contract review of an existing agreement** → `legal:review-contract`; **checking one specific action or feature against policy** → `legal:compliance-check`. Both where installed. This skill is the stage-based "what do we owe" list, not a review of a single document or change.

---

## The gate

Before producing any checklist, items 2–6 must be stated by the user and item 1 confirmed.
**Do not infer them.** If one is missing, name it and stop. A wrong data class or an unstated jurisdiction changes which
regime applies, so a guessed answer would send the whole checklist in the wrong direction.

**Facts you may surface from the repo / infra** (state for confirmation):

1. **What the app already collects and sends where** — schema fields, forms, analytics and
   error-tracker SDKs, third-party API calls (payments, email, LLM), logs. State what the
   code shows; the user confirms or corrects. Anything the code cannot show becomes an
   open question, not an assumption.

**Judgment calls that must come from the user, in their own words:**

2. **Data classes held** — ordinary personal data; financial; **health or health-adjacent**
   (symptoms, mood, cycles, medications, fitness tied to an identity); children's data or
   any chance of under-13/16 users; biometric; precise location; government IDs. "Some user
   info" is not an answer.
3. **User jurisdictions** — where users actually are: EU/UK, California and other US
   states, Canada, elsewhere, or a single country. Regimes follow the *user*, not the
   server or the company address.
4. **The operator's role** — for each data class: does the operator decide why and how the
   data is used (controller / "business"), or process it for a customer (processor /
   "service provider")? For health data, additionally: a HIPAA covered entity, a business
   associate of one, or a consumer app where the user enters their own data. This is the
   fork that decides the regime (see `health-data.md`).
5. **Customer type** — consumers only, businesses (B2B) or both; free, paid, or enterprise
   contracts. Business customers bring DPAs, security questionnaires, and SLAs.
6. **Stage and the next step** — prototype with test data / private beta / public launch /
   first enterprise deal / scaling. Name the next step on the ladder; the checklist is for
   that step and the one after.

"What legal stuff do I need for my app" with 2–6 absent is not valid input. The reply is the
list of what is missing, framed as the five things to commit to (plus a confirmation of what the code shows). **Pressure does not open the
gate** — "we're a tiny team", "just give me the standard list", "we'll sort it after launch"
are reasons to want it skipped. The fast path is items 2–6 in a sentence each; the cost of a
wrong data class is a regime missed (health data on an ad SDK is the usual one), not a
shorter list. Under a deadline or "don't ask me questions", still withhold the checklist but
do not reply with questions alone: lead with the **provisional flags** the surfaced facts
already raise, hedged ("if this is a consumer app, the FTC Health Breach Notification Rule and
state health-data laws still apply even without HIPAA"), plus the one or two time-sensitive
items, then the missing inputs as one-line answers. If they still won't answer, give a checklist
labelled provisional on stated assumptions (say which), never a verdict.

**SLA-only asks have a lighter gate.** When the question is only what uptime, credits or
support terms to promise (no data-handling question), the needed inputs are customer type,
stage, and the architecture facts; data classes and jurisdictions are not required. Go straight
to `sla-and-contracts.md`, and ask for the data inputs only if the contract needs a DPA or BAA.

---

## Challenge a proposed approach

If the user opens with a plan already made ("copy a privacy policy template, add a cookie
banner, done"), put it against the gate and flag the load-bearing gap as a question:

- **A template policy for data the app does not collect, or silent about data it does** —
  which data classes (item 2) does it name? (The after-the-fact check is `disclosure-gap-audit`.)
- **"We're not covered by HIPAA, so health rules don't apply"** — which fork of item 4? A
  consumer health app skips HIPAA, not the FTC Health Breach Notification Rule, state
  consumer-health-data laws, or GDPR special-category rules.
- **"Users are only in the US"** — which states? Washington, Nevada, Connecticut, California
  and others add rules; "US" alone is not a jurisdiction answer.
- **"We'll add deletion later"** — a deletion request must reach backups, logs, analytics,
  vendors, and AI training sets; retrofitting means finding all of them.
- **"99.99% uptime" in a contract** — against what architecture, measured how, with what
  credit? (The reachability math is `reliability-math`.)
- **"The vendor is compliant, so we are"** — a signed DPA or BAA with that vendor, on a tier
  that offers one, is the claim; a logo on their page is not.
- **Ad pixels or analytics on pages that hold sensitive data** — the most common live
  violation in health and finance apps.

---

## The process

Work `obligations-by-stage.md` (the data lifecycle, user rights, vendors, published
documents, stage ladder) in order once the gate is satisfied:

1. Restate the inputs and the regimes they implicate (jurisdiction × data class × role).
2. If health data is held, read `health-data.md` first — the HIPAA fork decides what follows.
3. Walk the checklist for the **next stage and the one after**, marking each item
   `build` / `sign` / `publish` / `decide` / `n/a — <reason>`.
4. If business customers are in play, walk `sla-and-contracts.md`: what the SLA may
   promise, what the DPA and BAA must cover, security attestations, and exit terms.
5. List every vendor that touches user data with the agreement it needs and whether the
   tier you use offers one.
6. Mark each item with **who confirms it**, and separate what the skill is confident
   about (mechanics, clocks) from what only counsel can settle.
7. Note which items are time-sensitive (a deletion path takes weeks to build; a SOC 2 Type II
   observation window looks backward).

Reference files:

- `obligations-by-stage.md` — data inventory, lawful basis and consent, user-rights
  mechanics and clocks, retention, vendors and transfers, breach response, children,
  published documents, and the stage ladder.
- `sla-and-contracts.md` — SLA anatomy (uptime, measurement, credits, exclusions),
  support terms, liability and warranty, DPAs, ownership and exit, attestations,
  auto-renewal, accessibility.
- `health-data.md` — the HIPAA fork, FTC and state consumer-health rules, GDPR Art. 9,
  what each forces in the design, and the vendor/BAA constraint.

---

## Output

**1. In chat, an obligations block:**

```
Inputs:            <data classes · jurisdictions · role (per class; HIPAA fork if health) · customer type · stage → next step>
Regimes flagged:   <each regime + the fact that raises it — flag only, no verdict>
Build now:         <controls the next stage needs: deletion/export path, consent record, audit log, encryption, retention job — each with the owning skill>
Sign:              <agreements: DPAs, BAAs, vendor terms — vendor, tier offering it, status>
Publish:           <documents: privacy policy sections, terms, cookie/consent UI, subprocessor list, status page>
SLA / contract:    <what may be promised; uptime basis; credits; liability cap; exit terms — or "no business customers yet">
Time-sensitive:    <items that take lead time and why>
Only counsel can settle: <questions the skill will not answer, each with who confirms>
Agent-drivable:    <what an agent can inspect — SDK and data-flow scan in the repo, header and cookie checks in a browser — vs what needs a human or vendor portal>
Revisit when:      <a concrete trigger — new region, health feature, first enterprise deal, new vendor, AI training on user data>
```

**2. On approval**, write it to `docs/legal/readiness/<system-slug>.md` (create the directory
if absent; where project docs live outside the project folder — here, the DevHiveMind docs
root per `conventions.md` — write it there). It is a living checklist, updated at each stage,
not an ADR. A decision inside it that is hard to reverse (picking a vendor tier for a BAA,
choosing to store health data at all) gets its own ADR from the skill that owns it.

Then hand off the build items one at a time (`access-control-modeling`,
`config-and-secrets-management`, `observability-strategy`, `data-tier-operations` for
backup and retention). After launch, `disclosure-gap-audit` checks the published documents
against the real product.

Stop before drafting legal text or implementing a control.

---

## Escape hatch

If the user has genuinely worked the inputs — data classes, jurisdictions, role, customer
type, and stage all stated — assemble the checklist directly rather than re-asking. A
complete opening message is the escape-hatch case. The flag-only rule and the "only counsel
can settle" list still apply; the escape hatch skips questions, not the caveat.

---

## Example invocations

> "I'm building a mood-tracking app. Users are in the US and EU. Free tier now, a paid
> tier planned. I'm the only developer and it's going into private beta next month."

Gate satisfied except role, which is only implied (consumer app, user enters own data → no
HIPAA fork, so controller): confirm it, then proceed. Regimes flagged: GDPR Art. 9 explicit
consent, FTC Health Breach Notification Rule, Washington My Health My Data and similar state
laws. Build now: consent record per purpose, deletion path reaching all stores, no ad or
analytics SDK on mood screens. Sign: DPAs with the cloud and email vendors. Publish: privacy
policy with a health-data section, separate consent for sharing. Only counsel can settle: whether
the app's features cross into a medical device claim.

> "What legal stuff do I need for my app?"

Gate not satisfied — no data classes, jurisdictions, role, customer type, or stage. Return
those five as the list of what is needed; do not hand over a generic checklist.

> "Our policy says we never share data but I think the analytics SDK does. Can you check?"

Does not fire: an existing policy checked against practice is `disclosure-gap-audit`.

---

## Portability

Needs no repo setup. Writes a living checklist to `docs/legal/readiness/` by default (follow
the repo's own convention); the dated facts in the reference files (fines, deadlines, rule
status) are as of the file's header date and are re-verified before they are relied on.

Depends on: `disclosure-gap-audit`, `design-scoping`, `reliability-math`, `access-control-modeling`, `config-and-secrets-management`, `cloud-iam-boundary`, `observability-strategy`, `data-tier-operations`, `technical-cost-decision`, `security-review`, `tech-decision-walkthrough`. If a named sibling isn't installed, say so and give the one-line answer inline instead of dropping the hand-off; when it is installed under a plugin namespace, hand off by that name. The load-bearing ones: no `disclosure-gap-audit` → state that the published documents still need checking against real behaviour and list the data flows to check; no `reliability-math` → nothing is lost before live telemetry exists (the series arithmetic is in `sla-and-contracts.md`); ask for measured uptime before promising a number; no `access-control-modeling` → name the control (per-tenant scoping, access logging) and leave its design open.

## Routing boundaries (full)

- Use when someone says "what do I need legally before launch", "do I need a privacy policy / terms / cookie banner", "do I need HIPAA", "does GDPR apply to us", "what do we owe users who ask for deletion", "what SLA should we offer", "an enterprise customer wants a DPA / BAA / SOC 2", "can I send health data to an LLM API", or "what changes legally as we grow".
- It is NOT for auditing a live policy against what the product does — "does our privacy policy cover this" is `disclosure-gap-audit`.
- It is NOT for scoping a system or recording the compliance regime as a constraint — that is `design-scoping`, which hands the unpacking here.
- It is NOT for the arithmetic of reachable uptime (`reliability-math`) or the cost of a compliance program (`technical-cost-decision`).
