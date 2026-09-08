# service-mesh-adoption skill

A gated decision for **whether to adopt a service mesh** (Istio, Linkerd, Consul Connect —
sidecar-proxy infrastructure for service-to-service traffic) versus a lighter-weight
alternative, and — if adopting one — which specific capability is actually being bought:
mTLS, fine-grained traffic control, uniform resilience without app changes, or free
observability. Also covers the service-discovery mechanism itself, since it's resolved by
the same decision. Given a system with more than one service calling more than one other
service, the skill makes the user name the specific capability driving the ask, the
platform, and who would own the added control plane before any tool is recommended, then
writes an ADR.

Built from an audit of `Architecture/Networking/` that found every existing mention of
"service mesh" across this catalog (`resilience-strategy`'s placement table,
`deployment-strategy`'s rollout tooling, `observability-strategy`'s collector topology)
treats a mesh as infrastructure that **already exists** — a place a control can live, never
something anyone decides whether to adopt. `cloud-iam-boundary` even names mTLS/encryption
in transit as an explicitly unowned gap. This skill closes that gap.

## Where it sits

```
microservices-decision     →  how many services exist, and their boundaries (given, input)
service-mesh-adoption       →  whether a mesh exists for service-to-service traffic, and
                               the discovery mechanism regardless                (this skill) → ADR
resilience-strategy         →  exactly which controls run and where, once this skill's
                               mesh-or-not answer narrows the placement options
cloud-iam-boundary          →  who's authorized to call whom, once a transport/identity
                               (mTLS or not) exists
deployment-strategy         →  canary/blue-green mechanics for one deployable, using the
                               mesh's traffic-splitting as a mechanism if one exists
bff-gateway-placement        →  the client-to-service (north-south) counterpart; this skill
                               is service-to-service (east-west) only
observability-strategy      →  the instrumentation strategy; a mesh can supply free RED
                               metrics/tracing as a side effect this skill names
serverless-execution-model  →  compute primitive for one unit of work; a sidecar mesh
                               generally doesn't fit a FaaS workload
```

## The shape

A gate skill, same family as `microservices-decision` and `bff-gateway-placement`. It
refuses to recommend a mesh, a lighter tool, or "none" until the user supplies:

- **service count and call topology** — not just "we have microservices," but how many and
  how they call each other
- **the specific capability driving the ask** — mTLS, traffic control, uniform resilience,
  or observability, named explicitly, not "it's standard practice"
- **platform fit** — Kubernetes (low-lift) vs VMs/ECS (high-lift) vs serverless (poor fit)
- **what's already achievable without a mesh** — the platform's native discovery, existing
  resilience libraries, or a narrower TLS approach
- **ownership** for the added control plane — an unowned mesh is the same failure mode
  `microservices-decision` gates on for an unowned service

Then it recommends one of three shapes (no mesh / lightweight mesh / full mesh), names the
discovery mechanism regardless, and writes an ADR.

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/`.

```
cp -r .claude/skills/Architecture/service-mesh-adoption /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `resilience-strategy`** — that skill already lists "service mesh" as one of four
  control-placement homes, assuming one may or may not exist. This skill decides whether it
  exists; that skill decides what runs where once it does (or doesn't).
- **vs `bff-gateway-placement`** — north-south (client-to-service) vs east-west
  (service-to-service). A system can have both a gateway and a mesh, solving different
  halves of the traffic picture; neither replaces the other.
- **vs `cloud-iam-boundary`** — this skill decides whether an encrypted, identity-bearing
  transport exists between services (mTLS or not); that skill decides who's authorized to
  use it. They compose: a mesh's automatic mTLS gives every service an identity that
  `cloud-iam-boundary`'s policy can reference.
- **vs `microservices-decision`** — that skill decides service boundaries and count; this
  skill takes that as a given input and never re-litigates whether the split is right.
