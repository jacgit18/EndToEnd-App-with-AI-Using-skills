# config-and-secrets-management skill

A gated decision for **where application configuration and secrets live and how they reach
a running process** — plain environment variables, orchestrator-native secrets (Kubernetes
Secrets/ConfigMaps, ECS task-definition secrets), a dedicated secrets manager (Vault, AWS
Secrets Manager, GCP Secret Manager, Azure Key Vault), or a dynamic config/feature-flag
service for values that must change without a redeploy. Also covers rotation policy and the
blast radius of a leak. Given a value a running app needs but shouldn't have hardcoded, the
skill makes the user name that specific value, its sensitivity, its change frequency, and
its rotation requirement before any mechanism is recommended, then writes an ADR.

Built from an audit of `Architecture/Twelve Factor App Design Framework/` — the "Config"
factor ("store config in the environment") and the "Configuration Changes" admin-process
note both circle a question 12-factor (written in 2011) never addresses: env vars vs a real
secrets manager vs dynamic config. `cloud-iam-boundary` had already flagged this twice as an
explicitly unowned gap ("Not for encryption-at-rest/in-transit or secrets/key rotation... no
skill owns it yet"). This skill closes the secrets/config half of that gap; general
at-rest encryption of a datastore's disk, unrelated to config/secrets specifically, remains
unowned.

## Where it sits

```
config-and-secrets-management  →  where a value lives, how it's delivered, rotation policy   (this skill) → ADR
cloud-iam-boundary               →  who/what is authorized to read the value once it's stored
access-control-modeling          →  a completely different principal (an app end user, not a
                                    service or a config value)
data-tier-operations             →  a specific datastore's own managed-rotation mechanics,
                                    once this skill says the value should rotate
deployment-strategy               →  how a chosen mechanism's value gets injected at
                                    build/release/run time
observability-strategy           →  alerting on a secrets manager's audit log
```

## The shape

A gate skill, same family as the other Architecture decision skills. It refuses to
recommend a mechanism until the user supplies, **per value** (not once for the whole
system):

- **the specific value**, named concretely — not "our secrets" collectively
- **sensitivity** — a credential/secret vs non-sensitive config
- **change frequency** — must it change without a restart, or only between deploys
- **rotation requirement** — none, periodic (compliance), or on-demand (post-compromise) —
  and whether rotating today means a fragile "redeploy everything at once"
- **blast radius of a leak** — what's actually exposed if this value gets out
- **platform** — Kubernetes, a specific cloud, or neither

Then it recommends one of four mechanisms (env var / orchestrator-native / secrets manager /
dynamic config service), names the rotation path, and writes an ADR.

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/`.

```
cp -r .claude/skills/Architecture/config-and-secrets-management /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Run `skill-interaction-testing` when this skill or a sibling's description changes. Known
boundaries to hold:

- **vs `cloud-iam-boundary`** — this skill decides where a value lives and how it's
  delivered; that skill decides who/what is authorized to read it once stored. They compose
  on nearly every real secret (a Secrets Manager entry needs both a storage decision here
  and an IAM grant there).
- **vs `access-control-modeling`** — different principal entirely (an application end user
  vs a service or a config value). No real overlap risk, but named explicitly since both
  skills use the word "access."
- **vs `data-tier-operations`** — that skill owns a specific datastore's own rotation
  mechanics (e.g., RDS-managed rotation); this skill decides whether a value needs to rotate
  at all and hands the "how does the DB itself do it" question there.
