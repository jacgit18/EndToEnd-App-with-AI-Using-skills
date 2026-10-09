# Obligations by stage

Reference for `SKILL.md` steps 1, 3, 5 and 7. Facts here are **as of 2026-10** and flag-only:
re-verify any clock, threshold or rule status before relying on it, and route the verdict to
the person named in "Who confirms".

## Contents

- Data lifecycle checklist
- Lawful basis and consent
- User rights: mechanics and clocks
- Retention and deletion
- Vendors, subprocessors and transfers
- Breach response
- Children and age
- Documents to publish
- The stage ladder
- Who confirms what

---

## Data lifecycle checklist

Walk each row for every data class from gate item 2.

| Stage | Question | Control it implies |
|---|---|---|
| Collect | What is collected, from whom, for which stated purpose? Is each field needed for that purpose? | Data inventory; drop fields with no purpose (minimization). |
| Store | Where, in which region, encrypted how, who can read it? | Encryption at rest, per-tenant scoping (`access-control-modeling`), region choice. |
| Use | Is it used for anything beyond the collection purpose (analytics, ads, model training)? | Purpose limitation; a new purpose may need new consent. |
| Share | Which vendors or partners receive it, and under what agreement? | Subprocessor list, DPA / BAA per vendor. |
| Retain | For how long, and what deletes it? | A stated period plus a purge job, not just a policy line. |
| Delete | Can one user's data be found and removed from every store? | Deletion path covering primary DB, backups (or a documented expiry), logs, analytics, search index, vendors, AI training sets. |

An element nobody has written down is itself a finding: you cannot disclose or delete a data
flow you have not listed.

---

## Lawful basis and consent

- **GDPR** needs one of six lawful bases **per purpose**: consent, contract, legal
  obligation, vital interests, public task, legitimate interests. Most ordinary processing
  rides on contract or legitimate interests; consent is only one basis and the hardest to
  maintain.
- **Valid consent** is specific, informed, unbundled, as easy to withdraw as to give, and
  recorded (who, when, what text, which version). A pre-ticked box or a banner with no
  equally prominent reject button is not consent in the EU and is a dark-pattern risk in
  California and under FTC practice.
- **Special-category data** (health, biometric, sexual orientation, religion and others)
  generally needs explicit consent or another narrow Art. 9 condition.
- **US states** are mostly opt-out for ordinary data (sale, targeted advertising, profiling)
  and **opt-in for sensitive data** in several states. The list changes yearly; ask which
  states users are in rather than assuming "US".
- **Cookies and SDKs**: non-essential ones load only after consent where e-Privacy applies.
  Check what loads on first paint, before any banner is touched.
- **Global Privacy Control** signals are required to be honored as an opt-out in some states.

Who confirms: privacy counsel.

---

## User rights: mechanics and clocks

| Right | Where it comes from | Mechanic to build | Typical clock |
|---|---|---|---|
| Access | GDPR, CCPA/CPRA, other states | Export of everything held about the user | GDPR one month; CCPA 45 days (extendable once) |
| Portability | GDPR, several states | Machine-readable export | Same as access |
| Correction | GDPR, CPRA, others | Edit path; propagate to vendors | One month / 45 days |
| Deletion | GDPR, CPRA, others | Delete path across all stores (see below) | One month / 45 days |
| Opt out of sale / sharing / targeted ads / profiling | CPRA, other states | Toggle plus signal handling; stop the downstream flow | Promptly |
| Withdraw consent | GDPR | One-step withdrawal | Without delay |
| Appeal a refusal | Several US states | Appeal route and a response | Per state |

Also needed: **identity verification** proportionate to the data (a deletion request
accepted from an unauthenticated email address is an account-takeover path), and a
**request log** that proves what you did and when.

Who confirms: privacy counsel (clocks and exemptions); engineering owns the mechanics.

---

## Retention and deletion

- Pick a period per data class and write it down. "Until the account is deleted" plus a
  concrete number for what happens after (logs 30 days, backups roll off in 35) is an answer;
  "as long as necessary" is not.
- **Backups**: either delete from them or document that they expire on a fixed cycle and are
  not restored without re-applying deletions. Pick one deliberately.
- **Legal holds and statutory retention** (tax and financial records, some health records)
  override deletion for the covered data; record which data they cover.
- **AI features**: if user content trains or fine-tunes a model, deletion must also reach
  that, or the policy must say it cannot. Prefer not training on user content by default.

Build owners: `data-tier-operations` (backup and retention mechanics), `observability-strategy`
(what logs may contain).

---

## Vendors, subprocessors and transfers

For every vendor that touches user data — cloud, database host, email, analytics, error
tracker, payments, support desk, **LLM API** — record:

| Vendor | Data it sees | Agreement needed | Offered on the tier in use? | Trains on your data? | Region |
|---|---|---|---|---|---|

