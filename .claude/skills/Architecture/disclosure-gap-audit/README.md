# disclosure-gap-audit skill

A **pre-flight audit** that takes a shipped-or-shipping product together with its public
commitments — privacy policy, terms, cookie banner, marketing claims — and produces a
**findings register** of the gaps between what the product does and what it discloses or
secures. Three passes, deliberately unequal:

- **Spine — policy vs practice.** Fifteen probes for practices a policy commonly omits or
  discloses vaguely: AI/LLM processing of user input, model training on user data,
  automated decisions/profiling, named subprocessors, retention windows, completeness of
  the data-categories list, cross-site/cross-app tracking, children's data, international
  transfers, cookie categorization + preference center, biometric data, policy-vs-practice
  drift from bolt-on features, right-to-know mechanics, the CCPA/CPRA "sale" vs "share"
  distinction, and a missing effective-date / changelog. Each failed probe is a factual
  `policy-vs-practice-gap` finding.
- **Secondary — security design anti-patterns.** A fixed eight-probe list at design-review
  depth (secret in VCS, no authz check, IDOR, insecure defaults, missing rate limiting, PII
  in logs, encryption absent, over-broad third-party scopes). Not a code audit.
- **Flag-only — legal/compliance.** Age gate, accessibility, dark patterns, consent
  mechanics, IP/licensing. Output names the regime and routes to counsel; it never rules.

It **gates on a data inventory** (data flows, subprocessors, retention config, tracking
tech, AI features and where user input goes) — it will not infer the product's behaviour to
fill a gap. A missing inventory element is itself a finding and caps the pass that depends
on it; a partial inventory still runs on what's known; with nothing at all the register is
those gaps plus "no policy / no inventory" as finding #1.

It is **non-authoritative on every legal question** by design — the spine produces facts
("does X; policy says nothing about X"), the flag pass produces routed flags, neither
produces a verdict.

## Where it sits

```
design-scoping         →  state the compliance regime as an INPUT, before designing        (pre-design front door)
disclosure-gap-audit   →  audit an EXISTING design + its public claims for the gaps         (this skill — post-hoc)
      │
      ├─ policy language / product change to close a disclosure gap  →  (policy revision — named sections)
      ├─ the missing authz / IAM / secrets control                    →  access-control-modeling / cloud-iam-boundary / config-and-secrets-management
      ├─ limits for a missing-rate-limit finding                      →  resilience-strategy
      ├─ what's safe to log / emit                                    →  observability-strategy
      ├─ the changed code's own correctness                           →  security-review
      └─ every needs-legal-review row                                 →  qualified counsel / privacy officer / a11y specialist
learning-gate          →  classifies intent; its Step 3 "auditing a product/design against its privacy commitments" row defers here
```

The boundary that most needs stating: **`change-surface-audit` vs `disclosure-gap-audit`**.
`change-surface-audit` takes *one already-proposed concrete change* and asks what it breaks
elsewhere in the system, across six blast-radius surfaces (one of which is "security").
`disclosure-gap-audit` takes the *whole product against its whole policy* and asks what's
undisclosed or un-built. When a single change (a new analytics SDK, a new field) is on the
table, the "what breaks" half is `change-surface-audit` and the "what must we now disclose"
half is this skill — they compose, they don't compete.

## The shape

A procedure skill, not a Socratic gate — the same family as
`Architecture/change-surface-audit`, `Architecture/failure-mode-analysis`, and
`Documents/document-page-check`. It doesn't withhold judgment pending a user rep. It does
have a hard **input gate**: no findings register until the data inventory is supplied;
missing items become `inventory-incomplete` findings and cap the passes that depend on
them.

The walk:

1. Set scope (jurisdictions, which public docs exist) and the dated "current as of" caveat;
   log finding #1 if no policy exists.
2. Gate on the data inventory; write `inventory-incomplete` findings for holes.
3. Spine pass — 15 probes, classify each `disclosed-adequately` / `disclosed-inadequately` /
   `not-disclosed` / `n/a`.
4. Security pass — the eight design-review probes; each gap a `security-anti-pattern`
   finding with a fix handoff.
