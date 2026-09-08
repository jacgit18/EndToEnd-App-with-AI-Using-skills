# Network Boundary

The vocabulary and decision tree behind gate item 8 (network exposure) in `SKILL.md`.

## VPC fundamentals

A **VPC** (Virtual Private Cloud) is a logically isolated network within the cloud account.
By default, nothing inside it can reach or be reached by the internet or another VPC — every
path in or out is something you explicitly configure. Inside a VPC:

- **Subnets** carve up the VPC's IP range, typically across multiple availability zones for
  redundancy. A subnet is "public" or "private" purely by virtue of its route table — nothing
  else makes it so.
- **Route tables** decide where traffic goes. A subnet is **public** if its route table sends
  `0.0.0.0/0` (internet-bound traffic) to an **Internet Gateway (IGW)**. A subnet is
  **private** if it has no such route, or routes internet-bound traffic to a **NAT Gateway**
  sitting in a public subnet instead.
- **Internet Gateway (IGW)** — allows two-way traffic between a subnet and the public
  internet. Anything in a subnet routed to an IGW is potentially internet-reachable if its
  security group also allows the inbound traffic.
- **NAT Gateway** — allows **outbound-only** internet access for resources in a private
  subnet (e.g. a Lambda-in-VPC or an ECS task pulling a package or calling an external API)
  without making them reachable *from* the internet.
- Every AWS region ships a **default VPC** with a default public subnet, IGW, and permissive
  security group already wired up. It's fine for genuinely throwaway or non-sensitive
  workloads and for quickly unblocking local development; it is not a substitute for
  deliberately answering item 8 for anything handling real data or reachable from real
  traffic. Don't delete it reflexively either — some AWS services and third-party tools
  assume it exists — just don't treat "it's the default" as the same decision as "we decided
  public is fine here."

## Security groups vs NACLs

| | Security Group | Network ACL (NACL) |
|---|---|---|
| **Scope** | Attached to a resource (instance, Lambda ENI, RDS instance) | Attached to a subnet — applies to everything in it |
| **State** | Stateful — a reply to an allowed request is automatically allowed back | Stateless — inbound and outbound rules must each be defined explicitly |
| **Rule type** | Allow rules only | Allow and explicit Deny rules |
| **Default in a custom VPC** | Denies all inbound, allows all outbound | Allows all inbound and outbound |

Use a security group as the primary, per-resource firewall — scope inbound rules to the
specific port and source (another security group or a narrow CIDR, never `0.0.0.0/0` unless
the resource is deliberately public per item 8). Reach for a NACL only when a rule needs to
apply at the subnet level regardless of which resource lives there, or when an explicit deny
is needed (a security group can't deny — it can only omit an allow).

## Private connectivity between VPCs or accounts

When two resources need to talk without crossing the public internet:

- **VPC Peering** — a direct, non-transitive network connection between two VPCs (same or
  different accounts). Simple for a small number of VPCs; doesn't scale cleanly past a
  handful of peered pairs (no transitive routing — every pair needs its own peering).
- **AWS PrivateLink** — exposes a specific service (yours or a vendor's) as an interface
  endpoint inside the consumer's VPC, without peering the whole network. Prefer this when
  only one specific service needs to be reached, not general network connectivity — it's a
  narrower, more auditable exposure than peering.
- **Transit Gateway** — a hub that many VPCs and on-premises networks attach to, giving
  transitive routing between all of them through one place. Reach for this once peering's
  pairwise connections become unmanageable (roughly double-digit VPC counts), not before —
  it's a bigger piece of shared infrastructure to own.

## The public-exposure decision tree

Answer in this order; stop at the first "no":

1. **Does this resource need to accept inbound requests directly from the public internet**
   (a browser, a third-party webhook, a mobile app hitting it directly — not through a
   gateway/load balancer that could sit in front of it)? If yes → public subnet, IGW route,
   a security group scoped to the specific port and, where possible, a narrower source than
   `0.0.0.0/0` (a CDN's or load balancer's IP range, if one fronts it). Pair with
   `resilience-strategy` for edge protection (WAF, Shield, rate limiting) — this skill places
   the resource, that skill defends it once placed.
2. **Does it only need outbound internet access** (calling a third-party API, pulling a
   package, sending an email) but never receives unsolicited inbound traffic from the
   internet? → private subnet, NAT Gateway route for outbound only. This is the common case
   for application servers, workers, and most Lambdas-in-a-VPC.
3. **Does it only need to reach other resources inside the VPC or account** (a database, an
   internal service, another AWS service reachable via a VPC endpoint)? → private subnet, no
   NAT, no IGW. This is the most isolated option and should be the default whenever items 1
   and 2 are both "no" — there is no reason to pay for or expose a NAT path a resource never
   uses.
4. **Does it need to reach one specific AWS service (S3, DynamoDB, Secrets Manager, etc.)
   without traversing the public internet at all, even via NAT?** → a VPC Gateway or
   Interface Endpoint for that service, instead of routing through a NAT Gateway. Cheaper and
   narrower than NAT egress when the only outbound need is to AWS's own services.

"Public because it's simpler to set up" fails at step 1 — the honest answer to step 1 is
almost always "no," and the resource belongs at step 2 or 3. The setup cost difference
between a private subnet with a NAT route and a public one is a few extra minutes of
Terraform; the cost difference in exposure is the entire point of gate item 8.
