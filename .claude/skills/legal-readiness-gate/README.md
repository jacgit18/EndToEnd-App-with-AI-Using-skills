# legal-readiness-gate skill

A gate skill, same shape as `design-scoping` and `pwa-adoption`. Works out what an app owes
its users and customers — consent, user rights, vendor agreements, published documents, SLA
and contract terms, and the extra tier for health data — for the stage it is at and the one
after. Flag-only: it names regimes and who confirms them, and never gives a legal verdict.

## Where it sits

```
design-scoping          →  scope statement; compliance is one line in "Constraints"
legal-readiness-gate    →  what that line obliges you to build, sign and publish, by stage   ← this skill
disclosure-gap-audit    →  after launch: do the published documents match what the product does
reliability-math        →  can the architecture actually hit the SLA number
```

`disclosure-gap-audit` already carries an L1–L6 legal flag list, but it audits a product that
exists and makes public claims. Nothing in the catalog answered the earlier question: *what
should I be building and publishing, given my data, users and stage?* This skill fills that gap
and hands the after-the-fact check back to the audit.

## The shape

Refuses to produce a checklist until the user states:

- **data classes held** — including health, financial, children's, biometric, location
- **user jurisdictions** — where users are, not where the server is
- **the operator's role** — controller / processor, and the HIPAA fork for health data
- **customer type** — consumer / business / enterprise
- **stage and the next step**

and (surfaced from the repo for confirmation) what the app already collects and sends where.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point: the gate, challenges, process, output block, escape hatch. |
| `obligations-by-stage.md` | Data lifecycle, lawful basis and consent, user-rights clocks, retention, vendors and transfers, breach response, children, documents to publish, stage ladder. |
| `sla-and-contracts.md` | SLA anatomy and credits, support terms, liability, DPA, ownership and exit, attestations (SOC 2, ISO), auto-renewal, accessibility. |
| `health-data.md` | The HIPAA fork, FTC and state consumer-health rules, GDPR Art. 9, design consequences, BAA vendor constraint, LLM use, device claims. |

The reference files carry dated facts (rule status, clocks) as of 2026-10; re-verify before
relying on them.

## Output

1. An obligations block in chat (inputs, regimes flagged, build / sign / publish, SLA and
   contract, time-sensitive items, only-counsel questions, agent-drivable, revisit trigger).
2. On approval: a living checklist at `docs/legal/readiness/<slug>.md` (resolved to the
   DevHiveMind docs root for projects whose docs live there). Not an ADR.

Stops before drafting policy or contract text and before implementing a control.

## Interaction with sibling skills

- **Defers to `disclosure-gap-audit`** for checking live documents against behaviour; hands
  there once the product is shipping. The reverse pointer is in that skill's description.
- **Receives from `design-scoping`** when the compliance constraint needs unpacking.
- **Defers to `reliability-math`** for whether an SLA number is reachable;
  **`access-control-modeling`**, **`config-and-secrets-management`**,
  **`cloud-iam-boundary`**, **`observability-strategy`**, **`data-tier-operations`** for
  designing the controls it names.
- **Defers to `technical-cost-decision`** for what an audit, pen test or insurance costs.
- **`learning-gate`** should hand legal/compliance "what do I need" questions here rather than
  running its own rep gate.

Re-check overlap after any trigger-description change: the closest neighbours are
`disclosure-gap-audit` and `design-scoping`.

## Shipping

Packaged in `architecture-skills` (relative symlink, plugin version 0.4.0; see
`plugins/README.md`). Needs no repo setup; siblings are listed in `SKILL.md` → Portability with
inline fallbacks.