- **Controller-to-processor**: a DPA (GDPR Art. 28; CCPA service-provider contract terms).
  Many vendors publish a click-through DPA; confirm it is accepted for your account.
- **Health data in HIPAA scope**: a **BAA** with every vendor that handles PHI; many default
  or free tiers will not sign one (see `health-data.md`).
- **Transfers out of the EU/UK**: a mechanism is needed — Standard Contractual Clauses, the
  EU-US Data Privacy Framework for certified US vendors, or another. The DPF's legal footing
  has been challenged in court; check its current status.
- **Public subprocessor list** once you have business customers; they will ask for it and
  for notice of changes.
- **Over-broad access**: a vendor with standing access to the whole dataset for a narrow job
  is `cloud-iam-boundary`'s least-privilege question.

Who confirms: privacy counsel for transfer mechanism; engineering for the data-flow facts.

---

## Breach response

Needed **before** an incident:

- A named owner and a runbook: detect, contain, assess, notify, document.
- The notification clocks that apply, with who sends each notice:
  - GDPR: supervisory authority within **72 hours** of becoming aware; affected users
    "without undue delay" when high risk.
  - US states: every state has its own trigger, deadline and regulator list; ask which
    states users are in.
  - Financial data: the GLBA Safeguards Rule applies to financial institutions as defined,
    which can include some fintech and tax-prep services.
  - Health data: HIPAA (individuals within 60 days; HHS timing depends on size) or the FTC
    Health Breach Notification Rule for non-HIPAA health apps.
- A way to reach affected users (verified contact data) and a log of incidents and decisions.
- Customer contracts often set shorter notice (24–72 hours); the DPA is where it lands.

Who confirms: privacy counsel and whoever operates the system. Detection signals are
`observability-strategy`'s.

---

## Children and age

- **US COPPA**: under 13, verifiable parental consent for collection; applies to services
  directed at children or with actual knowledge of child users.
- **GDPR Art. 8**: consent age 13–16 depending on member state (16 by default).
- **UK Age-Appropriate Design Code** and several US state age-appropriate-design laws add
  default-privacy requirements for services likely to be used by minors.
- If there is no age screen and the product is general-audience with user-generated content
  or social features, assume minors will use it. Decide: gate, block, or design for them.

Who confirms: privacy counsel.

---

## Documents to publish

| Document | Must cover | When |
|---|---|---|
| Privacy policy | Data categories, purposes, bases, sharing/vendors, retention, rights and how to use them, transfers, contact, effective date | Before the first public user |
| Terms of service | Acceptable use, accounts, content license, disclaimers, liability cap, termination, governing law, changes | Before the first public user |
| Cookie / consent UI | Equal-prominence accept and reject, granular categories, recorded consent | Before the first non-essential SDK loads |
| Consumer-health-data policy | Separate, linked, where a state law requires one (see `health-data.md`) | Before collecting health data from covered users |
| Subprocessor list | Vendors, purposes, regions, change notice | First business customer |
| Security page / questionnaire answers | Controls actually in place, no aspirational claims | First business customer |
| Status page | Incident history, tied to the SLA measurement | Before offering an SLA |

The after-the-fact check that these match behaviour is `disclosure-gap-audit`.

---

## The stage ladder

| Stage | New obligations on top of the previous stage |
|---|---|
| Prototype, test data only | None beyond keeping real third-party data out of dev and out of screenshots. |
| Private beta with real users | Privacy notice and terms (even short), consent for anything non-essential, a deletion path (manual is fine), a named breach owner, age decision. |
| Public launch | Full policy and terms, consent UI, automated or runbooked rights handling, vendor DPAs, data inventory, retention job, breach runbook. |
| Users in new regions | Re-run the jurisdiction question: GDPR/UK, new state laws, transfer mechanism, local-language notices where required. |
| First business customer | DPA, subprocessor list, security questionnaire, SLA and support terms, uptime measurement, liability cap, insurance question. |
| Health or other sensitive data added | Re-run `health-data.md`; separate consent, BAAs where in scope, no ad SDKs on those screens. |
| Scale | Applicability thresholds (CCPA revenue/consumer counts), possible DPO or EU representative, DPIAs for high-risk processing, pen tests, SOC 2 Type II observation window, ongoing vendor review. |

---

## Who confirms what

| Question type | Who |
|---|---|
| Whether a regime applies, lawful basis, transfer mechanism, clocks and exemptions | Privacy counsel |
| Contract text: liability, indemnity, DPA, BAA | Commercial counsel |
| HIPAA status (covered entity / business associate / neither) | Healthcare privacy counsel |
| Data-flow facts, what a vendor receives | Engineering owner |
| Accessibility conformance | Accessibility specialist plus counsel |
| Breach classification and notice | Privacy counsel plus the incident owner |
