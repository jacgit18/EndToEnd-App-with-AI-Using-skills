# The Significance Filter

For gate item 6 in `SKILL.md` — deciding which one or two decisions get designed deeply and
written down *now*, and which are acknowledged and deferred to implementation time. Ported
from `Architecture/Boundaries of LLD and HLD.md`.

The failure this prevents runs both ways: designing all forty decisions up front (waterfall,
and most of them will change), or treating a foundational decision as "just an
implementation detail" and getting boxed in six months later.

When the user has already named their 1–2 picks, run the filter over each one anyway — to
confirm it's genuinely load-bearing (occasionally a named pick is really mid-level and a
different decision deserves the slot) and to produce the blast-radius sentence the scope
statement records. If two picks are coupled — one's design is an input to the other's —
note it and design the upstream one first.

---

## The three tests

Apply all three to each candidate decision and read the *significance* off them: a decision
that scores **high on all three** — wide blast radius, an architect's call, a migration to
undo — is a deep-dive-now item. One that scores **low on all three** — local blast radius,
a developer's call, trivially reversible — is safe to defer. Mixed results sit in the
middle: deep-dive only if it's on the critical path for the purpose (gate item 2).

### 1. Blast radius — "if I change this later, how much breaks?"

| If changing it later touches… | Level | Deep-dive now? |
|---|---|---|
| The whole system, or the data model | High-level | **Yes** |
| Many modules / several teams' code | Mid-level | Only if it's on the critical path for the purpose |
| One function / one module | Low-level | No — decide it while implementing |

### 2. Who cares — who needs to be in the room for this decision

- An **architect** would need to weigh in → high-level → deep-dive candidate.
- A **team lead** → mid-level.
- An **individual developer**, alone, at the keyboard → low-level → not now.

If you'd feel the need to call a design meeting for it, it's a candidate. If you'd just
pick one and move on, it isn't.

### 3. The migration tell

If changing the decision later would require a **migration plan, a data rewrite, or an
operational change**, it was never low-level — no matter how small the code diff looks.

Decisions that routinely get mislabeled "implementation detail" and shouldn't be:

- The primary datastore / persistence engine
- The service boundaries (what's one service vs several)
- The public API shape and its versioning approach
- The auth / identity mechanism
- The serialization / wire format for stored or messaged data
- The ORM or data-access layer
- The multi-tenancy model (shared schema / schema-per-tenant / DB-per-tenant)
- The primary-key / ID scheme for core entities

---

## Worked examples

| Candidate decision | Blast radius | Who cares | Migration to undo? | Verdict |
|---|---|---|---|---|
| Which datastore holds orders | Whole data model | Architect | Yes — data migration + dual-write | **Deep-dive now** |
| Service boundaries for a payments split | Whole system | Architect | Yes — extract + cutover | **Deep-dive now** |
| The retry/backoff policy on one outbound call | One module | Team lead | No | Defer |
| Which date library the frontend uses | One function's worth | A developer | No | Defer |
| REST vs event-driven for the public API | Whole system, every consumer | Architect | Yes — every integration re-does its client | **Deep-dive now** |
| Log format / structured-logging fields | Many modules | Team lead | Painful but not a migration | Defer — with a written convention |
| The pagination style on internal list endpoints | Many endpoints | Team lead | No — additive change | Defer |
| Multi-tenancy model (shared vs isolated schema) | Whole data model + ops | Architect | Yes — the hardest kind of migration | **Deep-dive now** |

Most scope statements land on **one or two** "deep-dive now" decisions. If the filter is
producing five, either the system genuinely is a large architecture program (say so, and
scope a first phase), or "critical path for the purpose" (test 1, mid-level row) is being
read too generously — tighten it to "the purpose in gate item 2 fails without this decided
right".

---

## What this filter is NOT

It is **not** the reversibility / cost-to-replace analysis. "How expensive is this to
change later, in engineer-weeks and dollars" is a different axis and it lives in
`technical-cost-decision`. This filter is about **scope of impact** — how much of the system
a change ripples through — which is what decides whether the decision needs *design and a
written record now*, regardless of what the rebuild would cost.

The two often agree (a whole-data-model decision is usually also expensive to reverse), but
when they diverge, keep them separate: a decision can be wide blast radius but cheap to
change (a shared enum), or narrow but expensive (a gnarly one-module algorithm). This
filter cares about the first number; `technical-cost-decision` cares about the second.

---

## Feeding the scope statement

For each "deep-dive now" decision, the scope statement records:

- The decision, in one line.
- Its blast radius (which of the three tests it failed, concretely — "changing this is a
  data migration + every consumer re-integrates").
- Which specialist skill owns the deep design: `capacity-estimation`,
  `microservices-decision`, `api-interface-style`, `database-architecture`, or
  `failure-mode-analysis`.

Everything that passed the filter goes in the **"acknowledged, deferred"** list — named, so
it isn't forgotten, with a one-line note of when it gets decided ("during implementation of
the X module", "in the phase-2 design pass").
