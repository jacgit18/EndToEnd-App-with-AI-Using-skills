# Disclosure checklist — the spine pass

Reference for `SKILL.md` step 3. Fifteen probes. For each: what the product might be
doing, what an adequate disclosure looks like, the primary source that sets the
expectation, and the severity to assign when it's `not-disclosed` or
`disclosed-inadequately`.

This is a **gap checklist, not a legal opinion generator**. A probe that fails produces a
finding of the form *"the product does X; the policy says Y / nothing about X"* — a fact.
Whether that fact is a statutory violation is a `needs-legal-review` question, not
something to assert from this table.

## B2B / workforce products — who the data subjects are

When the product is sold to businesses and its records are about the customer's **employees**
(an HR tool, an expense app, a monitoring product), two things shift and the probes below
should be read with them in mind:

- **The customer is usually the controller and you are the processor.** Some of the fixes a
  failed probe points to land in the **customer-facing DPA and the subprocessor list**, not
  the public website policy — and adding a subprocessor (probe 3) or a profiling feature
  (probe 10) often triggers a contractual notice-and-objection window. Name that in the
  finding.
- **Employee data is in scope of privacy law.** California has treated employees and B2B
  contacts as "consumers" under CCPA/CPRA since 1 Jan 2023, and other regimes cover
  worker data directly. So probes 10 (profiling) and 14 (sale/share) apply to the
  customer's employees, not only to marketing-site visitors.

---

## "Current as of" — the volatile items

Record the audit date in the register. These move, and a checklist written today rots:

- **US state privacy laws.** California (CCPA/CPRA), plus a growing set of states with
  comprehensive statutes (Virginia, Colorado, Connecticut, Utah, Texas, Oregon, Montana,
  and more each year). Each has its own definitions and its own list of consumer rights.
  Do not enumerate "the states" from memory — name the ones in input 2's jurisdictions and
  flag the rest as "confirm current coverage."
- **CCPA/CPRA "sale" and "share."** "Share" is a defined term covering cross-context
  behavioral advertising; disclosing ad-tech data flows as neither a "sale" nor a "share"
  is a common and specific gap (probe 14).
- **EU AI Act.** Transparency duties for AI systems — telling users they are interacting
  with an AI, and disclosure around certain automated processing — are phasing in.
- **GDPR Art. 22 / automated decision-making** guidance continues to evolve, as does US
  state law on profiling and opt-outs.

When any probe touches these, the finding says "current as of `<date>`; re-check before
relying on this."

---

## The 15 probes

### 1. AI / ML processing of user input

| | |
|---|---|
| **Product might** | Send user text, images, audio, or files to a model — in-house or a third-party API (OpenAI, Anthropic, a cloud AI service) — for generation, classification, extraction, moderation, or embedding. |
| **Adequate disclosure** | States that user input is processed by AI/ML; if a third party, that a third-party AI provider receives it (ties to probe 3); the purpose; whether a human reviews outputs. |
| **Primary source** | GDPR Arts. 13–14 (identify processing and recipients); FTC guidance on AI claims; EU AI Act transparency duties. |
| **Severity** | **High** when user-submitted *content* goes to a third party undisclosed. **Medium** for an in-house model or a purpose-of-processing omission. |

### 2. Model training on user data

| | |
|---|---|
| **Product might** | Use user inputs, outputs, or interaction logs to train, fine-tune, or evaluate models — its own or by not opting out of a provider's training. |
| **Adequate disclosure** | States plainly whether user data trains models, which data, and how to opt out if an opt-out exists. |
| **Primary source** | GDPR purpose-limitation (Art. 5(1)(b)) — training is a distinct purpose; FTC actions on undisclosed training / "AI washing"; state-law "secondary use" provisions. |
| **Severity** | **High** — training is a purpose users do not assume, and unwinding a model trained on improperly disclosed data is expensive. |

### 3. Named third-party subprocessors / data sharing

| | |
|---|---|
| **Product might** | Send user data to analytics, advertising networks, cloud/hosting, email, customer support, payment, session-replay, and AI vendors. |
| **Adequate disclosure** | Names the categories of recipients and — where a regime or the product's own past promises require it — the specific vendors, or links a maintained subprocessor list. "We share with trusted partners" is not adequate. |
| **Primary source** | GDPR Art. 13(1)(e) (recipients or categories); CCPA/CPRA disclosure of categories of third parties; SOC 2 / DPA subprocessor-list norms. |
| **Severity** | **High** when a whole category is undisclosed (e.g. advertising, or an AI provider). **Medium** when categories are named but vague or the list is stale. |

