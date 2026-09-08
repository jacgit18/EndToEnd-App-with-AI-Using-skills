# IAM Mechanics

The vocabulary and evaluation model behind the gate in `SKILL.md`. Written in AWS terms;
the concepts map directly onto Azure RBAC (role assignments, deny assignments, management
groups) and GCP IAM (roles, deny policies, organization policies) if this repo targets a
different cloud.

## Entities and policy types

| Concept | What it is | Attached to | Defines |
|---|---|---|---|
| **User** | A person or app with (ideally temporary, not long-lived) credentials | — | — |
| **Group** | A collection of users | Users | Nothing itself — a way to attach policies to many users at once |
| **Role** | An identity meant to be *assumed*, not logged into | — | — |
| **Identity-based policy** | JSON document granting actions on resources | Users, groups, roles | What the principal can do |
| **Resource-based policy** | JSON document on the resource itself | AWS resources (S3, SNS, SQS, Lambda, KMS keys) | Who can access this specific resource, and how |
| **Trust policy** | A specific resource-based policy that lives on a role | Roles only | Who may call `sts:AssumeRole` on this role — a separate question from what the role can do once assumed |
| **Permissions boundary** | A ceiling on maximum grantable permissions | Users, roles | The upper bound identity-based policies cannot exceed, regardless of what they grant |
| **Service Control Policy (SCP)** | An organization-wide ceiling | AWS accounts / OUs (via AWS Organizations) | The upper bound for every principal in the account, regardless of any policy below it |

A role is not "assigned" the way a policy is — it is *assumed*. Once assumed, the caller
receives temporary credentials scoped to whatever that role's identity-based policy allows,
constrained by any permissions boundary on the role.

## Corrected evaluation model

Source material in this vault's notes stated an evaluation order that mixed together
policies operating at different scopes ("identity-based → resource-based → trust →
permissions boundary → SCP") as if they were one linear list. That is not how AWS actually
evaluates a request, and treating it as a flat ordered list produces wrong predictions about
what a given combination of policies actually allows. The real model has three ceilings and
one grant, evaluated as nested scopes:

1. **Organization ceiling (SCP)** — if this account is in an AWS Organization, the applicable
   SCPs must allow the action, or nothing below matters. SCPs never grant; they only cap.
2. **Identity ceiling (permissions boundary)** — if the calling role or user has a permissions
   boundary attached, the boundary must allow the action, or nothing below matters. Boundaries
   never grant either; they only cap what the identity-based policy is allowed to grant.
3. **The actual grant — identity-based ∩ resource-based** — within both ceilings above:
   - **Same-account call**: an allow in *either* the caller's identity-based policy *or* the
     target resource's resource-based policy is sufficient (they are additive, not both-required).
   - **Cross-account call**: the caller's identity-based policy in their own account **and**
     the target's resource-based policy in the target account must *both* allow it. One side
     granting is not enough — this is the single most common cause of "I attached the policy
     and it still doesn't work" when the resource is in a different account.
4. **Assuming a role at all** is a separate question from what the role can do: the trust
   policy on the role must name the calling principal, and the caller must itself have
   permission to call `sts:AssumeRole`.
5. **An explicit `Deny` at any layer above wins**, unconditionally, over any `Allow` anywhere
   else in the evaluation. There is no "highest privilege wins" — deny is absolute.

The practical read: three separate ceilings (org, then identity) that only ever narrow, and
one grant that comes from the intersection of identity and resource policy (same-account) or
the AND of both sides (cross-account), with deny always winning. Draw this as three nested
boxes narrowing down to the grant, not a flat ordered checklist, when explaining it back to
a user.

## Principal types

| Principal | Example | Typical use |
|---|---|---|
| AWS account | `arn:aws:iam::111122223333:root` | Whole-account trust, usually too broad — prefer naming the specific role |
| IAM user or role | `arn:aws:iam::111122223333:role/MyRole` | The common case — one named identity |
| AWS service | `lambda.amazonaws.com`, `ec2.amazonaws.com` | A service assuming a role to act on your behalf (the role's trust policy names the service) |
| Federated identity | External IdP via Cognito or IAM identity federation | External users authenticated outside AWS, assuming a role with temporary credentials |

**Omit `Principal` entirely** in an identity-based policy (it applies directly to whatever
user/role it's attached to) and in an SCP (it applies to everything in scope by default).
Always include `Principal` in a resource-based policy or a trust policy — that's the whole
point of those two.

## ARN structure

```
arn:aws:<service>:<region>:<account-id>:<resource-type>/<resource-name>
```

S3 is the outlier — bucket ARNs omit the account ID and region entirely
(`arn:aws:s3:::my-bucket`, `arn:aws:s3:::my-bucket/key-prefix/*`). Everything else
(`lambda:...:function:Name`, `dynamodb:...:table/Name`, `states:...:stateMachine:Name`,
`sqs:...:QueueName`) follows the full pattern above.

## Temporary credentials over long-lived keys

`sts:AssumeRole` returns a temporary access key, secret key, and session token, scoped to
the assumed role's permissions and expiring on their own (typically 15 minutes to 12 hours,
configurable). This is why item 6 in the gate defaults every compute resource (Lambda, EC2,
ECS, cross-account access) to an assumed role rather than a static IAM user access key: a
leaked temporary credential is only useful until it expires; a leaked static key is useful
until someone notices and manually rotates it. The only legitimate reason to reach for a
long-lived key is a caller that structurally cannot assume a role — some legacy on-prem or
third-party tooling. Name that constraint explicitly; don't default to keys because they're
more familiar to write.

## Authoring least privilege

Start from the calling code, not a template. Read (or ask for) the actual SDK/API calls the
principal makes, and write the policy's `Action` list to match exactly those calls, with
`Resource` scoped to the specific bucket/table/prefix/function involved — never a bare
service wildcard (`s3:*`, `dynamodb:*`) unless the resource genuinely needs the full breadth
of a service's actions and that's stated as a deliberate choice, not a default for
convenience. Prefer **AWS-managed policies** for truly common, unmodified permission sets
(e.g. `AmazonS3ReadOnlyAccess` when read-only access to any bucket really is the requirement)
and **customer-managed policies** (not inline) for anything specific to this workload, so the
policy is visible, versioned, and reusable independent of the one role it happened to be
authored for.

## Auditing the boundary itself

A role or policy is not "done" once it's created — the requirement from gate item 10 is a
concrete, watchable signal: CloudTrail logging IAM/STS API calls, a metric filter on
`PutRolePolicy` / `AttachRolePolicy` / `CreateAccessKey` events, and a named severity (page
vs ticket) handed to `observability-strategy` for the actual alert design. Periodically run
IAM Access Analyzer (over-permissive policy findings) and Access Advisor (last-accessed data
to find permissions nobody's used) against existing roles — this is the mechanism that turns
"we did least privilege once" into "we still have least privilege," and it's the tool that
surfaces the audit findings that reopen this skill's gate on an existing role.
