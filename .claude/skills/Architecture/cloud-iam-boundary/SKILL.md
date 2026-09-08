---
name: cloud-iam-boundary
description: A gated decision for who or what gets access to a cloud resource and where that resource sits on the network — the identity (person, CI pipeline, compute role, cross-account caller, federated user), the least-privilege permission set (specific actions/resources, not a managed-admin policy or a wildcard), the trust boundary (which principal may assume the role, same-account vs cross-account, temporary STS credentials vs long-lived keys), any permissions boundary or org-wide SCP ceiling, and the network placement (public vs private subnet, security group / NACL rules, whether it needs an internet gateway or NAT at all). Use when someone says "what permissions does this Lambda/service need", "create an IAM role for X", "can this cross-account", "should this be public or private subnet", "we're locked down to AdministratorAccess and need to fix it", "an audit flagged an over-permissive role", "how do we let service A talk to service B", "does this need to be internet-facing", or proposes an access grant and wants it checked. It forces the user to state the triggering need, the principal, the specific resources/actions, the credential lifetime, and the network exposure before any policy or subnet placement is recommended, then records the outcome as an ADR. Not for the compute primitive or orchestration a workload runs on (Lambda vs Fargate vs Step Functions, retries, DLQs) — that is `serverless-execution-model`, which consumes the role this skill designs. Not for rate limiting, circuit breakers, or edge/DDoS mitigation placement (WAF, Shield) — that is `resilience-strategy`. Not for general encryption-at-rest of a datastore's disk, unrelated to config/secrets specifically — still unowned, name it and defer. Not for where a secret or config value lives and how it's rotated — that is `config-and-secrets-management`; this skill designs the grant authorizing a principal to read a secret once that skill has decided where it's stored. Not for whether encrypted, mutually-authenticated transport (mTLS) between services exists at all — that is `service-mesh-adoption`, which this skill's authorization policy can reference once that transport/identity exists. Not for scanning code for injection/XSS/auth bugs on a diff — that is `security-review`, a different altitude (code-level vulnerabilities, not the identity/network boundary a resource lives inside). Not for the alerting on IAM/config-drift events beyond naming the requirement — that is `observability-strategy`, which this skill hands the audit trigger to. Not for an unscoped, not-yet-designed system with no named resource or principal yet ("what roles should our new admin tool have") — that is `design-scoping` first. Not for application-level roles and permissions — which end user can view/edit/delete which resource inside the app, RBAC/ABAC/ACL model choice, or multi-tenant data isolation — that is `access-control-modeling`; this skill's principal is a service, pipeline, or cross-account caller reaching a cloud resource, not an application end user reaching an app resource.
---

# Cloud IAM & Network Boundary

Take a resource that needs to do something in a cloud account — a function that needs to read a bucket, a service that needs to call another service, a pipeline that needs to deploy, a person who needs console access — and decide exactly who may act as it, exactly what it may touch, how long that grant is trusted for, and what network segment it lives in. The skill makes the user name the concrete need and the specific principal, resource, and action before any policy is drafted, because "give it what it needs" and "make it public so it's simple" are the two ways this decision goes wrong, and both are cheap to state correctly up front and expensive to unwind once fifty resources reference the role.

## When to use

- Someone is **creating a new role or policy** — "what permissions does this Lambda need", "create a role for the CI pipeline to deploy", "the ECS task needs to read from S3 and write to DynamoDB".
- Someone needs **one identity to reach another** — cross-service (Lambda → DynamoDB), cross-account (Account A's function reading Account B's bucket), or federated (an external IdP assuming a role).
- Someone is deciding **network placement** — "does this need a public IP", "public or private subnet", "does it need a NAT gateway", "can these two services talk without going over the public internet".
- An **audit or incident** surfaced an access problem — "this role has `*:*`", "we found a public S3 bucket", "someone's static access key leaked", "an SCP is blocking something it shouldn't".
- Someone proposes a grant already-shaped and wants it checked — "just attach `AdministratorAccess`, it's faster", "let's make the bucket public so the frontend can read it directly", "one shared role for all our Lambdas".
- Someone is designing an **org-wide guardrail** — a permissions boundary or SCP meant to cap what any role in an account/OU can ever be granted.

## Out of scope — hand these off

