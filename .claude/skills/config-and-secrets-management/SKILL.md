---
name: config-and-secrets-management
description: Gated decision for where app config and secrets live and reach a running process: env vars, orchestrator secrets, a secrets manager, or a feature-flag service, plus rotation and leak blast radius. Triggers: "where should we store our API keys/secrets", "we committed a secret to git", "how do we rotate our database password without downtime", "should we use LaunchDarkly". Not for who may read a secret — `cloud-iam-boundary`. Not for app permissions — `access-control-modeling`. Not for an unscoped system — `design-scoping`.
---

# Config & Secrets Management

Take a value that a running application needs but that shouldn't be hardcoded into its code — a database password, an API key, a feature toggle, a per-environment hostname — and decide exactly where it lives, how it gets to the process that needs it, whether it can be rotated without redeploying every consumer, and what happens if it leaks. The skill makes the user name the specific value and its sensitivity before any mechanism is recommended, because "we'll just use env vars for everything" and "let's put all our secrets in Vault" are both defaults that either under-protect a credential that needed rotation and audit, or over-engineer a feature toggle that never needed a dedicated secrets manager in the first place.

## When to use

- Someone is **choosing where a new value goes** — "should this API key be an env var or go in a secrets manager", "where do we store the Stripe key".
- Someone is **fixing a leak or a near-miss** — "we committed a secret to git", "our .env file has production credentials", "a secret showed up in a CI log".
- Someone is **designing rotation** — "how do we rotate the database password without downtime", "this token needs to expire and renew automatically".
- Someone is **introducing dynamic/runtime config** — "should this be a feature flag", "we want to change this without a redeploy", "LaunchDarkly vs a config file".
- Someone asks about **platform-native mechanisms** — "how does config work in Kubernetes", "ConfigMaps vs Secrets", "ECS task-definition secrets vs Parameter Store".
- Someone proposes an already-decided approach and wants it checked — "let's just use env vars for all of it", "we're putting everything in Vault, even non-sensitive config".

## Out of scope — hand these off

- **Who or what is authorized to read a secret once it's stored** — the IAM policy granting a service access to a Vault path or a Secrets Manager entry → `cloud-iam-boundary`. This skill decides where the value lives; that skill designs the grant to read it. The two compose on nearly every real secret.
- **Application-level end-user authorization** — which end user may view/edit/delete which resource → `access-control-modeling`. A completely different principal (an app user, not a service or a config value).
- **General encryption-at-rest of a datastore's disk**, unrelated to config/secrets specifically — still unowned in this catalog; name it and defer.
- **A specific datastore's own managed-rotation mechanics** (e.g., AWS RDS-managed credential rotation, the connection-pool behavior during a rotation) → `data-tier-operations`, once this skill has decided the value needs rotation at all.
- **Feature-flag-driven experimentation or A/B-testing methodology** — this skill decides the delivery mechanism for a config value (env var, secrets manager, dynamic config service); it does not design the experiment built on top of a flag.
- **Build/release/run pipeline mechanics** — how config gets baked into a release artifact vs injected at runtime → `deployment-strategy`, which this skill's storage-mechanism choice feeds.
- **Implementation** — the actual Vault policies, Terraform for a Secrets Manager entry, SDK integration code, the CI pipeline's secret injection step. This skill stops at a recommendation and an ADR.
- **An unscoped, not-yet-designed system** — "how should our new service handle config" with no named value yet → `design-scoping` first.
- **A bare conceptual question with no named value** — "what's the difference between Vault and AWS Secrets Manager", "what is a feature flag" — is answered directly, no gate.
- **Auditing a shipped product for secrets-in-version-control or policy-vs-practice gaps** → `disclosure-gap-audit`, which hands the fix here.
- **What changing a config value breaks elsewhere** → `change-surface-audit`.

---

## Incident first: a secret already leaked

If the request is "we committed/pasted/logged a secret", the gate does not delay the first move. Say up front, before any question: **revoke or rotate that credential now** — deleting the commit or log line does not un-leak it, and git history, forks and CI caches still hold it. Then run the gate for the *replacement* design (items 2–8).

## The gate

