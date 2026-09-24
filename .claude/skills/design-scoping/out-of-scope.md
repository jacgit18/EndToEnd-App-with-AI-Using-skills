# Design Scoping — out-of-scope hand-offs (full)

Full reasoning behind the one-line out-of-scope summary in `SKILL.md`. Read when a request sits near a boundary.

## Out of scope — hand these off

- **Working out what a vague request even asks for** — "help me with my system", "improve
  the architecture", "can you look at this" with no design intent established → `ambiguity-gate`.
  That skill resolves *which task this is*; this skill takes over once "design / architect a
  system or feature" is the settled intent. (Same split as `test-practice-gate` ↔
  `ambiguity-gate`.)
- **Judging or sizing a defined ticket** — "should this be in the sprint", "how risky is
  this ticket", "estimate this" → `ticket-evaluation`. That skill works a *specified* unit
  of work; this skill elaborates scope on an *under-specified* design ask.
- **The capacity numbers themselves** — turning "≈2M DAU" into QPS, storage, bandwidth,
  server count, and what binds first → `capacity-estimation`. This skill makes the user
  *state the non-functional targets*; that skill *derives the physical quantities* from the
  usage assumptions. Chain: scope here, size there.
- **Whether to split into services and where the boundaries go** → `microservices-decision`.
- **The API surface style** (REST / GraphQL / gRPC / events / streaming) → `api-interface-style`.
- **Where the source of truth lives and which store** → `database-architecture`.
- **The failure surface** — enumerating and ranking every way the design can break →
  `failure-mode-analysis`.
- **Who/what gets access to a resource, and its network placement** →
  `cloud-iam-boundary`, once a specific resource and principal exist to grant access to —
  this skill states the compliance regime (GDPR/HIPAA/PCI) that shapes how strict that
  skill's gate needs to be, not the grant itself.
- **What compute primitive runs a given unit of work** — Lambda vs container vs a
  long-running service, orchestration vs choreography → `serverless-execution-model`, once a
  specific operation exists to run, not for the system as a whole.
- **The deep design of the 1–2 chosen features** — this skill *selects* them (via the
  significance filter) and states why they matter; the actual design is the specialist
  skills above, run one at a time.
- **Cost of reversing a decision** — how expensive a choice is to change later →
  `technical-cost-decision`. The significance filter here uses *blast radius* (how much
  breaks if this changes), which is a different axis; don't duplicate the cost analysis.
- **Auditing a system that already exists and already makes public claims** — for the gaps
  between what a shipped product does and what its privacy policy / cookie banner / security
  posture disclose → `disclosure-gap-audit`. This skill states the compliance regime as an
  input *before* the design; that skill is the post-build audit that checks the built thing
  against its commitments. Scope here, audit there.
- **Walking the whole technology decision list candidate-by-candidate** — presenting the
  options, tradeoffs, and a recommendation for each stack choice, system-design-interview
  style, and recording an ADR per decision → `tech-decision-walkthrough`, downstream of this
  skill. This skill picks *which* one or two decisions deserve deep design and states the
  targets; it does not run the comparison for every choice. Chain: `design-scoping` →
  `tech-decision-walkthrough` → `spec-drift-gate` → `incremental-build-pacing`.
- **The delivery cadence of the build that follows** — building the scoped system slowly,
  one file at a time, so the user learns it → `incremental-build-pacing`, after
  `spec-drift-gate` turns this scope statement into a build spec and names the first slice.
  This skill scopes; that one paces delivery.
