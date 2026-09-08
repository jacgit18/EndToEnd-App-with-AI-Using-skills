# architecture skill

A gated decision process for data-architecture choices: where a piece of data's source of truth
should live (database-first / code-first / contract-first), what the system boundaries are, and
what gets generated from that — recorded as an ADR.

Built from `database schema disscusiion.md`, plus `Architecture/02. Backing Service Options/File
System Storage.md` (the `store-options.md` reference — object / block / DFS storage, blob-vs-row).
It deliberately does **not** encode "always contract-first"; it encodes the process for deciding.
The AWS service-name mapping tables in `store-options.md` were added `2026-09-04` from
`Architecture/02. Backing Service Options/Cloud/AWS/Cloud Storage.md`, `Cloud Databases.md`,
and `AWS/Cloud Storage & Databases.md`.


ADR = Architecture Decision Record (sometimes "Architectural Decision Record").

It's a short markdown file that captures one significant architectural decision and the reasoning behind it, kept in version control next to the code. The format (popularized by Michael Nygard in 2011) is typically:

Context — the situation and forces at play when you decided
Decision — what you chose
Consequences — what you accepted as a result, what you rejected, and what would make you revisit
Conventions:

Numbered sequentially — 001-source-of-truth.md, 002-api-contract.md
Append-only — you don't edit a past ADR to change the decision; you write a new one that "supersedes" it
The point is memory: six months later, "why is the database model different from our API?" is answered by reading 003 instead of guessing
In this skill, the ADR is the artifact written to docs/architecture/decisions/ once you approve a recommendation — see adr-template.md.

(I notice the folder is now database-architecture/ — you renamed it from architecture/. The skill name in its frontmatter still says name: architecture; you'll want those to match.)


## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The hard gate, the challenge-the-proposal behavior, the output contract. |
| `decision-framework.md` | The 7-step process Claude works once the gate is satisfied. |
| `schema-taxonomy.md` | The "which schema do you mean" reference — DB / domain / API / validation / type. |
| `store-options.md` | Where large binaries live — object vs block vs distributed-file-system storage, the blob-in-object-storage vs DB-row decision, large-binary patterns, the controls for regulated data on object storage (HIPAA / GDPR / PCI), and concrete AWS service-name mappings for both the storage shapes and the eight database paradigms. |
| `adr-template.md` | The ADR format written to `docs/architecture/decisions/NNN-*.md` on approval. |

## What it produces

1. A recommendation block in chat (approach, source of truth, persistence, access, validation,
   mapping, tradeoffs).
2. On approval: a numbered ADR in `docs/architecture/decisions/` in the repo it's invoked from.

It stops before implementation. Migrations, models, DTOs, and wiring are a separate step you
start explicitly after the ADR exists.

## Design choices

- **Hard gate**, in the style of `problem-solving-gates`: Claude will not emit a schema or
  recommendation until the user answers consumers / ownership / exposure / evolution /
  source-of-truth leaning / contract leaning **in their own words**. Facts visible in the repo
  (DB technology, existing specs) Claude may surface for confirmation.
- **Recommendation + ADR**, no separate project-context file. The ADRs themselves are the
  standing architectural memory.

## Using it in another repo

The skill is repo-agnostic — it reads and writes `docs/architecture/` relative to wherever it's
invoked. To vendor it:

```
cp -r .claude/skills/architecture /path/to/other-repo/.claude/skills/
```

Nothing else to configure. First run in a repo creates `docs/architecture/decisions/` and
starts numbering at `001`.

## Not built (yet)

Relational modeling detail (normalization, indexes, constraints, keys, lifecycle columns) now
lives in the **`relational-modeling`** sibling skill — this skill hands off to it after the
ADR exists.

Scaling and distribution (sharding, replication topology, transaction isolation, 2PC/Saga,
pooling, failover) now live in the **`data-tier-operations`** sibling skill, which reuses this
skill's `adr-template.md`.

Analytical / dimensional modeling (star/snowflake, fact/dimension, grain, SCD, warehouses/marts)
now lives in the **`dimensional-modeling`** sibling skill.

Still not built: contract authoring (versioning, compatibility, DTO design). The source
discussion also sketched an `implementation` agent. Those become sibling skills if they start
needing their own repeatable process.


## To try 
Invoke /architecture (or just start a data-modeling request) with a real feature. Fastest sanity check: give it "design the schema for X" with no context — it should name what's missing and stop, not draft anything. Then give it a fully-specified request like the billing example in SKILL.md and confirm the recommendation block + ADR come out the way you want. Adjust the gate list or ADR fields from there.