- **The compute primitive and its orchestration** — whether the workload runs as a Lambda, a Fargate task, or a Step Functions workflow, and its retry/DLQ/failure-destination design → `serverless-execution-model`. That skill's execution role is what this skill designs; hand the finished role back to it.
- **Edge protection and overload defense** — WAF rules, AWS Shield, rate limiting, circuit breakers, and where each control sits in the request path → `resilience-strategy`. A public-facing resource this skill places still needs that skill's protection; name the hand-off, don't design the mitigation here.
- **Encryption and secrets** — KMS key policy, encryption-at-rest/in-transit, Secrets Manager rotation. No skill owns this yet in this catalog; name the requirement and defer rather than improvising a design.
- **Code-level security review** — injection, auth-bypass, unsafe deserialization, dependency CVEs on a diff → `security-review`. This skill decides the account/network boundary a resource lives inside, not whether its code is safe.
- **Alerting on the audit trail** — the SLI/alert design for "an IAM policy changed unexpectedly" beyond naming that the event must be watched → `observability-strategy`, which this skill hands the requirement (event name, severity, who's paged) to.
- **An unscoped, not-yet-designed system** — "what roles/access should our new admin tool have" with no named resource, principal, or data flow yet → `design-scoping` first, which sequences specific resources back here once the system's purpose and functional scope exist. This skill needs something concrete to grant access *to*.
- **Application-level authorization** — end-user roles and permissions, RBAC/ABAC/ACL/ReBAC model choice, per-instance or per-field access, multi-tenant isolation → `access-control-modeling`. That skill's principal is an application user; this skill's is a service, pipeline, or cross-account caller. They compose when one action needs both (an app "admin" role that also triggers an AWS console grant) — name both ADRs.
- **Implementation** — writing the actual Terraform/CloudFormation/CDK, wiring CloudTrail, running the policy simulator. The skill stops at the ADR.

---

## The gate

Before recommending a policy shape or a network placement, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **What already exists** — any IAM roles, policies, or Terraform/CloudFormation/CDK modules already touching this resource; the account's existing VPC layout if visible (default VPC vs custom, existing subnets).
2. **The resource type(s) involved** — Lambda, EC2, ECS/Fargate task, RDS, S3, a human IAM user, a CI runner — as far as the code or IaC shows.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

3. **The concrete need** — what triggered this: a new resource needs access to do X, an audit finding, a cross-account integration, a broken deploy. "Best practice says least privilege" or "let's just lock things down" is not a need — it is a reason to ask what specifically is over- or under-permissioned.
4. **The principal** — precisely who or what is acting: a named person, a CI/CD pipeline, a specific compute resource (which Lambda, which ECS task definition), a specific external account, or a federated identity via an IdP. "The service" is not precise enough if there are several.
5. **The resources and actions** — the specific AWS (or cloud) services and operations needed, not "whatever it needs" — e.g. `s3:GetObject` on one bucket prefix, not `s3:*` on `*`. If the user doesn't know yet, the answer is "find out from the calling code," not a wildcard placeholder.
6. **Credential lifetime and blast radius** — is this a long-lived credential (an IAM user's access keys, a static API key) or a temporary one obtained by assuming a role (STS)? What can an attacker reach if this credential leaks, and for how long is it valid? Long-lived keys on a human or a service are a finding to challenge, not a default.
7. **Trust boundary** — same account, cross-account, cross-organization, or third-party? If cross-account or federated, which entity is on the other side of the trust policy, and do they control what they claim to control?
8. **Network exposure** — does this resource need to accept inbound traffic from the public internet (needs a public subnet + internet gateway + a scoped security group), does it only need outbound internet access (private subnet + NAT), or does it need no internet path at all (private subnet, VPC-internal or PrivateLink only)? Default to the most isolated option that still does the job; "public because it's simpler to set up" is the failure mode this item exists to catch.
9. **Existing guardrails** — is there already a permissions boundary or SCP on this account/OU that caps what can be granted here? Does this grant need a *new* one because it's a pattern that will repeat (e.g. "every Lambda in this account should be capped at these services")?
10. **Auditability requirement** — does a change to this role/policy need to page someone, file a ticket, or just be visible in a periodic review? Who owns this role going forward, and who reviews it when the resource's job changes?

"Give the Lambda whatever it needs to run" or "let's use one shared role for now" with items 3–8 unanswered is not valid input.

**Urgency does not open the gate.** "We're blocked on deploy, just attach `AdministratorAccess` and we'll fix it later" is the single most common way an over-permissioned role becomes permanent — nobody circles back. Under real time pressure, naming the specific 3–5 actions this resource actually calls (items 5 and 6, one sentence) is faster than it sounds and is the only version of "unblock the deploy" that doesn't become a permanent finding on the next audit.

---

## Challenge a proposed approach

If the user opens with the grant already decided, put their reasoning under the gate, then test the specific claim against `iam-mechanics.md`:

- **"attach `AdministratorAccess`, it's faster"** — faster to grant, permanent to revoke (nobody schedules "tighten this later"). What are the actual 3–5 actions this resource calls (item 5)? A role scoped to those, even if it takes ten more minutes now, is the entire point of item 6 (blast radius).
- **"one shared role for all our Lambdas"** — if any one function's dependency changes, every function using the role gets the new permission whether it needs it or not, and a compromise of the least-trusted function grants everything the role can do. Role-per-function (or per-tightly-related-group) is the default; a shared role needs a reason (item 5 — do they genuinely all need the identical action/resource set?).
- **"make the bucket/API public, it's simpler"** — public means anyone, forever, until someone remembers to lock it down. What's the actual caller (item 4)? A same-account service, a specific known partner account, or truly the public internet? Only the last one is a public-resource question; the other two are a resource-based policy scoped to a principal (`iam-mechanics.md`) or a private network path (item 8).
- **"use long-lived access keys, roles are confusing"** — a leaked static key is valid until manually rotated or revoked; a role's temporary credentials (via `sts:AssumeRole`) expire on their own (item 6). The exception is a genuine external system that cannot assume a role (some legacy on-prem tooling) — name that constraint explicitly rather than defaulting to keys because they're familiar.
- **"just widen the SCP / permissions boundary, this one team keeps hitting it"** — a boundary exists because it's the ceiling for an entire account or OU (item 9); widening it for one team's convenience widens it for everyone under that boundary. The fix is usually a narrower boundary on the specific OU/role that needs more room, not loosening the shared ceiling.
- **"put it in the default VPC, don't overthink networking"** — the default VPC is fine for genuinely non-sensitive, throwaway workloads; anything handling real data or reachable from the internet needs the exposure question (item 8) answered on purpose, not by default. "We didn't think about it" is not the same as "we decided public is fine."

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `iam-mechanics.md` and `network-boundary.md` in order once the gate is satisfied. In short: confirm the need and identify the exact principal (items 3–4) → enumerate the specific actions and resources, resisting any wildcard that isn't justified (item 5) → choose the credential mechanism, defaulting to an assumed role via STS over long-lived keys (item 6) → write the trust policy naming exactly who may assume the role, and if cross-account, confirm both sides' policies (item 7) → decide network placement using the most-isolated-option-that-still-works rule (item 8) → check against any existing permissions boundary or SCP, or propose a new one if this is a repeating pattern (item 9) → name the audit/change-notification requirement and who owns the role (item 10) → recommend and record.

Reference files:

- `iam-mechanics.md` — the policy types (identity-based, resource-based, trust, permissions boundary, SCP) and what each is attached to and defines; the corrected evaluation model (SCP ceiling → permissions boundary ceiling → identity-based ∩ resource-based grant, cross-account requires both sides to allow, explicit deny anywhere wins); principal types and ARN structure; STS/`AssumeRole` mechanics and why temporary credentials beat static keys; least-privilege authoring practice (start from the calling code's actual calls, not a template).
- `network-boundary.md` — VPC/subnet fundamentals, public vs private subnet and what routes to an internet gateway vs a NAT gateway vs neither; security groups (stateful, instance-level) vs NACLs (stateless, subnet-level) and when each is the right tool; private connectivity options (VPC peering, PrivateLink, Transit Gateway) for reaching another VPC or account without the public internet; the public-exposure decision tree.

---

## Output

**1. In chat, a recommendation block:**

```
Need:                <the concrete trigger from gate item 3>
Principal:           <exactly who/what — person, pipeline, specific compute resource, cross-account entity, federated identity>
Credential mechanism: <assumed role via STS (default) | long-lived keys, with the specific constraint that forces this>
Permissions policy:  <specific actions + resources, e.g. "s3:GetObject on arn:...:my-bucket/uploads/*" — never a bare service wildcard without a named reason>
Trust policy:        <who may assume this role, and whether it's same-account or cross-account>
Permissions boundary / SCP: <existing ceiling this must fit inside, or "new boundary proposed for <pattern>", or "n/a">
Network placement:   <public subnet + IGW | private subnet + NAT (outbound only) | private subnet, no internet path> — with the security-group/NACL rule shape
Blast radius accepted: <what this credential can reach if leaked, and for how long>
Audit requirement:   <what event must be watched, at what severity, who owns this role — handed to observability-strategy>
Tradeoffs accepted:  <2–4 concrete costs: role-per-function sprawl, extra IaC to maintain, slower initial setup vs a shared/broad grant>
Not chosen because:  <one line per rejected shape — shared role, public bucket, long-lived keys, whichever was on the table>
Follow-ups:          <execution model this role attaches to → serverless-execution-model; edge/DDoS protection if internet-facing → resilience-strategy; encrypted transport between services (mTLS) → service-mesh-adoption; where the secret/config value itself lives and rotates → config-and-secrets-management; general at-rest encryption → name and defer; audit alerting → observability-strategy>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering). Reference any related `serverless-execution-model` or `resilience-strategy` ADR for the resource this role attaches to. Fill "Revisit when" with a concrete trigger — "this role is referenced by a second, meaningfully different function (split it)", "the calling code adds a new AWS API call (extend the policy, don't wildcard it)", "this account joins an AWS Organization with a new SCP (recheck the ceiling)", "the resource needs to be reachable from a new network path".

Then stop. Implementation — the actual Terraform/CloudFormation/CDK, wiring CloudTrail and the policy simulator — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the principal named, the specific actions enumerated from real calling code, the credential mechanism and network placement decided against a real exposure question — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "New Lambda `resize-thumbnails`, triggered by S3 `ObjectCreated` on `uploads/` in `my-app-media`, writes the resized file back to `derived/` in the same bucket, and needs to log to CloudWatch. No other calls. It's triggered async by S3, nothing else assumes this role. Bucket isn't public. No cross-account. This is a routine addition, not an audit finding — just want the role scoped correctly from the start."

Gate satisfied. Principal: the `resize-thumbnails` Lambda, no other caller. Actions: `s3:GetObject` on `arn:aws:s3:::my-app-media/uploads/*`, `s3:PutObject` on `arn:aws:s3:::my-app-media/derived/*`, `logs:CreateLogGroup`/`CreateLogStream`/`PutLogEvents` scoped to this function's log group — no `dynamodb:*`, no bare `s3:*`. Credential mechanism: assumed role, trust policy allows only `lambda.amazonaws.com` to `sts:AssumeRole`. No permissions boundary needed (no repeating pattern yet — note it as a candidate if a third similar function appears). Network: Lambda not in a VPC at all (no VPC-only resource it needs to reach), so no subnet/SG question applies — flag that adding VPC config later for, say, a private RDS call reopens item 8. Audit: role-change events → CloudWatch/CloudTrail alarm at ticket severity (not paging) → observability-strategy. ADR; revisit when this function calls a second AWS service.

> "Just give the deploy pipeline `AdministratorAccess`, we're blocked and need to ship today."

Gate not satisfied — item 3 (the actual blocker isn't named — what specific action is the pipeline failing on?), item 5 (no specific action/resource list). Response: ask what the pipeline is actually trying to do right now (deploy a Lambda? push to ECR? update a stack?) — that's usually 3–4 actions, nameable in one sentence, and scoping to those unblocks today just as fast as `AdministratorAccess` while not leaving a permanent finding. Do not recommend the broad grant.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Written from AWS IAM/VPC vocabulary (roles, policies, SCPs, security groups) but the gate items and process transfer directly to Azure RBAC/VNet or GCP IAM/VPC — swap the vocabulary in `iam-mechanics.md` and `network-boundary.md` if this repo targets a different cloud. Copy the `cloud-iam-boundary/` directory into another repo's `.claude/skills/` to use it there.
