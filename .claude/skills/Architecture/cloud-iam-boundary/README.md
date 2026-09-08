# cloud-iam-boundary skill

A gated decision for **who or what gets access to a cloud resource and where that resource
sits on the network** — the principal, the least-privilege permission set, the trust
boundary and credential lifetime, any permissions boundary or org-wide SCP ceiling, and the
public/private network placement. Not the compute primitive a workload runs on (that's
`serverless-execution-model`), not edge/DDoS/rate-limiting defense (that's
`resilience-strategy`), not encryption or secrets management (unowned — name and defer), not
code-level vulnerability scanning (that's `security-review`).

Built from the `Architecture/02. Backing Service Options/Cloud/` notes — `IAM Principles.md`,
`Hierarchy of Policies in AWS.md`, `AWS/IAM Policies and Role Types in AWS.md`, `AWS/IAM Role
Creation Process.md`, `AWS/Managing IAM.md`, `AWS IAM Monitoring, Auditing, & Automation.md`,
`AWS/Server-less & Permission.md`, `AWS/serverless IAM Stuff.md`, `AWS/AWS Security Token
Service.md`, `AWS/VPC & IGW.md`, `AWS/AWS Shield.md`, and `Cloud Security Best Practices.md`.

## Where it sits

```
design-scoping            →  states the compliance regime / constraints this resource lives under
cloud-iam-boundary         →  who/what may act, what it may touch, what network segment it's in   (this skill)  → ADR
serverless-execution-model →  consumes the role this skill designs, for the compute primitive it chose
resilience-strategy        →  defends a resource this skill placed on the public internet (WAF, Shield, rate limiting)
observability-strategy     →  the alert design for the audit requirement this skill names
security-review            →  code-level vulnerabilities in the resource itself, a different altitude
```

## The shape

A gate skill. It refuses to recommend a policy or a subnet placement until the user supplies:

- **a concrete need** — a new resource needing access, an audit finding, a cross-account
  integration — never "best practice" alone
- **the exact principal** — a named person, pipeline, or specific compute resource, not "the
  service"
- **the specific actions and resources** — not "whatever it needs"
- **the credential mechanism and blast radius** — assumed role (default) vs long-lived keys,
  and what leaks if this credential is compromised
- **the trust boundary** — same-account, cross-account, or federated
- **network exposure** — public / private-outbound / fully private, answered on purpose
- **existing guardrails** — any permissions boundary or SCP this must fit inside
- **an audit/ownership requirement** — who's notified when this role changes, and who owns it

Then it walks the corrected policy-evaluation model (three nested ceilings — SCP, then
permissions boundary, then the identity ∩ resource-based grant, with cross-account requiring
both sides and explicit deny always winning), picks the least-isolated-necessary network
placement, and writes an ADR.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 3–10 from the user), challenge-the-proposal, output contract. |
| `iam-mechanics.md` | Policy types, the corrected evaluation model, principal types, ARN structure, STS/temporary-credential mechanics, least-privilege authoring practice, auditing the boundary. |
| `network-boundary.md` | VPC/subnet/IGW/NAT fundamentals, security groups vs NACLs, private connectivity options (peering, PrivateLink, Transit Gateway), the public-exposure decision tree. |

## Output

1. A recommendation block in chat (need, principal, credential mechanism, permissions policy,
   trust policy, boundary/SCP fit, network placement, blast radius, audit requirement,
   tradeoffs, follow-ups).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (a second, different consumer
   of this role; the calling code adds a new API call; the account joins an Organization with
   a new SCP; a new network path is needed).

Stops before implementation (the actual Terraform/CloudFormation/CDK, CloudTrail wiring,
policy simulator runs).

## Interaction with sibling skills

- **Feeds `serverless-execution-model`** — the execution role for whatever compute primitive
  that skill chooses is designed here first (or alongside it); this skill states the
  principal and the permission set, that skill states what runs under it.
  `skill-interaction-testing` confirmed this composes cleanly on a real end-to-end workload —
  no duplicate questions, each skill reused the other's facts.
- **Hands off to `resilience-strategy`** — a resource placed on the public internet by this
  skill's network-exposure decision still needs edge defense (WAF, Shield, rate limiting);
  this skill places it, that skill protects it. Confirmed clean sequential hand-off under test.
- **Hands off to `observability-strategy`** — the audit/change-notification requirement
  (item 10) is named here, designed there.
- **Distinct from `security-review`** — that skill scans code on a diff for vulnerabilities;
  this skill decides the account/network boundary the code runs inside, independent of
  whether the code itself is safe.
- **Consumes `design-scoping`** — a stated compliance regime (GDPR/HIPAA/PCI) from that
  skill's constraints section shapes how strict item 8 (network exposure) and item 6
  (credential lifetime) need to be. Also defers there outright for an unscoped, not-yet-designed
  system with no named resource yet — reciprocal pointer added both directions.
- **No skill owns encryption/secrets yet** — name the requirement (KMS, Secrets Manager
  rotation) and defer rather than improvising a design inside this skill's scope.

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `serverless-execution-model` (who designs the role vs who consumes it),
`resilience-strategy` (edge protection on a publicly-placed resource), and `security-review`
(altitude: account/network boundary vs code-level vulnerability).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside
`database-architecture` and reuses its `adr-template.md`. Written in AWS vocabulary
(IAM, VPC, SCPs); swap `iam-mechanics.md` and `network-boundary.md` for Azure RBAC/VNet or
GCP IAM/VPC vocabulary if this repo targets a different cloud — the gate items and process
carry over unchanged.

```
cp -r ".claude/skills/Architecture/cloud-iam-boundary" /path/to/other-repo/.claude/skills/
```