Before recommending a storage mechanism or rotation policy, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **What already exists** — a `.env` file, existing secrets-manager usage, orchestrator-native secrets already configured, a feature-flag service already in the stack.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any of 2–6 is missing, name it and stop (7–8 shape the mechanism choice: ask for them, but do not withhold the recommendation for a value whose sensitivity and rotation needs are already clear and where the platform is stated in the repo):

2. **The specific value** — name it concretely: "the Stripe API key," "the database password," "the checkout-page feature toggle" — not "our secrets" or "our config" collectively. Different values in the same system often want different answers.
3. **Sensitivity** — is this a credential/secret (its exposure grants access to something) or non-sensitive config (a timeout, a hostname, a feature toggle whose exposure causes no harm)? This single fact rules out entire mechanisms immediately — non-sensitive config rarely needs a secrets manager's rotation and audit machinery.
4. **Change frequency and redeploy coupling** — does this value need to change without a code deploy and without restarting the process (a feature flag toggled mid-incident), only between deploys (a per-environment hostname), or effectively never? A value that must change without a restart rules out plain env vars, which require a process restart to pick up a new value.
5. **Rotation requirement** — does this secret need periodic rotation (compliance-driven — PCI DSS, SOC 2 — or just good hygiene) or on-demand rotation after a suspected compromise? If it rotates, can every consumer pick up the new value without a coordinated, all-at-once redeploy, or does rotation currently mean "redeploy everything simultaneously and hope nothing calls with the old value mid-rollout"?
6. **Blast radius of a leak** — what's the actual damage if this specific value is exposed in a log, a CI job's output, a stack trace, or git history? A read-only feature-flag value leaking is not the same event as a production database's write credentials leaking — don't apply the same mechanism to both by default.
7. **Platform** — Kubernetes (native Secrets/ConfigMaps, or an External-Secrets-style operator syncing from a cloud secrets manager), a specific cloud provider (each with a native secrets service), or neither (VMs, on-prem, bare containers) — this changes what's already available "for free" versus what needs a new tool.
8. **Access and audit need** — does anyone need to know who read or changed this value and when (a compliance requirement, a security incident's forensic trail), or is that unnecessary for this value?

"Where should we store our secrets" with items 2–6 unanswered is not valid input — naming the specific value and its sensitivity (items 2–3) is one sentence and is the fact the rest of the recommendation depends on.

**Pressure does not open the gate.** "We need this shipped today, just make it an env var" is a reasonable default for a low-sensitivity, low-change-frequency value — but only once items 2–3 are actually named, not assumed. A genuine secret shipped as a bare env var under deadline pressure is exactly how credentials end up in shell history, process listings, and CI logs.

---

## Challenge a proposed approach

If the user opens with the mechanism already chosen, put their reasoning under the gate, then test the specific claim against `mechanisms-and-tradeoffs.md`:

- **"let's just use env vars for everything"** — for the specific value named (item 2), is it sensitive (item 3)? Env vars have no rotation story without a restart, show up in process listings and often in crash dumps or error-tracking payloads, and have no per-secret access audit. Fine for non-sensitive config; a real credential deserves better.
- **"we're putting everything in Vault, even feature flags"** — does a non-sensitive, frequently-toggled value (item 3, item 4) need Vault's access-control and audit machinery, or is that solving a problem this value doesn't have? A dynamic config service or even a simple database row may fit better and be far cheaper to operate.
- **"we'll rotate it manually when we remember"** — is there an actual rotation requirement (item 5, compliance or hygiene)? "Manually, when we remember" is not a rotation policy; if compliance requires periodic rotation, that has to be automatable, not a calendar reminder to a person who may leave the team.
- **"the .env file isn't committed, so it's fine"** — is it fine in CI logs, in a support engineer's terminal history, in an error-tracking tool that captures environment snapshots on crash? Not being in git is necessary but not sufficient — ask where else the value could leak (item 6).
- **"we need a feature-flag service so we can change anything instantly"** — what happens when the flag service is unreachable? Every dynamic-config approach needs a safe local default the app falls back to, or the flag service itself becomes a new single point of failure for values that used to just work. Name the fallback behavior, not just the happy path.
- **"rotating this secret means redeploying every service that uses it"** — that's the sign this secret should move to a mechanism supporting live rotation (a secrets manager the app polls or is pushed updates from) rather than a baked-in env var, especially if rotation is required on-demand after a suspected compromise (item 5) and a coordinated redeploy is too slow for that.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `mechanisms-and-tradeoffs.md` once the gate is satisfied. In short: name the specific value and its sensitivity (items 2–3) → check change frequency against redeploy coupling (item 4) — if it must change without a restart, dynamic config/feature-flag territory; if not, continue → check the rotation requirement (item 5) — if real rotation without a coordinated redeploy is needed, a secrets manager or orchestrator-native secret with live sync, not a baked-in env var → weigh the blast radius of a leak (item 6) against the platform's native options (item 7) → name the audit requirement (item 8) → recommend one mechanism per value (not one mechanism for everything) → record.

Reference file:

- `mechanisms-and-tradeoffs.md` — plain env vars vs orchestrator-native secrets vs a dedicated secrets manager vs a dynamic config/feature-flag service: what each protects against, what it costs operationally, and its failure mode when misapplied; rotation mechanics and the "redeploy everything" anti-pattern; where a value commonly leaks besides git; the fallback-default requirement for dynamic config.

---

## Output

**1. In chat, a recommendation block:**

```
Value:                 <the specific config/secret named>
Sensitivity:           <credential/secret | non-sensitive config>
Change frequency:      <static per-deploy | must change without a restart>
Rotation requirement:  <none | periodic (compliance/hygiene) | on-demand (post-compromise)>
Blast radius if leaked: <what's actually exposed or accessible>
Platform:              <Kubernetes | cloud-native (name provider) | neither>
Mechanism:             <plain env var | orchestrator-native secret | dedicated secrets manager (name it) | dynamic config/feature-flag service (name it)>
Rotation path:         <how a rotated value reaches every consumer without a coordinated redeploy, or "not needed">
Audit:                 <who can see access/change history, or "not needed for this value">
Agent access surface:  <does the mechanism have a scriptable read/rotate API an agent could use (most dedicated secrets managers do) vs. a plain env var an agent only sees via the process environment — named here; whether an agent *should* get that access is cloud-iam-boundary / access-control-modeling's call>
Tradeoffs accepted:    <2-4 concrete costs: operational burden of running a secrets manager, no-audit-trail risk of plain env vars, a new SPOF from a dynamic config service without a fallback>
Not chosen because:    <one line per rejected mechanism>
Follow-ups:            <cloud-iam-boundary for the access grant to read this value; data-tier-operations if this is a datastore credential with managed rotation; observability-strategy for audit-log alerting>
```

Any field you cannot fill from the user's own words is `UNANSWERED`. A block with `UNANSWERED` fields on items 2–6 ends the response.

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering). Fill "Revisit when" with a concrete trigger — "this value's rotation requirement changes (a compliance regime now applies)", "a second consumer needs this value and the current mechanism doesn't support fan-out cleanly", "the dynamic-config service has an outage and the fallback-default gap becomes a real incident."

