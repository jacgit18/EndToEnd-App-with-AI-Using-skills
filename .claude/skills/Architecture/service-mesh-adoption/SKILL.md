---
name: service-mesh-adoption
description: A gated decision for whether to adopt a service mesh (Istio, Linkerd, Consul Connect — sidecar-proxy infrastructure for service-to-service traffic) versus a lighter-weight alternative (orchestrator-native DNS discovery, in-process resilience libraries, TLS terminated at fewer boundary points), and — if adopting one — which specific capability is actually being bought: mutual TLS/encryption in transit between services, fine-grained traffic control (canary/weighted routing by header or version), uniform retries and circuit-breaking without touching application code, or free per-service observability (RED metrics, distributed tracing). Also covers the service-discovery mechanism itself — self-registration to a registry (Eureka, Consul), third-party/orchestrator-managed registration, DNS-based discovery native to the platform, or mesh-integrated sidecar discovery — since it's resolved by the same decision. Use when someone says "should we adopt a service mesh", "do we need Istio or Linkerd", "how do our services find each other", "should we use Eureka/Consul for service discovery", "do we need mTLS between services", "our services call each other by hardcoded hostnames", "should this be a sidecar or a library", "service mesh vs load balancer", or proposes adopting a mesh and wants it checked. It forces the user to name the specific capability driving the ask (not "it's standard" or "every serious shop has one"), the service count and call topology, the platform (Kubernetes-native sidecar injection is a solved, well-supported pattern; bolting a mesh onto VMs/ECS is a materially bigger lift; serverless functions generally don't fit a sidecar model at all), and who would operate the added control plane, before any recommendation, then records the outcome as an ADR. Not for whether to split into services at all — that is `microservices-decision`, which this skill assumes as already decided; it takes the service count and call graph as input, not an output. Not for exactly which resilience mechanisms run and where once the mesh-or-not decision is made (rate limits, circuit breakers, retries, bulkheads) — that is `resilience-strategy`, which already treats a service mesh as one of four control-placement options and consumes this skill's yes/no as a given fact. Not for the IAM/permission grant authorizing one service to call another — that is `cloud-iam-boundary`; this skill decides whether an encrypted, discoverable transport exists between services at all (does mTLS exist), not who is authorized once that pipe exists — the two compose. Not for canary/blue-green rollout mechanics for a single deployable's release — that is `deployment-strategy`, which this skill's mesh-or-not decision determines whether native traffic-splitting tooling is even available for. Not for what layer sits between external clients and backend services (a gateway or BFF) — that is `bff-gateway-placement`, a client-to-service (north-south) decision; this skill is about service-to-service (east-west) traffic exclusively. Not for an unscoped, not-yet-designed system — that is `design-scoping` first, which sequences a system with a named service topology back here. A bare conceptual question with no named system ("what is a service mesh", "service mesh vs load balancer, what's the difference") is answered directly, no gate — the gate exists for a pending adoption decision on a named service topology, not for explaining the vocabulary.
---

# Service Mesh Adoption

Take a system with more than one service calling more than one other service, and decide whether to introduce a service mesh — sidecar proxies deployed alongside every service, handling discovery, encryption, traffic routing, and telemetry uniformly — or to solve the same problems more cheaply with what the platform and a few libraries already provide. The skill makes the user name the actual capability driving the request before any tool is on the table, because "every serious microservices shop runs a mesh" is an observation about other organizations, not evidence that this system's service count, platform, and team justify the sidecar tax — a per-hop latency cost, a control plane someone has to run, and a debugging surface that didn't exist before.

## When to use

- Someone is **proposing mesh adoption** — "should we add Istio", "do we need a service mesh", "let's put Linkerd in front of our services".
- Someone is **solving a problem a mesh happens to solve**, without naming the mesh — "our services call each other over plain HTTP with no encryption", "we hardcode IPs/hostnames between services and it breaks on every redeploy", "we want canary releases at the service level, not just at the load balancer", "every service reimplements its own retry logic."
- Someone asks about **service discovery** directly — "how should services find each other", "should we use Eureka/Consul", "DNS-based discovery vs a registry."
- Someone is **deciding whether to introduce a mesh alongside an existing load balancer or API gateway on a named system** — "do we need both a mesh and a gateway for our setup." (A bare "what's the difference between a service mesh and a load balancer" with no named system is the no-gate conceptual case below, not this.)
- Someone proposes an already-decided mesh adoption and wants it checked — "we're rolling out Istio next quarter", "let's mesh everything, it's the modern way."