### 4. Data retention and deletion

| | |
|---|---|
| **Product might** | Keep records indefinitely; keep backups past the "deletion" point; have no defined retention at all. |
| **Adequate disclosure** | States retention period or the criteria used to set it, per data category; states the deletion path, its timeline, and how backups are handled. |
| **Primary source** | GDPR Art. 13(2)(a) (retention period or criteria) and storage-limitation principle; CPRA retention-disclosure requirement. |
| **Severity** | **Medium** generally; **High** if the policy claims data is deleted on request but backups or a downstream store retain it. |

### 5. Categories of data collected — completeness

| | |
|---|---|
| **Product might** | Collect more than the obvious form fields: device and browser fingerprint, precise or coarse location, IP-derived data, behavioral event streams, and **inferred / derived** attributes (interests, risk scores, predicted demographics). |
| **Adequate disclosure** | Lists all categories including derived/inferred data and fingerprinting/location; does not stop at "name, email, and usage data." |
| **Primary source** | CCPA/CPRA enumerated categories (incl. "inferences"); GDPR "personal data" breadth incl. online identifiers (Recital 30). |
| **Severity** | **Medium**; **High** if precise location or biometric-adjacent data (probe 11) is collected and unlisted. |

### 6. Cross-site / cross-app tracking

| | |
|---|---|
| **Product might** | Load advertising or analytics pixels/SDKs that track users across other sites and apps; participate in an ad-tech graph; use third-party cookies for measurement. |
| **Adequate disclosure** | States that tracking occurs across other properties, names the mechanism (pixels, SDKs), and — under CPRA — treats it under "share" with an opt-out (probe 14). |
| **Primary source** | CPRA "cross-context behavioral advertising"; e-Privacy Directive consent-before-storage; Apple ATT / platform rules for apps. |
| **Severity** | **High** when undisclosed and an opt-out is legally expected; **Medium** when disclosed but not categorized. |

### 7. Children's / minors' data

| | |
|---|---|
| **Product might** | Knowingly or foreseeably have users under 13 (COPPA) or under 16 (GDPR default); collect data from them with no parental consent and no age gate. |
| **Adequate disclosure** | States the product's position on minors — not directed to children, or how it obtains verifiable parental consent, or the minimum age — and matches that to the actual age gate (or its absence, which is also a security/legal-pass flag). |
| **Primary source** | COPPA (US, under 13); GDPR Art. 8 (consent age, 13–16 by member state); UK Age Appropriate Design Code. |
| **Severity** | **High** — regulators act on children's-data gaps directly, and the policy being silent is itself notable. |

### 8. International data transfers

| | |
|---|---|
| **Product might** | Process or store data outside the user's jurisdiction — a US cloud region for EU users, a support team on another continent, an AI provider in a third country. |
| **Adequate disclosure** | States that data is transferred internationally, to which regions/countries broadly, and the safeguard relied on (SCCs, adequacy decision, Data Privacy Framework). |
| **Primary source** | GDPR Ch. V (Arts. 44–49); UK IDTA; state-law data-residency provisions where they exist. |
| **Severity** | **Medium**; **High** for EU/UK personal data moving to a third country with no safeguard named. |

### 9. Cookie / tracking-technology specifics

| | |
|---|---|
| **Product might** | Set cookies and similar storage across necessary / functional / analytics / advertising purposes, with only a generic "we use cookies" line and no preference control. |
| **Adequate disclosure** | Categorizes cookies by purpose, names the key ones or links a cookie table, and provides a working preference center; consent is obtained before non-essential storage where required. |
| **Primary source** | e-Privacy Directive (consent before storage); GDPR consent standard (Art. 7); EDPB guidance on consent banners / dark patterns. |
| **Severity** | **Medium**; **Low** if categorized and a preference center exists but isn't linked from the policy. |

### 10. Automated decision-making / profiling / scoring

| | |
|---|---|
| **Product might** | Rank, score, price, gate eligibility, moderate, or recommend using an algorithm whose output materially affects the user, with or without a human in the loop. |
| **Adequate disclosure** | States that automated decisions/profiling occur, the logic involved at a meaningful level, the significance and consequences for the user, and the right to human review where it applies. |
| **Primary source** | GDPR Art. 22 and Arts. 13(2)(f)/14(2)(g); state-law profiling opt-outs (Colorado, Connecticut, etc.); EU AI Act. |
| **Severity** | **High** when a decision affects access, price, or money and is undisclosed; **Medium** for ranking/recommendation with lower stakes. |