5. Legal/compliance pass — the flag list; each concern a `needs-legal-review` finding
   naming the regime and a human, never a verdict.
6. Assemble the findings register (ID · Category · Finding · Evidence · Severity · Who
   confirms this · Handoff), sorted by severity.
7. Recommend next actions per category, then stop.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point — when it applies / doesn't, the inputs (incl. the inventory gate), the 7-step walk, the output block. |
| `disclosure-checklist.md` | The spine pass: the 15 probes, each with what the product might do, what adequate disclosure looks like, the primary source, and the severity to assign; plus the B2B/workforce note, the "current as of" note on the volatile regimes, and the row-classification table. |
| `security-and-legal-passes.md` | The security probe list (8 rows, design-review depth, with fix handoffs), the legal/compliance flag list (5+ rows, flag-only phrasing rule), the severity definitions, and the findings-register format + file header. |

## What it produces

1. A summary block in chat: scope, "current as of" date, inventory status, spine tallies,
   findings by severity and category, the top 3–5, and the per-category recommendation.
2. **When the team wants it tracked**: a written register at
   `docs/compliance/disclosure-audit-<slug>-<date>.md`, with a header stating it is
   non-authoritative and that `needs-legal-review` rows require counsel. A one-off check
   gets only the chat block, same as `change-surface-audit`.

Stops before writing the policy language, building the controls, or obtaining the legal
review — those are separate, explicitly started steps that consume the register.

## When it does NOT apply

- Code-level vulnerability review of a diff → `security-review`.
- Blast-radius check of one concrete proposed change → `change-surface-audit` (its
  disclosure half, if any, comes back here).
- Stating a compliance regime before a design exists → `design-scoping`.
- Designing the authz / IAM / secrets model → `access-control-modeling` /
  `cloud-iam-boundary` / `config-and-secrets-management`.
- Whole-design operational failure enumeration / pre-mortem → `failure-mode-analysis`.
- The dollar cost of a compliance program → `technical-cost-decision`.
- A bare conceptual question ("what is GDPR Art. 22") → answered directly.
- The inventory was already supplied in the request → the input gate is satisfied on
  arrival; run the passes.

## Using it in another repo

Repo-agnostic. Writes an optional register to `docs/compliance/`.

```
cp -r ".claude/skills/Architecture/disclosure-gap-audit" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` whenever this skill or a sibling's description changes.
Known boundaries to hold:

- **vs `security-review`** — that built-in reads the changed code for its own defects; this
  skill's security pass asks whether a control *exists at all*, as one register row. A
  finding here ("no rate limiting on login") feeds `security-review` once the control is
  designed.
- **vs `change-surface-audit`** — one concrete change's blast radius vs. the whole product
  against the whole policy. They compose on a single change: "what breaks" there, "what
  must we disclose" here.
- **vs `design-scoping`** — pre-design (state the regime as a constraint) vs. post-hoc
  (audit the built thing against its claims). `design-scoping` should point here as the
  audit that closes the loop; this skill points back for a system with no design yet.
- **vs `access-control-modeling` / `cloud-iam-boundary` / `config-and-secrets-management`** —
  this skill flags the *absence* of a control (S1–S4, S7–S8 in `security-and-legal-passes.md`);
  those skills design it. One-way handoff out, with a pointer back for "where did this gap
  come from."
- **vs `failure-mode-analysis`** — FMA is a pre-mortem over operational failure modes
  across nine categories; this skill's security pass is a fixed eight-probe control
  checklist and its spine is about disclosure, not failure. They can both run on one system
  without stacking — different questions, different registers.
- **vs `learning-gate`** — `learning-gate` classifies intent and sets the ceiling; this
  skill owns the audit procedure. Don't stack the learning-rep questions on top of the
  inventory gate. A new Step 3 row in `learning-gate` defers the "audit a product against
  its privacy commitments" intent here.
- **vs `ambiguity-gate`** — "review my app" with no policy text, design doc, or inventory
  is `ambiguity-gate` first (what is even being reviewed); this skill takes over once a
  concrete product + its commitments are the established target.
