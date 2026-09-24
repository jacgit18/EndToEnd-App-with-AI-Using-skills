# Mesh, discovery, and the smallest tool that fits

Reference for the process step in `SKILL.md`. Two related decisions: whether to adopt a mesh at all, and how services find each other regardless of that answer.

## Service discovery mechanisms

Every system with more than one service instance calling another needs some answer to "what's the current network location of the service I need to call." Three shapes:

| Mechanism | How it works | Fits when |
|---|---|---|
| **Self-registration to a registry** (Eureka, Consul) | Each instance registers itself on startup and sends heartbeats; callers query the registry for a live instance list | The platform has no native discovery (bare VMs, older orchestration) and the team is willing to run and operate the registry itself |
| **Third-party / orchestrator-managed registration** | A platform component (Kubernetes, an orchestrator) registers instances on services' behalf as they're scheduled | Already running a container orchestrator — this is usually the cheapest option since the orchestrator is doing it anyway (Kubernetes `Service` objects + cluster DNS) |
| **DNS-based, platform-native** | Callers resolve a stable DNS name; the platform keeps the DNS answer current as instances come and go | Kubernetes, ECS Service Discovery (Cloud Map), or any platform with built-in DNS-based discovery — usually the default once the orchestrator choice is made, no separate tool needed |
| **Mesh-integrated (sidecar)** | The sidecar proxy handles discovery transparently; services call a logical name and the sidecar resolves and routes it | Already adopting a mesh for other reasons (below) — discovery comes bundled, not a separate cost |

Don't add a standalone registry (Eureka/Consul) on top of a platform that already gives DNS-based discovery for free (Kubernetes, ECS) — that's the third-party-registration or DNS-native row solving the same problem the orchestrator already solves, at the cost of running one more component.

## No mesh vs lightweight mesh vs full mesh

| | No mesh | Lightweight / partial mesh (e.g. Linkerd, mTLS-focused) | Full-featured mesh (e.g. Istio) |
|---|---|---|---|
| **Encryption in transit (mTLS)** | Per-service, hand-configured (app-level TLS + a private CA), or accepted risk within a trusted network | Automatic, uniform, low operational overhead | Automatic, uniform, plus fine-grained policy over it |
| **Traffic control** (canary/weighted routing by version) | Only via the deploy pipeline or a gateway in front | Basic | Fine-grained: header-based routing, weighted splits, fault injection |
| **Uniform retries / circuit-breaking without app changes** | No — each service implements its own (or shares a library) | Yes, basic | Yes, with more configuration surface |
| **Observability (RED metrics, tracing) without instrumenting each service** | No — each service instruments itself | Yes, basic | Yes, comprehensive |
| **Per-hop latency tax** | None | Small | Small to moderate (more proxy logic in the data path) |
| **Operational burden** | None beyond what's already run | A control plane, but a simpler one | A control plane with real configuration surface and a learning curve |
| **Resource overhead** | None | One sidecar per pod, lighter footprint | One sidecar per pod, more capable and heavier |

The point of naming the specific capability (`SKILL.md` gate item 3) before picking a row: a team that needs mTLS and nothing else is paying for Istio's full policy and traffic-management surface without using most of it, when a lighter tool or even hand-configured app-level TLS might close the actual gap. Pick the smallest tool that satisfies the named capability, the same principle `access-control-modeling` applies to picking the smallest authorization model that fits the stated granularity.

## The sidecar pattern, mechanically

A mesh works by deploying a proxy (commonly Envoy) alongside every service instance — one sidecar container per pod in Kubernetes. All inbound and outbound traffic for that service instance is transparently routed through its sidecar. This is what makes the mesh's behavior (mTLS, retries, traffic splitting, telemetry) uniform across every service without touching application code — but it's also the whole cost: one more container per instance, one more hop in every call's path, and one more thing that can misbehave (a sidecar misconfiguration produces failures that look like they're coming from the service itself, and debugging that distinction is a real skill the operating team needs to build).

Sidecar injection is a solved, low-friction pattern on Kubernetes (a namespace label or an admission webhook adds the sidecar automatically at pod creation). On VMs or a non-Kubernetes container platform (bare ECS, for instance), there's no equivalent automatic injection — sidecars have to be wired into deployment scripts, service definitions, and health checks by hand, which is a materially bigger and more fragile lift. This is why `SKILL.md`'s gate treats platform (item 4) as a first-order fact, not a footnote.

## Service mesh vs load balancer — complementary, not competing

A load balancer distributes traffic across replicas of the *same* service — simple, cheap, well-understood, and usually necessary regardless of whether a mesh exists. A service mesh governs traffic *between different* services, uniformly, with encryption, fine-grained routing, and telemetry as part of the package. Most real systems that adopt a mesh still have load balancers in front of public-facing entry points — the mesh handles the east-west (service-to-service) traffic a load balancer was never designed to see into. Treating mesh adoption as "replacing" the load balancer is a category error; check what specific load-balancing responsibility, if any, is actually being absorbed before framing it that way.
