# SLAs and contract terms

Reference for `SKILL.md` step 4. Applies once a business customer or a paying consumer tier
exists. Flag-only: commercial counsel confirms contract text; the numbers come from the
architecture, not from the contract template.

## Contents

- SLA anatomy
- Promise only what the architecture can hit
- Support terms
- Liability, warranty and indemnity
- Data processing agreement (DPA)
- Ownership, licence and exit
- Security attestations
- Auto-renewal and cancellation
- Accessibility commitments
- Contract checklist by customer type

---

## SLA anatomy

An SLA is a promise with a measurement and a remedy. Every part must be written down.

| Part | Decide | Common failure |
|---|---|---|
| **Metric** | Availability of what — the API, the web app, one feature? Error-rate and latency commitments, or uptime only? | "The service" with no scope; a promise that covers components you do not control. |
| **Measurement** | Who measures, where from, over what window (monthly), how a partial outage counts (error rate over a threshold counts as down?) | Measuring only a health-check endpoint while checkout is broken. |
| **Target** | A number per tier (e.g. 99.5 / 99.9 / 99.95) | A number copied from a competitor, not from the design. |
| **Exclusions** | Scheduled maintenance (with notice), force majeure, customer-caused, third-party outages | Exclusions so broad the SLA never triggers. |
| **Remedy** | Service credits as a percentage of the monthly fee at defined thresholds; sole remedy or not; how a credit is claimed | Automatic credits you have no way to compute. |
| **Reporting** | Public status page, post-incident reports within a stated time | Promising a report without an incident process. |

Rough monthly downtime budgets: 99.0% ≈ 7.3 h, 99.5% ≈ 3.6 h, 99.9% ≈ 43 min, 99.95% ≈ 22 min,
99.99% ≈ 4.4 min. (SLA = what you promise customers; **SLO** = the stricter internal target
that protects it; **SLI** = the measured signal. Set the SLO tighter than the SLA.)

---

## Promise only what the architecture can hit

- An SLA is capped by the weakest serial dependency. Components in series multiply: the
  whole is available only when every part is. Redundant parallel copies combine as
  1 − (1 − a)ⁿ, but only if failover actually works. Example: one app server (99.9%) ×
  one database host (99.9%) × one region/network (99.95%) ≈ 99.75%, about 1.8 hours a month,
  so 99.99% (about 4 minutes) is not promisable on that design. These are illustrative inputs;
  use the vendors' published or your measured figures.
- Single points of failure to remove first: `failure-mode-analysis`. Once there is live
  telemetry (SLO burn, percentiles), `reliability-math` takes over.
- Your upstream vendors' own SLAs bound yours; read them and note what they exclude.
- You need the measurement **before** you offer the SLA: signals, a status page, an on-call
  owner (`observability-strategy`). A promise nobody is measuring is a liability.
- Start with an SLO and publish a "target" with no credits while you collect a few months of
  data; convert to a contractual SLA when the history supports it.

---

## Support terms

Separate from uptime. Define:

- Severity levels with examples (S1 outage, S2 degraded, S3 minor, S4 question).
- **Response** time per severity (first human reply) and, where offered, **resolution/update**
  cadence.
- Support hours and channels, and what the tier includes.
- An escalation path and a named contact for incidents.

A one-person team can still commit to "S1 acknowledged within 4 business hours" — the commitment
must match who is on call.

---

## Liability, warranty and indemnity

Counsel territory; know the vocabulary so you can see what is being asked:

- **Limitation of liability**: usually capped at fees paid in the prior 12 months, with
  carve-outs customers push on (data breach, confidentiality, IP infringement, gross
  negligence). "Super-caps" for data breach (a multiple of fees) are common in enterprise deals.
- **Warranty disclaimer**: "as is" for consumer terms; limited warranties for B2B.
- **Indemnity**: who covers third-party IP claims or data-protection fines, and whether yours is
  capped.
- **Insurance**: enterprise buyers may ask for cyber-liability and tech E&O cover with stated limits.
- **Governing law and venue**, and arbitration for consumer terms where used.

---

## Data processing agreement (DPA)

When you process personal data on behalf of a business customer, you are their processor and
they will ask for a DPA (GDPR Art. 28). It normally covers:

- Scope: subject matter, duration, data types, data subjects.
- Process only on documented instructions; confidentiality of staff.
- Security measures (annex), often tied to a named standard.
- **Subprocessors**: list, notice of changes, right to object, flow-down of the same terms.
- Assistance with user-rights requests and DPIAs.
- **Breach notice** to the customer within a stated time (24–72 hours is typical).
- Return or deletion of data at termination, and audit rights.
- Transfer mechanism for data leaving the EU/UK.

A **BAA** is the HIPAA equivalent when PHI is in scope (`health-data.md`).

---

## Ownership, licence and exit

- Customers own their data and content; you take only the licence needed to run the service.
  A broad licence "to improve our services" is where AI-training rights get granted by accident.
- State whether customer data trains any model; many enterprise buyers require "no".
- **Export** at any time and at termination, in a usable format, within a stated window.
- **Deletion** after termination on a stated schedule, with certification on request.
- Open-source dependencies: copyleft (GPL/AGPL) obligations can reach a hosted service;
  keep a licence inventory and meet attribution requirements.

---

## Security attestations

| Evidence | What it is | Lead time |
|---|---|---|
| Security questionnaire (SIG, CAIQ, custom) | Self-attested answers | Days; answers must be true |
| Pen test summary | Third-party test, remediation noted | Weeks |
| SOC 2 Type I | Controls designed properly at a point in time | Months of preparation |
| SOC 2 Type II | Controls operated effectively across an observation window (typically 3–12 months) | Longest; the window looks backward, so start collecting evidence early |
| ISO/IEC 27001 | Certified ISMS | Months |
| HIPAA | No official certification; a risk analysis, policies and safeguards you can document, optionally assessed by a third party | Ongoing |

Never claim "SOC 2 compliant" or "HIPAA compliant" for something not independently attested
or documented; the claim itself becomes the exposure. Compliance-automation tooling can cost
money — record it in the project's paid-options doc (cost sizing is `technical-cost-decision`).

---

## Auto-renewal and cancellation

- State renewal terms, price changes and notice clearly at signup.
- Cancelling must be at least as easy as subscribing. The FTC's 2024 "click-to-cancel" rule
  was struck down by a federal appeals court in 2025, but ROSCA, FTC Act §5 enforcement and
  many state auto-renewal laws remain; re-verify current status.
- Confirmation email for trials and renewals; a reminder before a paid conversion where a state requires it.

---

## Accessibility commitments

Public-facing apps face ADA Title III claims in the US and the European Accessibility Act
(in force since June 2025) for covered consumer services in the EU. A conformance claim
needs manual evidence; a Lighthouse or axe score is regression evidence only. This repo's
standing policy is in `.claude/rules/web-accessibility-and-lighthouse.md`.

---

## Contract checklist by customer type

| Customer | Needs |
|---|---|
| Consumer, free | Terms, privacy policy, acceptable use, content licence. |
| Consumer, paid | Above plus billing terms, refunds, auto-renewal disclosures, cancellation path. |
| Small business | Above plus a lightweight SLA / support commitment and a DPA on request. |
| Enterprise | MSA, SLA with credits, DPA, security questionnaire, subprocessor list, pen test/SOC 2 path, liability negotiation, insurance proof, possibly BAA, exit and data-return terms. |
