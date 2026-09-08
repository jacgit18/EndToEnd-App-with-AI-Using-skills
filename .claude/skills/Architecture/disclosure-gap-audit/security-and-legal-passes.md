# Security pass, legal/compliance flag pass, and the register format

Reference for `SKILL.md` steps 4, 5, and 6.

The security pass is **design-review depth**: it asks whether a control *exists*, as one row
in a product-wide register. It is not a code audit and not a penetration test — a specific
handler's correctness is `security-review`'s job, and exploit development is out of scope
entirely.

The legal/compliance pass is **flag-only**: it produces `needs-legal-review` findings that
name a regime and route to a human. It never asserts a violation.

---

## Security pass — the fixed probe list

Walk every row. For each: does the product have this control, based on the design doc and
the inventory? A gap is a `security-anti-pattern` finding with the handoff shown.

| # | Probe | What a gap looks like | Severity | Fix handoff |
|---|---|---|---|---|
| S1 | **Secrets in version control** | API keys, DB passwords, signing keys, `.env` files committed; a key in the git history even if later removed. | **High** | `config-and-secrets-management` (where it should live + rotation); rotate the exposed key now. |
| S2 | **Resource with no authorization check** | An endpoint, job, or admin surface that checks *authentication* but not *whether this caller may act on this object*. | **High** | `access-control-modeling` (the model); `security-review` (the code once designed). |
| S3 | **IDOR — unscoped object references** | `/invoice/1234` returns any invoice; sequential or guessable IDs with no per-caller scoping; a file URL with no signature or ownership check. | **High** | `access-control-modeling`; `security-review`. |
| S4 | **Insecure defaults** | Public-by-default sharing, world-readable buckets, permissive CORS (`*` with credentials), debug/admin endpoints reachable in prod, default credentials unchanged. | **High / Medium** | `cloud-iam-boundary` (resource exposure + network placement); `config-and-secrets-management` (default config). |
| S5 | **Missing rate limiting** | No throttle on login / password-reset / OTP / signup, or on expensive endpoints (search, export, an AI call). Enables credential stuffing, enumeration, cost-amplification. | **Medium** | `resilience-strategy` (limits + backpressure). |
| S6 | **PII in logs or analytics** | Full request bodies, tokens, emails, or the contents of a user message written to application logs, an error tracker, or an analytics event. | **Medium / High** | `observability-strategy` (what's safe to emit); scrub before shipping to any third party (ties to `disclosure-checklist.md` probes 1, 3, 6). |
| S7 | **Encryption absent** | Plaintext transport on any user-data path (internal service hops included); sensitive fields or backups unencrypted at rest. | **High** for external transport; **Medium** for at-rest gaps. | `cloud-iam-boundary` / platform config; note it, don't design the crypto here. |
| S8 | **Over-broad third-party permissions** | An OAuth integration requesting far more scope than it uses; a vendor with standing access to a whole dataset for a narrow job; a long-lived API key where a short-lived token would do. | **Medium** | `cloud-iam-boundary` (least privilege, credential lifetime). |

Mark a probe `n/a — <reason>` rather than skipping it. A probe you can't answer from the
inputs is `inventory-incomplete`, not a pass.

**When no design doc or architecture description was supplied**, every probe is
`inventory-incomplete` and eight near-identical rows add no signal. Instead emit **one
bundled `inventory-incomplete / security-anti-pattern` finding per theme**, each phrased as
the questions to answer and naming the probes it covers:

- **Tenant isolation & object scoping** (S2, S3) — is there an authorization check that the
  caller owns / their tenant owns the resource; are file URLs signed and ownership-scoped.
- **Data egress to third parties & logs** (S6, S8) — does PII / user content reach
  analytics event properties, an error tracker, or an over-broad vendor destination.
- **Abuse & cost controls** (S5) — rate limiting on auth endpoints and on any
  expensive/third-party-call path.
- **Key & crypto hygiene** (S1, S7) — where the secrets live and their rotation; transport
  and at-rest encryption on user-data paths.

Set *Who confirms this* on these to the product/engineering owner who holds the inventory.

**Out of the security pass entirely:** the correctness of a specific piece of code (an
injection bug, an unsafe deserialize, a broken auth-token comparison) → `security-review`.
This pass would say "the login endpoint has no rate limiting and no documented lockout"
(a design gap); `security-review` would say "this token comparison is not constant-time"
(a code defect).

---

## Legal / compliance pass — the flag list

For each concern: state the **observable fact**, name the **regime(s)** given the
jurisdictions in `SKILL.md` input 2, set **Who confirms this**, and stop. Every row is a
`needs-legal-review` finding. Phrasing rule: *"the product does X; [regime] implications;
confirm with [reviewer]"* — never *"the product violates [regime]"*.

| # | Flag | Observable fact that raises it | Regimes it implicates | Who confirms |
|---|---|---|---|---|
| L1 | **Age gate** | Product collects birthdate / targets a general audience / has UGC and social features, with no age screen. | COPPA (US <13), GDPR Art. 8 (<16 default), UK AADC. | Privacy counsel. |
| L2 | **Accessibility** | No evidence of WCAG conformance; known issues (no alt text, keyboard traps, contrast failures) in core flows. | ADA Title III (US case law), Section 508 (US public sector), EN 301 549 / EU Accessibility Act. | Accessibility specialist + counsel. |
| L3 | **Dark patterns** | Consent banner with no equally-prominent "reject"; cancellation flow harder than signup; pre-checked opt-ins; "confirmshaming" copy. | FTC Act §5, CPRA (dark-pattern-obtained consent is not consent), EDPB banner guidance. | Privacy counsel + design review. |
| L4 | **Consent mechanics** | Non-essential cookies/SDKs load before consent; no consent recorded for a purpose a regime requires it (marketing, sensitive data, minors). | e-Privacy Directive, GDPR Art. 7, state sensitive-data opt-ins. | Privacy counsel. |
| L5 | **IP / licensing** | Training data of unknown provenance; user content re-licensed by the terms more broadly than the product needs; third-party content or code with license obligations (attribution, copyleft) not met. | Copyright law, open-source license terms, the product's own ToS grant. | IP counsel + engineering. |

Add a row for any other regime the jurisdictions raise that the passes above don't cover
(HIPAA if health data, GLBA if financial, PCI-DSS if card data, sector rules) — same
flag-only treatment: name it, state the fact, route to counsel.

---

## Severity definitions (all three categories)

| Severity | Meaning |
|---|---|
| **High** | An undisclosed practice or missing control a regulator or plaintiff could act on directly, or that contradicts an explicit public promise. Examples: undisclosed sale/share of data, undisclosed model training on user content, silent processing of minors' data, a live secret in a public repo, no authz check on a resource exposing other users' data, a "we never sell your data" claim contradicted by ad pixels. Fix before the next release or the next external review. |
| **Medium** | A disclosure that is inadequate or outdated, or a control that is weak but not currently exposed, or a flag that plausibly needs counsel but isn't obviously live. Examples: a vague subprocessor list, a missing retention number, rate limiting absent on a non-auth endpoint, an accessibility gap outside core flows. Fix on a near-term plan with an owner. |
| **Low** | A best-practice or cosmetic gap with little standalone exposure. Examples: no effective-date/changelog on the policy, a preference center that exists but isn't linked, generic-but-not-wrong cookie language. Log and batch. |

An `inventory-incomplete` row takes the severity of the *worst case* the unknown could be,
and is marked so — it sorts with its band but is visibly unresolved.

---

## Findings register format

One table, sorted by severity (High → Low), then by category.

| ID | Category | Finding (observable fact) | Evidence | Severity | Who confirms this | Handoff |
|---|---|---|---|---|---|---|
| DGA-001 | policy-vs-practice-gap | Support messages are sent to a third-party LLM API; the privacy policy does not mention AI processing or the provider. | Inventory: AI feature #2, provider = <name>, their API. Policy: "How we use your data" — no AI/ML reference; last updated <date>. | High | Privacy counsel (confirm provider data-use terms) | Policy revision — "How we use data", "Who we share with" |
| DGA-002 | security-anti-pattern | The `/export/{userId}` endpoint authenticates the caller but does not check the caller owns `userId`. | Design doc §4; no scoping in the handler description. | High | — (design gap, not a legal question) | `access-control-modeling`; then `security-review` on the code |
| DGA-003 | needs-legal-review | Product collects birthdate and has UGC features; no age gate. | Inventory: data flows — birthdate collected at signup; no age screen in the flow. | High | Privacy counsel | COPPA / GDPR Art. 8 — flag only |

- **ID** — `DGA-001`, stable across revisions.
- **Category** — exactly one of `policy-vs-practice-gap` / `security-anti-pattern` /
  `needs-legal-review` (plus `inventory-incomplete` as a prefix note where it applies).
- **Finding** — the observable fact, concrete enough to act on. Not a conclusion of law.
- **Evidence** — the inventory item *and* the policy text (or "policy silent"), or the
  design-doc reference. This column is what makes the finding checkable.
- **Who confirms this** — counsel / privacy officer / accessibility specialist for a
  `needs-legal-review` row (name a human, never leave blank); the product/engineering owner
  who holds the inventory for an `inventory-incomplete` row; "—" for a pure design gap with
  a clear internal owner already named in the handoff.
- **Handoff** — the skill or team that owns the fix: policy revision (name the sections),
  `access-control-modeling`, `cloud-iam-boundary`, `config-and-secrets-management`,
  `resilience-strategy`, `observability-strategy`, `security-review`, or a named reviewer.

### Register file header (when written to `docs/compliance/`)

```
# Disclosure gap audit — <product/surface> — <date>

NON-AUTHORITATIVE. This register states factual gaps between what the product does and what
it discloses or secures. It does not determine that anything is unlawful. Every
`needs-legal-review` row requires review by qualified counsel before any conclusion is
drawn. Compliance items are current only as of <date> — the US state-law patchwork, the
CCPA/CPRA sale-vs-share treatment, and the EU AI Act are moving; re-check before relying.

Jurisdictions in scope: <...>
Documents reviewed: <...>
Data inventory: <complete | incomplete — missing: ...>
```
