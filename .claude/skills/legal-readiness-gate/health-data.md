# Health data

Reference for `SKILL.md` step 2. Health data is the highest-consequence class this skill
handles, and the regime depends on a fork about the operator's role, not on how sensitive the
data feels. Facts are **as of 2026-10**, flag-only; health-privacy counsel confirms.

## Contents

- The HIPAA fork
- Path A: HIPAA applies
- Path B: consumer health app, HIPAA does not apply
- GDPR and UK for health data
- What this forces in the design
- Vendors and the BAA constraint
- LLM and AI features with health data
- Claims and device regulation
- Other sensitive health categories
- Worked forks

---

## The HIPAA fork

Ask three questions, in order:

1. **Is the operator a covered entity** — a health-care provider that bills electronically,
   a health plan, or a clearinghouse? → HIPAA applies directly.
2. **Is the operator a business associate** — handling protected health information (PHI)
   *on behalf of* a covered entity or another business associate (a clinic's patient portal, a
   billing tool for providers, a hosted EHR add-on)? → HIPAA applies via a BAA.
3. **Neither** — users enter their own data in a consumer app with no covered entity
   involved (symptom, mood, cycle, fitness, medication reminders)? → HIPAA generally does
   **not** apply, and Path B governs. A consumer app can *become* a business associate the
   day a clinic or employer plan starts sending it data or paying for it on behalf of patients.

"Health-related" and "HIPAA-covered" are different things. Many products believe they are in
the second bucket and are not, and the reverse mistake is as common.

Who confirms: healthcare privacy counsel. Do not let the engineering team settle this alone.

---

## Path A: HIPAA applies

- **Privacy Rule**: use and disclosure of PHI only as permitted; minimum necessary;
  individuals' rights of access, amendment, and an accounting of disclosures.
- **Security Rule**: administrative, physical and technical safeguards, driven by a documented
  **risk analysis**: access controls, unique user IDs, audit controls (logs of who touched
  what), integrity controls, transmission security, encryption (addressable but treat as
  required), contingency plan and backups, workforce training, sanctions policy.
- **BAAs** with every vendor that creates, receives, maintains or transmits PHI for you,
  including cloud, database, email, logging, support and analytics tools, and subcontractors
  down the chain.
- **Breach Notification Rule**: notify affected individuals without unreasonable delay and no
  later than 60 days after discovery; notify HHS (immediately within the 60 days for 500+
  individuals, annually for fewer); media notice for large state-wide breaches.
- Enforcement is by HHS OCR and state attorneys general; penalties scale with culpability.
- The Security Rule update proposed in early 2025 (mandatory encryption, MFA, network
  segmentation, annual audits) may be in motion; check its status before designing to the old text.
- No HIPAA "certification" exists. Claim "HIPAA-compliant" only with documented safeguards,
  signed BAAs and a current risk analysis, and phrase it as a posture, not a certificate.

---

## Path B: consumer health app, HIPAA does not apply

You are still regulated, and recent enforcement targets exactly this category.

- **FTC Act §5**: promising privacy and then sharing health data is a deceptive practice.
  GoodRx (2023) and BetterHelp (2023) were both penalised for sending health-related data to
  advertising platforms contrary to their promises.
- **FTC Health Breach Notification Rule**: covers vendors of personal health records and
  related entities that fall outside HIPAA. The 2024 amendments make clear that health apps are
  covered and that an *unauthorised disclosure* (such as sharing with an ad platform without
  consent) counts as a breach. Notice to individuals and the FTC within 60 days (sooner for
  large events).
- **State consumer-health-data laws**: Washington's My Health My Data Act (separate consumer
  health data privacy policy, opt-in consent to collect and a separate authorization to share
  or sell, deletion right, geofencing limits, and a private right of action through the state
  consumer-protection act), Nevada's SB 370, and Connecticut's consumer-health-data
  provisions. More states add provisions each year; ask which states users are in.
- **Sensitive-data opt-in** under comprehensive state privacy laws (California, Colorado,
  Connecticut, Virginia and others) generally covers health diagnoses and, in some, reproductive
  and mental-health data.
- **State medical-privacy and reproductive-health laws** may add stricter rules (for example
  limits on disclosing reproductive-health data to out-of-state requests).
- Practical consequence: treat health data as opt-in for collection, separately opt-in for any
  sharing, and never route it to advertising or generic analytics vendors.

---

## GDPR and UK for health data

- Health data is **special-category data (Art. 9)**: processing is prohibited unless an Art. 9
  condition applies in addition to an Art. 6 lawful basis. For a consumer app the usual route
  is **explicit consent**; others include health-care provision by a professional under
  secrecy obligations.
- Processing health data at scale or systematic monitoring usually requires a **DPIA**
  before launch.
- Consent must be explicit, separable from the terms, and as easy to withdraw as to give.
- Health data is subject to stricter transfer, security and breach-notification handling; a
  breach likely meets the "high risk to individuals" bar, so users get notified as well as the regulator (72 hours).