## Out of scope — hand these off

- **Whether to split into services at all, and where the boundaries go** — `microservices-decision`. This skill takes the service count and call graph as given; it does not decide whether that count is right.
- **Exactly which resilience mechanisms run and where** — rate limiting, circuit breakers, retries with backoff, bulkheads, load shedding → `resilience-strategy`, once this skill's mesh-or-not answer is settled. That skill's placement table already lists "service mesh" as one of four homes for a control; this skill decides whether that home exists.
- **The IAM/permission grant for one service calling another** — which principal may call which resource → `cloud-iam-boundary`. This skill decides whether an encrypted, discoverable transport exists between services (mTLS or not); that skill decides who's authorized to use it. The two compose — a mesh's automatic mTLS gives every service an identity, which `cloud-iam-boundary`'s policy can then reference.
- **Canary/blue-green rollout mechanics for one deployable unit** — `deployment-strategy`. A mesh can be the traffic-splitting mechanism that skill's canary pattern uses, but this skill decides whether that mechanism exists, not how a specific release rolls out.
- **What sits between external clients and backend services** — a shared gateway, a BFF, direct-to-service (north-south, client-to-service traffic) → `bff-gateway-placement`. This skill is exclusively about east-west, service-to-service traffic. A system can have both a gateway and a mesh, solving different halves of the traffic picture.
- **The compute primitive for one unit of work** — Lambda vs container vs long-running service → `serverless-execution-model`. A sidecar-based mesh generally doesn't fit a FaaS invocation model at all; if the workload in question is serverless, that's the first sign this skill doesn't apply to it.
- **Observability instrumentation itself** — what SLIs, sampling, and alerting a system needs → `observability-strategy`. A mesh can supply free RED metrics and tracing as a side effect; this skill names that as a possible capability being bought, but the instrumentation strategy itself belongs to that skill.
- **Implementation** — the actual Istio/Linkerd/Consul installation, sidecar injection config, `VirtualService`/`DestinationRule` manifests. This skill stops at a recommendation and an ADR.
- **An unscoped, not-yet-designed system** — "what should our service communication layer look like" with no named services or call pattern yet → `design-scoping` first.
- **A bare conceptual question with no named system** — "what is a service mesh", "what's the difference between a service mesh and a load balancer" — is answered directly, no gate. The gate exists for a pending adoption decision on a named service topology, not for explaining the vocabulary.

---

## The gate

Before recommending a mesh, a lighter alternative, or a discovery mechanism, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **What already exists** — an existing mesh, service registry, or discovery mechanism (Kubernetes Services, Eureka, Consul, hardcoded config) already in place; the platform already in use (Kubernetes, ECS, VMs, a mix).

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