### 11. Biometric data

| | |
|---|---|
| **Product might** | Collect or derive faceprints, voiceprints, fingerprints, or other biometric identifiers — including from photos or audio uploaded for another purpose. |
| **Adequate disclosure** | Calls biometric data out **specifically** (not folded into "other data"), states purpose, retention, and that separate consent is obtained where required. |
| **Primary source** | Illinois BIPA (private right of action), Texas CUBI, Washington; CCPA/CPRA "sensitive personal information"; GDPR Art. 9 special category. |
| **Severity** | **High** — BIPA-style statutes carry statutory damages and a private right of action; a generic disclosure is treated as no disclosure. |

### 12. Policy-vs-practice drift (bolt-on features)

| | |
|---|---|
| **Product might** | Have shipped features — an AI assistant, a new integration, a referral system, a data export — after the policy was last written, so the policy describes an earlier product. |
| **Adequate disclosure** | Policy's substance matches the current feature set; the effective date is recent enough to be plausible given the release history. |
| **Primary source** | GDPR accuracy/transparency principles; FTC "unfair or deceptive" standard — a policy that no longer describes the product is a deception risk. |
| **Severity** | Two modes. **As a cause tag:** when the drift shows up as a specific gap caught by another probe (1, 3, 6, 10…), don't raise a duplicate row — annotate that probe's finding "cause: drift." **As a standalone finding:** when the pattern itself is the gap — the effective date is implausible given the release history, or several features are undocumented and no single other probe captures it — raise one `not-disclosed` row at the severity of the most serious undocumented feature (usually Medium–High). |

### 13. Right-to-know / rights-exercise mechanics

| | |
|---|---|
| **Product might** | State that users have access / deletion / correction / opt-out rights but give no working mechanism — no address, no form, no timeline, no identity-verification description. |
| **Adequate disclosure** | Names the method (email, form, toll-free number where required), the response timeline, the verification process, and any authorized-agent path. |
| **Primary source** | GDPR Arts. 15–22 + Art. 12 (facilitate exercise, respond within one month); CCPA/CPRA request methods and 45-day timeline. |
| **Severity** | **Medium** — rights that exist on paper but can't be exercised are a recognized enforcement target. |

### 14. "Sale" vs "share" vs neither (CCPA/CPRA)

| | |
|---|---|
| **Product might** | Pass data to ad-tech or analytics partners in a way that meets the CCPA "sale" definition (valuable consideration, not just money) or the CPRA "share" definition (cross-context behavioral advertising), while the policy says "we do not sell your data." |
| **Adequate disclosure** | Analyzes ad-tech flows against both definitions; if either applies, provides the "Do Not Sell or Share My Personal Information" mechanism and discloses it; the "we don't sell" claim is qualified accordingly. |
| **Primary source** | CCPA §1798.140(ad) ("sale"), CPRA "share" definition and opt-out; California AG / CPPA enforcement (e.g. the Sephora action). |
| **Severity** | **High** — a "we never sell your data" claim contradicted by pixel-based ad flows is both a disclosure gap and a deceptive-statement risk. |

### 15. Effective date and change history

| | |
|---|---|
| **Product might** | Publish a policy with no "last updated" date, or with a date but no summary of what changed, so a user cannot tell whether terms have moved or how. |
| **Adequate disclosure** | Carries a visible effective date and a short change log or "what changed" note for material revisions; a mechanism (email to account-holders, in-app notice) for announcing material changes. |
| **Primary source** | CalOPPA (effective-date requirement); GDPR transparency principle; general "material change" notice norms. |
| **Severity** | **Low** on its own — but it is what makes probe 12's drift invisible to users, so an absent effective date alongside a real drift finding is noted on that row too. |

---

## Classifying a row

| Classification | Test |
|---|---|
| `disclosed-adequately` | Specific, current, complete. A regulator reading the policy and then the product would not be surprised. No finding. |
| `disclosed-inadequately` | The practice is mentioned but the disclosure is vague, incomplete, or predates the feature. Finding, severity usually one band below the "not-disclosed" severity for that probe. |
| `not-disclosed` | The practice is real (confirmed in the inventory) and the policy is silent. Finding at the probe's stated severity. |
| `n/a` | The inventory confirms the product does not do this. Record the basis; do not leave the probe blank. |
| `inventory-incomplete` | The inventory doesn't say whether the product does this. Not a pass — a finding that the inventory has a hole, plus a note that this probe is unresolved. |
