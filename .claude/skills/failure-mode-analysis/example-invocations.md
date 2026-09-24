# Example invocations (failure-mode-analysis)

Contents: checkout pre-mortem (RPN) · Redis cache addition (small altitude) · live 502 (not this skill)

> "Do a pre-mortem on this: a checkout service that calls a pricing service (gRPC, sync), a
> payment gateway (HTTPS, sync), writes orders to Postgres, and emits an `order.placed`
> event to Kafka that a fulfilment consumer reads. Two engineers own it, basic
> CloudWatch alarms on 5xx rate only."

Frame: 5 components (checkout, pricing, payment gateway, Postgres, Kafka + fulfilment
consumer), 4 interactions. Severity 10 = a customer charged with no order recorded, or an
order shipped that wasn't paid. Scheme: RPN (load-bearing, money). Walk each component ×9
and each interaction. Sample rows: *payment gateway call succeeds, Postgres write then
fails* → double-charge risk / customer charged, no order → S10 O4 D7 (only 5xx alarms, this
path returns 200) RPN 280 → watchlist + resilience-strategy (outbox/idempotency) +
observability-strategy (reconcile alarm). *`order.placed` published, consumer down* →
fulfilment silently lags → S7 O5 D8 RPN 280 → observability (consumer-lag alert) +
test-strategy (inject consumer outage). *pricing service returns stale price on cache
fallback* → wrong amount charged → S8 O3 D9 RPN 216. Detection gaps: 4 rows where the only
signal is a customer complaint. Recommend block sign-off — two watchlist rows.

> "What could go wrong with adding a Redis cache in front of our user-profile reads?"

Narrower altitude — one interaction added. Walk the new component (Redis) and the new
interaction (app → Redis, with DB fallback) ×9. Modes: cache down → fallback storm on the
DB (dependency/performance); stale profile after an update (consistency); key stampede on a
hot miss (performance); Redis eviction under memory pressure drops the working set
(operational); a serialization-format change makes old cached entries poison
(integration/operational). Register + hand the stampede and cache-down rows to
`resilience-strategy` and `caching-strategy`. Small enough that "register only" is the
right default.

> "The API is throwing 502s right now and I think it's the connection pool — help me debug."

Not this skill. One failure, happening now, with a hypothesis → `problem-solving-gates`
(Rubber Duck). Say so and route.
