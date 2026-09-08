# design-scoping skill

The **front-door gate for a system-design effort**. It refuses to start designing until the
user has stated five things — purpose + audience, functional requirements + an explicit
out-of-scope list, the non-functional numeric targets (RPS ceiling, concurrency, latency
budget, uptime, error budget, cost cap), the constraints (team, timeline, existing stack,
platforms, compliance regime), and which one or two decisions are worth designing deeply
now. Its output is a written **scope statement** that then sequences into the specialist
Architecture skills.

Consolidated from three source notes — `Architecture/01. System Design/Specifying Scope
indepth.md` (purpose/audience, functional vs additional, the scope-question method),
`Architecture/01. System Design/Userbase.md` (user-base characterization + the compliance
checklist), `Architecture/Define system threshold.md` (the non-functional numeric targets)
— plus the blast-radius / who-cares / migration-tell classifier from `Architecture/
Boundaries of LLD and HLD.md`, used as the significance filter for the deep-dive selection.

## Where it sits

```
design-scoping        →  purpose · audience · functional + out-of-scope · numeric targets · constraints · the 1–2 to design deep   (this skill)  → scope statement
      │
      ├─ capacity-estimation      →  audience + throughput targets → QPS / storage / bandwidth / what binds first
      ├─ microservices-decision   →  one service or several, and the boundaries
      ├─ api-interface-style      →  the surface style per boundary
      ├─ database-architecture    →  where the source of truth lives + which store
      └─ failure-mode-analysis    →  the failure surface of the resulting design, before sign-off
```

It is the **first** skill in an Architecture pass — everything else consumes its scope
statement. It does not do any of the deep design itself; it decides *which* one or two
decisions deserve it and routes them.

## The shape

A gate skill (same shape as `capacity-estimation`, `resilience-strategy`,
`database-architecture`). It refuses to produce a design, a structure, or a technology
recommendation until the five dimensions are stated by the user. "Design a system for X"
with the dimensions absent gets the list of what's missing, framed as the scope the user
must commit to — not an invented purpose and a set of made-up targets.

The **highest absorption risk** in the library: `ambiguity-gate` already claims "unstated
scope". The boundary, mirrored from the `test-practice-gate` ↔ `ambiguity-gate` precedent:
`ambiguity-gate` resolves *what a vague request even asks for* ("help with my system",
"make it better"); `design-scoping` takes over *once "design / architect a system or
feature" is the established intent* and does the system-design-specific decomposition
(functional / non-functional / scale numbers / deep-dive feature selection) that
`ambiguity-gate` wouldn't know to ask for. A second line runs vs `ticket-evaluation`: that
skill judges/sizes a *defined* ticket; this one elaborates scope on an *under-specified*
design ask.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The five-dimension gate, the significance filter for deep-dive selection, challenge-a-proposed-scope, the scope-statement output contract + the specialist-skill sequence. |
| `scope-dimensions.md` | The five dimensions expanded — purpose/audience + user-base characterization; functional + the required out-of-scope list; the non-functional target checklist with what each number drives downstream; the constraints list with the GDPR / HIPAA / PCI DSS / SOC 2 / data-residency cheat-sheet. |
| `significance-filter.md` | The blast-radius / who-cares / migration-tell classifier in full, worked against example decisions, with the explicit note that it is *scope of impact*, not the cost-to-replace axis (`technical-cost-decision`). |

## Output

1. A scope statement in chat — purpose, audience, in-scope, explicitly-out, the six
   non-functional targets (each a number or an explicit "not constrained"), constraints
   (compliance last and explicit), the 1–2 deep-dive decisions with their blast radius, the
   acknowledged-deferred list, and the specialist-skill sequence.
2. On approval: a **living document** at `docs/architecture/scope/<system-slug>.md` (not an
   ADR — it's updated as scope changes). Each deep-dive decision gets its own ADR later,
   from the specialist skill that owns it.

## Interaction with sibling skills

- **Defers to `ambiguity-gate`** — for "what does this request even mean"; takes over once
  "design a system/feature" is established. If `skill-interaction-testing` shows
  `ambiguity-gate` still swallows system-design requests, a one-line hand-off clause goes
  into `ambiguity-gate` pointing them here.
- **Distinct from `ticket-evaluation`** — defined ticket → that skill; under-specified
  design ask → here.
- **Sequences into** `capacity-estimation`, `microservices-decision`, `api-interface-style`,
  `database-architecture`, `failure-mode-analysis` — names them and the order; does not do
  their jobs.
- **Hands cost questions to `technical-cost-decision`** — the cost cap is a scope input; the
  bill sizing and the reversibility/cost-to-replace axis are that skill's.
- **`learning-gate`** Step 3 routes "how do I scope a system design" here rather than
  running its own rep gate.

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `ambiguity-gate` (vague request vs system-design scope decomposition — the sharp
one), `ticket-evaluation` (defined vs under-specified), and the five downstream skills
(scope vs the deep design each owns).

## Using it in another repo

Repo-agnostic. Writes a living scope statement to `docs/architecture/scope/`.

```
cp -r ".claude/skills/Architecture/design-scoping" /path/to/other-repo/.claude/skills/
```
