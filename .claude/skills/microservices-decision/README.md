# microservices-decision skill

A gated decision for **how many services a team should run and where the boundaries go** —
monolith, modular monolith, or microservices — plus the follow-on repo layout (one repo,
repo-per-service, hybrid) and frontend decomposition (micro-frontends). The gate is
headcount and ownership: it refuses a service list until the user states engineers, owner per
service, and the problem being solved, including when the decision is "already made".

## Where it sits

```
design-scoping             →  scopes a greenfield system, then sequences here
microservices-decision      →  service count, boundaries, repo layout, micro-frontends   (this skill) → ADR
bff-gateway-placement       →  what layer sits between clients and these services (takes boundaries as input)
api-interface-style         →  the wire protocol per boundary
service-mesh-adoption       →  whether service-to-service transport needs a mesh (takes the split as given)
serverless-execution-model  →  what compute primitive runs one already-scoped service
migration-cutover           →  executes an agreed extraction / repo split
deployment-strategy         →  rollout of one deployable unit
data-tier-operations        →  sharding / replication (not a service split)
technical-cost-decision     →  CI and platform dollar cost
```

## The shape

A gate skill. Output order is fixed: Readiness Block first, unanswered gate questions
(then stop), recommendation only once the block is filled. Companions: `repo-layout.md`
(monorepo tooling, CODEOWNERS, affected-graph CI) and `frontend-layout.md` (integration
techniques).

## Using it in another repo

Repo-agnostic. Writes ADRs to `docs/architecture/decisions/`. Copy the directory to
`.claude/skills/microservices-decision/`.
