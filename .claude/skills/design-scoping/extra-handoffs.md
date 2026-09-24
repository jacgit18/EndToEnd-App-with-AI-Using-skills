# Design Scoping — additional hand-off skills

Read when the deep-dive picks imply a skill beyond the seven-step typical order in `SKILL.md`.

Not every design needs all seven, and the sequence is not a closed list — a scope statement
may also pull in `data-tier-operations` (scaling an existing store), `technical-cost-decision`
(when the cost cap is tight), `caching-strategy`, `access-control-modeling` (when one of the
deep-dive picks is the permission/authorization model — who may do what to which resource), or
`bff-gateway-placement` (when the audience names more than one client type — web, mobile,
partners — and what sits between them and the services from step 2 is itself a deep-dive pick),
`service-mesh-adoption` (when the service split from step 2 produces enough services calling
each other that encryption, discovery, or uniform resilience between them is itself a deep-dive
pick), or `config-and-secrets-management` (when a named credential or config value's storage
and rotation is itself a deep-dive pick) where the deep-dive decisions imply them. Name the
skills this scope actually needs, in dependency order.
