# Mechanisms and their failure modes

Reference for the process step in `SKILL.md`. Pick per-value, not once for the whole system — a feature toggle and a database password rarely want the same mechanism.

## Plain environment variables

Injected by the platform (a `.env` file loaded in development, a Docker `--env-file`, an orchestrator's env-var injection) and read by the process at startup.

**Fits:** non-sensitive config with a low blast radius if exposed — a hostname, a timeout, a log level, a feature toggle that only needs to change between deploys.

**Cost:** no rotation without a process restart; visible in `/proc/<pid>/environ` and process listings on the host; commonly captured whole in crash dumps, error-tracking tool snapshots (Sentry, Rollbar), and CI job logs when a script echoes the environment for debugging; easy to accidentally commit via a `.env` file that isn't actually gitignored, or a leaked CI log.

**Failure mode:** a genuine credential shipped as a bare env var "because that's how we do config here," with no rotation path and no audit trail — exactly the shape of the PCI/SOC2 finding that triggers a scramble later.

## Orchestrator-native secrets

Kubernetes `Secret` objects (base64-encoded, not encrypted by default unless encryption-at-rest is configured on etcd), ECS task-definition secrets (which can pull from Parameter Store or Secrets Manager at task launch), or the equivalent on another platform.

**Fits:** a step up from plain env vars with no new infrastructure to run — integrates with the platform's own RBAC (who can `kubectl get secret`, which IAM role can read a given ECS secret reference) and, for ECS specifically, can proxy to a real secrets manager without app code changes.

**Cost:** Kubernetes `Secret`s are not encrypted at rest by default (a common misconception) — that needs to be configured separately (etcd encryption, or a KMS-backed provider) or paired with an external-secrets operator syncing from a real secrets manager. Rotation still generally requires a pod restart to pick up a changed `Secret` unless a sidecar or the app itself watches for changes.

## Dedicated secrets manager

Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault — a service purpose-built for storing sensitive values, with access policies, automatic rotation for supported credential types (e.g., AWS Secrets Manager's native RDS rotation), and an audit trail of every read and write.

**Fits:** anything with a real rotation requirement, a real audit requirement, or a high blast radius if leaked (item 6 in `SKILL.md`'s gate) — a production database password, a payment-processor API key, a signing key.

**Cost:** one more service to operate (self-hosted Vault) or pay for (managed offerings); every consumer needs a client integration (an SDK call, a sidecar, or an operator syncing values into the platform's native secret store) rather than just reading an env var; a fetch-at-startup pattern means the secrets manager being briefly unavailable can block a deploy or a pod from starting, so a caching/retry story matters.

**Rotation, done right:** the goal is a rotated secret reaching every consumer without a coordinated, all-at-once redeploy. Two shapes: (1) the app polls or is pushed a refreshed value and swaps it in without restarting (works well for things like short-lived database connections that can be re-established), or (2) the platform re-injects the current value on the next natural restart/rolling-update cycle, and rotation is scheduled to tolerate a brief overlap window where both old and new values are valid (common for API keys with a provider-side grace period, like Stripe). The anti-pattern is treating rotation as "redeploy every consumer simultaneously" — that's fragile by construction and is usually what makes teams avoid rotating at all.

## Dynamic config / feature-flag service

LaunchDarkly, Consul KV, etcd, a homegrown config API — a service the app queries (or subscribes to) for values that can change without a deploy or a restart.

**Fits:** the specific case plain env vars structurally can't serve — a value that must change **without restarting the process** (a feature flag flipped mid-incident, a rate limit tightened live, a kill switch).

**Cost:** the service itself becomes a new dependency on the request path (if queried synchronously) or a new source of staleness (if cached/polled) — either way, it needs a **safe local default** the app falls back to if the service is unreachable, or the flag service has just become a single point of failure for a value that used to simply work. This is the single most common mistake with this mechanism: shipping it without a fallback and discovering the gap during the flag service's first outage.

## Choosing by value, not by system

A real system typically ends up with all four mechanisms in play at once for different values — plain env vars for the database hostname, a secrets manager for the database password, orchestrator-native secrets syncing from that same secrets manager so app code doesn't need a custom SDK call, and a feature-flag service for the handful of values that genuinely need runtime toggling. Treating this as one system-wide decision ("we use Vault" / "we use env vars") skips the one question that actually matters per value: does *this* value need rotation, runtime changeability, or an audit trail — or is it just a hostname.