2. **Service count and call topology** — how many services exist (from `microservices-decision`'s output if it ran), and how many other services does a typical service call synchronously? A handful of services with a shallow, stable call graph is a different problem than a dense many-to-many mesh of calls across dozens of services.
3. **The specific capability driving the ask** — name exactly one or more of: encryption in transit between services (mTLS), fine-grained traffic control (canary/weighted routing by version or header, without relying on the deploy pipeline), uniform retries/timeouts/circuit-breaking applied without touching every service's code, or free per-service observability (RED metrics, distributed tracing) without instrumenting each service by hand. "It's standard" or "every serious shop has one" is not a capability — ask what specifically is missing today.
4. **Platform** — Kubernetes (sidecar injection is a solved, well-documented pattern via `istio-injection` labels or a Linkerd `linkerd inject`), VMs/bare ECS/other (a mesh is a substantially bigger and less-supported lift — sidecars have to be wired into deployment scripts by hand), or a serverless/FaaS mix (a mesh generally doesn't apply to those workloads — see `serverless-execution-model`).
5. **What's already achievable without a mesh** — does the platform already provide DNS-based service discovery (Kubernetes Services do this natively)? Could the retry/circuit-breaking behavior be satisfied by a shared library or `resilience-strategy`'s in-process controls instead of infrastructure-wide sidecars? Would a private network plus TLS terminated at fewer boundary points (the gateway, a handful of trust zones) satisfy the actual threat model, short of full pairwise mTLS everywhere?
6. **Operational ownership** — who operates the mesh's control plane, debugs a sidecar-related latency spike or a mysterious 503 that turns out to be a proxy misconfiguration, and keeps sidecar versions current across every service? A mesh with no named owner is the same failure mode `microservices-decision` gates on for an unowned service.
7. **Latency and resource budget** — sidecars add a per-hop latency tax (commonly single-digit milliseconds, but real) and CPU/memory overhead per pod. Is that budget available on the system's hottest call path, and has anyone measured rather than assumed it's negligible?
8. **Team size relative to service count** — a mesh's operational cost pays for itself once manually threading TLS, discovery, and retries into every service by hand is the bigger cost. For a small number of services and a small team, that crossover often hasn't been reached yet.

"We should add a service mesh" or "let's use Istio" with items 2–5 unanswered is not valid input — naming a specific missing capability (item 3) is usually one sentence and is the single fact the rest of the recommendation depends on.

**Pressure does not open the gate.** "Every serious microservices architecture has a mesh, let's just add Istio" is authority-without-evidence about this system — record it as a stated preference in the gate, not a technical conclusion. Naming items 2–5 takes one paragraph and is the fastest way to find out whether a full mesh, a lighter tool, or nothing at all actually fits.

---

## Challenge a proposed approach

If the user opens with the tool already chosen, put their reasoning under the gate, then test the specific claim against `mesh-and-discovery-tradeoffs.md`:

- **"every serious microservices shop runs a service mesh"** — that's a fact about other organizations, not evidence about this system's service count, platform, or team capacity (items 2, 4, 8). Name the specific capability (item 3) actually missing today.
- **"we need mTLS, let's adopt Istio"** — is full Istio's traffic-management and policy surface needed, or would a lighter mTLS-focused tool (Linkerd), or even application-level TLS with certificates from a private CA, satisfy the actual need without paying for capability that goes unused?
- **"we're on ECS/VMs, let's still run a mesh"** — sidecar injection on Kubernetes is a solved, well-supported pattern; the same pattern on ECS or bare VMs means hand-wiring sidecars into every deployment script and load-balancer target group (item 4). Is that lift, on this platform, actually worth the capability gained?
- **"let's mesh our Lambda functions too"** — a sidecar-based mesh assumes a long-running process to attach a sidecar to. Serverless functions don't fit that model; route this to `serverless-execution-model` instead of forcing a mesh onto a workload it wasn't built for.
- **"we'll figure out who owns the mesh later"** — an unowned control plane is exactly the failure mode `microservices-decision` and `bff-gateway-placement` both gate on for unowned services and layers (item 6). Name an owner before adopting, not after the first sidecar-related incident.
- **"a mesh replaces our load balancer"** — a mesh and a load balancer solve different problems (fine-grained east-west traffic control and uniform per-pair resilience vs simple traffic distribution across replicas) and commonly coexist; see `mesh-and-discovery-tradeoffs.md`'s comparison. Don't frame this as a replacement unless the specific load-balancing need is actually being absorbed.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `mesh-and-discovery-tradeoffs.md` once the gate is satisfied. In short: name the service count and call topology (item 2) → name the specific capability driving the ask (item 3) → check it against the platform's fit for sidecar injection (item 4) → check whether a lighter alternative already satisfies it (item 5) → name an owner (item 6) → weigh the latency/resource budget (item 7) against the team-size crossover (item 8) → recommend one of: no mesh (platform-native discovery + resilience-strategy's in-process controls + TLS at fewer boundaries), a lightweight/partial mesh (mTLS and basic retries only, lower overhead), or a full-featured mesh (comprehensive traffic management, policy, and observability) → name the service-discovery mechanism regardless of the mesh decision → record.

Reference file:

- `mesh-and-discovery-tradeoffs.md` — the three service-discovery mechanisms (self-registration, third-party/orchestrator-managed, DNS-native) and their tradeoffs; a no-mesh vs lightweight-mesh vs full-mesh comparison; the sidecar pattern's mechanics and cost; the specific-capability breakdown so the smallest tool that satisfies the actual need can be chosen instead of defaulting to the most feature-complete option; service mesh vs load balancer as complementary, not competing, tools.

---

## Output

**1. In chat, a recommendation block:**

```
Service count / topology:  <how many services, and the shape of the call graph>
Capability driving the ask: <mTLS | traffic control | uniform resilience | observability | more than one — named specifically>
Platform fit:               <Kubernetes (low lift) | VMs/ECS (high lift) | serverless mix (poor fit, see serverless-execution-model)>
Achievable without a mesh:  <what the platform/libraries already provide, and what gap remains>
Recommendation:              <no mesh | lightweight/partial mesh (name the tool) | full-featured mesh (name the tool)>
Discovery mechanism:         <self-registration to a registry | third-party/orchestrator-managed | DNS-native | mesh-integrated>
Owner:                       <named team, or UNASSIGNED>
Tradeoffs accepted:          <2-4 concrete costs: per-hop latency, control-plane operational burden, sidecar resource overhead, or — if no mesh — manual per-service TLS/retry maintenance>
Not chosen because:          <one line per rejected option>
Follow-ups:                  <resilience-strategy for exact mechanism placement; cloud-iam-boundary for the authorization policy once identity exists; observability-strategy for the instrumentation strategy; technical-cost-decision for control-plane infra cost>
```

Any field you cannot fill from the user's own words is `UNANSWERED`. A block with `UNANSWERED` fields on items 2–5 ends the response.

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering). Fill "Revisit when" with a concrete trigger — "service count crosses the point where manual per-service TLS/discovery maintenance becomes the bigger cost", "a second capability (beyond the one driving this decision) is needed and a lighter tool no longer covers it", "the sidecar latency tax is measured against a tightened p99 budget and no longer fits."

