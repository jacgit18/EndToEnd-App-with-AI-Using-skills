# Design Scoping — example invocations

Read to calibrate the response to a specific kind of opening message.

## Example invocations

> "Design a link-shortening service for us."

Gate not satisfied — items 2–6 absent. Response: this needs scoping before a design, and
the scoping is the work. Ask for: who it's for and roughly how many (internal tool? public
service? marketing team?); the functional list (shorten, redirect, custom aliases,
analytics?) and what's explicitly out (user accounts? link expiry? bulk API?); the numbers
(redirects/sec at peak, acceptable redirect latency, uptime target, monthly cost ceiling);
the constraints (team size, deadline, existing stack, any compliance); and — using the
significance filter — which one or two decisions (the key-generation scheme? the
read-path/storage design? custom-domain support?) are worth designing deeply now. Don't
propose a schema or a technology.

> "We're building an internal analytics dashboard. Purpose: let the ops team see order
> volumes and error rates without asking engineering. ~20 users, all internal, web only,
> US. In scope: 6 predefined dashboards, CSV export, a date-range picker. Explicitly out:
> custom query builder, alerting, mobile, external sharing. Targets: it can be slow (5s
> page load fine), 20 concurrent users max, 99% uptime is plenty, no hard cost cap but
> keep it under ~$200/mo. Team: 2 engineers, 6 weeks, we're a Python/Postgres shop on AWS,
> no compliance beyond SOC 2. Deep-dive: the query/aggregation approach over the orders
> data, since that decides whether we hit Postgres directly or need a rollup layer."

Escape hatch — fully scoped. Assemble the scope statement, note that the one deep-dive
(direct-query vs rollup layer) is a whole-data-model blast-radius call and routes to
`database-architecture` / `data-tier-operations`, and that with 20 users and a 5s budget
the sequence is short: skip `capacity-estimation` (numbers are trivially small), skip
`microservices-decision` (one small app), go straight to the data decision, then a light
`failure-mode-analysis` pass before ship.

> "Can you help me with my system? It's kind of a mess."

Not this skill yet. "Help" and "a mess" don't establish a design task — is this a
refactor, a debugging session, a redesign, a documentation pass? → `ambiguity-gate` to
resolve what's being asked. If it resolves to "redesign it", this skill picks up.

> "Is this ticket worth pulling into the sprint? [pastes a defined ticket]"

Not this skill. A specified unit of work being judged → `ticket-evaluation`.