- A DPO is required for large-scale processing of special-category data as a core activity.
- UK GDPR and the Data Protection Act 2018 follow the same pattern.

---

## What this forces in the design

| Control | Why | Owning skill |
|---|---|---|
| Classify and tag health fields at the schema level; segregate or separately encrypt them | Scopes access, logging, retention and deletion to the sensitive set | `relational-modeling`, `database-architecture` |
| Field- or record-level access with per-tenant scoping and no shared admin superuser | Minimum necessary / least privilege | `access-control-modeling` |
| Audit trail of reads, writes, exports and admin access to health data | HIPAA audit controls; evidence in an investigation | `observability-strategy` |
| **No health data in logs, error trackers, analytics events, URLs or query strings** | The commonest leak path | `observability-strategy` |
| **No ad pixels or generic analytics SDKs on pages that show or collect health data** | Source of the FTC and state enforcement | `disclosure-gap-audit` (check) |
| Encryption in transit everywhere and at rest, with managed keys and rotation | Security Rule; breach safe-harbour | `config-and-secrets-management` |
| Short retention and a tested purge across backups | Minimization; deletion rights | `data-tier-operations` |
| Separate consent records per purpose (collect vs share vs research) | Opt-in state laws and GDPR Art. 9 | build now; this skill |
| Breach runbook that names the health-specific clocks | 60-day and 72-hour clocks | this skill; `obligations-by-stage.md` |
| Region selection and data residency | EU and some state requirements | `cloud-iam-boundary` |
| De-identification standard if data is used for analytics or research | HIPAA Safe Harbor / Expert Determination; re-identification risk is real | counsel plus engineering |

---

## Vendors and the BAA constraint

This is the constraint that most often reshapes the architecture, so check it first.

- For every vendor on a PHI path, ask: **will they sign a BAA, and on which tier?** Many
  clouds sign one for specific eligible services only; many SaaS tools sign only on enterprise
  plans or not at all.
- If the answer is no, the vendor must not receive PHI: swap it, move the flow, or strip identifiers
  before the call.
- Free tiers and hobby plans usually exclude BAAs.
- Path B (no HIPAA) has no BAA requirement, but the same discipline applies as a contractual
  and promise-keeping matter: the vendor must not use health data for its own purposes.
- Record the answer in the vendor table in `obligations-by-stage.md`.

---

## LLM and AI features with health data

- Sending health data to a third-party LLM API is a **disclosure to a vendor**. Under HIPAA that
  requires a BAA with the provider on a tier that offers one and zero-retention / no-training
  settings; otherwise the data must not go there.
- Outside HIPAA, it is still a sharing event that the privacy policy and consent must cover.
- Prefer de-identifying before the call, minimising the context sent, and not logging prompts.
- Model outputs that influence care decisions raise clinical-safety and device-regulation questions
  (next section).
- If user content may train or fine-tune a model, that needs its own consent and a deletion story.

---

## Claims and device regulation

- Marketing claims are policed by the FTC: no unsubstantiated "treats", "diagnoses", or
  "prevents" claims.
- Software that diagnoses, treats, or drives clinical decisions can be a **medical device**
  (FDA Software as a Medical Device; EU MDR). General wellness and logging apps are often outside,
  but the line depends on the intended use claims, so wording is a regulatory decision.
- Telehealth, prescribing and licensed-professional features bring state licensing and
  e-prescribing rules.

Who confirms: regulatory counsel.

---

## Other sensitive health categories

- **Substance-use-disorder records** from federally assisted programmes: 42 CFR Part 2, stricter
  than HIPAA.
- **Mental-health and therapy notes**: heightened protection under HIPAA and many state laws.
- **Genetic data**: state genetic-privacy laws and consumer-genetics rules.
- **Minors' health data**: parental rights and consent vary by state and age.
- **Employer or insurer access**: do not expose health data to an employer or insurer sponsor without
  an explicit legal basis and consent.

---

## Worked forks

| Scenario | Fork | Regimes flagged | Key forced decisions |
|---|---|---|---|
| Solo-built mood tracker, users enter their own entries, US and EU | Path B | FTC HBNR, state consumer-health laws, GDPR Art. 9 | Explicit consent per purpose; no ad/analytics SDK on entry screens; deletion across all stores; DPIA question |
| Patient portal sold to clinics | Path A (business associate) | HIPAA, state laws, GDPR if EU patients | BAA with each clinic and each vendor; audit logging; risk analysis; breach clocks |
| Fitness app with steps and heart rate, no diagnosis | Path B, likely | FTC HBNR, state laws, GDPR (health-related) | Treat as sensitive; consent for sharing; watch wearable-vendor terms |
| Finance dashboard with no health fields | Not health | GLBA-flavoured safeguards, state privacy, breach notice | Out of this file |
| Consumer app later contracted by an employer wellness plan | Fork changes mid-life | Possibly HIPAA business associate | Re-run the gate at the contract, before data flows |