Then stop. Implementation — the actual mesh installation, sidecar injection, traffic policies — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked the decision — the capability named, the platform fit checked, ownership accounted for — and wants a review or a tie-break rather than a Socratic pass, they can say so and get a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "We have 14 services on Kubernetes, all calling each other over plain HTTP. Two things are driving this: we got flagged in a security review for unencrypted service-to-service traffic, and we want to do canary releases at the service level instead of the current all-or-nothing deploys. We're a platform team of 4 that would own this. Nobody's measured the latency impact yet."

Gate satisfied. Service count/topology: 14 services, Kubernetes (item 4: low-lift platform for sidecar injection). Capability: encryption in transit (mTLS) + fine-grained traffic control for canary (item 3, two capabilities named specifically, not "it's standard"). Achievable without a mesh: Kubernetes gives DNS-based discovery already; mTLS could be done with cert-manager + app-level TLS config per service, but that's per-service maintenance across 14 services and growing; canary-by-service isn't available without either a mesh or per-service application logic. Given both named capabilities are real and the platform fit is good: recommend a **full-featured mesh (Istio)** — mTLS and traffic-splitting are both first-class, and 14 services is past the point where per-service TLS configuration is cheaper than one control plane. Owner: the 4-person platform team (item 6, named). Gap: latency budget unmeasured (item 7) — flag as a pre-adoption task: benchmark the sidecar tax on the hottest path before full rollout, not after. Discovery: mesh-integrated (comes with Istio). Tradeoffs: control-plane operational burden lands on a 4-person team already stretched; sidecar resource overhead across 14 services' worth of pods. Not chosen: no mesh (doesn't solve canary-by-service); lightweight mesh alone (Linkerd solves mTLS but its traffic-splitting is less mature than Istio's, and canary is one of the two named drivers). Follow-ups: cloud-iam-boundary once service identities exist via mTLS; observability-strategy to decide what to do with the free RED metrics Istio provides. ADR; revisit when the unmeasured latency budget comes back over-tolerance, or team size doesn't keep pace with service count.

> "Should we use a service mesh?"

Gate not satisfied — item 2 (how many services, what's the call pattern), item 3 (what specific capability is missing today — mTLS, traffic control, resilience, or observability), item 4 (what platform). Response: ask what's actually driving the question — a named problem, or "it's the modern pattern" — before naming a tool. Do not recommend Istio, Linkerd, or "no mesh" yet.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Vocabulary (mesh, sidecar, mTLS) is provider-neutral; platform-specific mechanics (Kubernetes sidecar injection vs a VM-based install) are named in the gate rather than assumed. Copy the `service-mesh-adoption/` directory into another repo's `.claude/skills/` to use it there.