Then stop. Implementation — the actual secrets-manager entries, IaC, SDK wiring — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked the decision — the value and its sensitivity named, rotation and platform checked, the leak blast-radius considered — and wants a review or a tie-break rather than a Socratic pass, they can say so and get a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "We have a Stripe secret API key currently sitting in a `.env` file that's gitignored but gets loaded as a plain env var in production. PCI compliance now requires we rotate API keys quarterly, and rotating today means coordinating a redeploy of the 3 services that use it, timed together, which is nerve-wracking. We're on AWS, using ECS."

Gate satisfied. Value: Stripe API key (item 2). Sensitivity: credential (item 3) — grants payment-processing access. Change frequency: quarterly rotation, ideally without a coordinated redeploy (item 4). Rotation: required, compliance-driven (item 5) — the exact pain point named. Blast radius: full payment-processing access if leaked (item 6) — high. Platform: AWS ECS (item 7) — AWS Secrets Manager integrates natively with ECS task definitions. Recommendation: move the key into **AWS Secrets Manager**, referenced from each of the 3 services' ECS task definitions as a secret (not a plain environment variable baked at deploy time) — ECS re-fetches the current value from Secrets Manager at task launch, so a rotation followed by a rolling restart of each service (not a simultaneous coordinated redeploy) picks up the new value without the "all three at once" nervousness. Enable Secrets Manager's automatic rotation on a 90-day schedule (satisfies quarterly). Audit: Secrets Manager's access logging via CloudTrail, satisfying the audit need (item 8) implicitly. Tradeoffs: one more AWS service to operate and pay for; a brief window where old and new keys must both be valid at Stripe during rollover (name this as a Stripe-side rotation-window requirement, not this skill's to solve). Not chosen: keep it as a plain env var (no native rotation path, exactly the current pain); a dynamic config service (overkill for a value that only needs to change on a rotation schedule, not on-demand toggling). Follow-ups: `cloud-iam-boundary` for the IAM role granting each service's task read access to this specific Secrets Manager entry. ADR; revisit when a 4th service needs this key (confirm the rotation rollout order still avoids overlap gaps).

> "Where should we store our secrets?"

Gate not satisfied — item 2 (which secret, specifically — there's rarely one uniform answer for all of them), item 3 (sensitivity varies per value); the platform (item 7) is also unstated — ask for it alongside. Response: ask for one concrete value to start with, and what platform it runs on. Do not recommend a single mechanism for "secrets" as an undifferentiated category.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Vocabulary (secrets manager, dynamic config, rotation) is provider-neutral; platform-specific mechanics (ECS task-definition secrets vs Kubernetes Secrets vs Vault) are named in the gate rather than assumed. Copy the `config-and-secrets-management/` directory into another repo's `.claude/skills/` to use it there.

## Routing boundaries (full)

The frontmatter `description` is truncated in the skill listing, so the full boundary rules live here (moved verbatim from the original description):

- Not for who or what is authorized to read a secret once it's stored in a cloud secrets manager — that is `cloud-iam-boundary`, which this skill hands the access-grant question to once the storage mechanism is chosen; this skill decides where a value lives, that skill decides who may read it.
- Not for which end user may perform which action in the application — that is `access-control-modeling`, a different principal entirely (an app user, not a service or a config value).
- Not for general encryption-at-rest of a datastore's underlying disk, unrelated to config/secrets specifically — still unowned, name it and defer.
- Not for a specific datastore's own managed-rotation mechanics (e.g., RDS-managed credential rotation) once this skill has decided the value should rotate — that is `data-tier-operations`, which this skill hands the rotation requirement to.
- Not for feature-flag-driven experimentation or A/B-testing methodology — this skill only decides the delivery mechanism for a config value, not the product experimentation strategy built on top of it.
- Not for an unscoped, not-yet-designed system — that is `design-scoping` first.
- A bare conceptual question with no named value ("what's the difference between Vault and AWS Secrets Manager", "what is a feature flag") is answered directly, no gate — the gate exists for a pending decision on a named config/secret, not for explaining the vocabulary.
- Not for auditing a shipped product's disclosures or design for secrets-in-version-control gaps — that is `disclosure-gap-audit`, which hands the fix here.
- Not for how a deploy or rollout delivers a new version — that is `deployment-strategy`.
- Not for what a change to a config value breaks elsewhere — that is `change-surface-audit`.
- Gated decision for where application config and secrets live and how they reach a running process — env vars, orchestrator-native secrets, a secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault), or a dynamic config/feature-flag service (LaunchDarkly, Consul KV, etcd), plus rotation policy and leak blast radius.
- Use when someone says "where should we store our API keys/secrets", "should this be an env var or in a secrets manager", "how do we rotate our database password without downtime", "we committed a secret to git", "should we use LaunchDarkly / a feature flag for this", "our .env file has production credentials in it", "how do services get their config in Kubernetes", or proposes a config/secrets approach to check.
- Forces the specific value, sensitivity, change frequency, rotation need, platform and leak damage before recommending; records an ADR.
- A bare conceptual question ("what's the difference between Vault and AWS Secrets Manager", "what is a feature flag") is answered directly, no gate.
- Not for who may read a secret — `cloud-iam-boundary`.
- Not for app user permissions — `access-control-modeling`.
- Not for datastore rotation mechanics — `data-tier-operations`.
- Not for an unscoped system — `design-scoping`.
- Not for `disclosure-gap-audit`, `deployment-strategy`, or `change-surface-audit`.
