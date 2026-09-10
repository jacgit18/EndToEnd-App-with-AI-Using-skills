# Decision loop

The per-decision protocol for `tech-decision-walkthrough`, the two registers in detail, axes
libraries for the decisions a build hits most often, and the ADR shape. Operate at the
assistance level `learning-gate` set — this file is *how* the loop runs at levels 1–3, it
doesn't lift the ceiling.

## The two registers

| | Collaborative (default) | Interviewer |
|---|---|---|
| Assistance level | 3 | 1–2 |
| Who names the candidates | Claude | The user first; Claude adds what's missing |
| Who names the axes | Claude, before scoring | The user; Claude prompts the ones they skipped |
| Who scores | Claude, user reacts | The user; Claude challenges soft spots |
| The recommendation | Claude gives it with a because; user decides | The user commits and defends; Claude stress-tests, then confirms or pushes back |
| Trigger | Default | "let me drive", "quiz me", "interview me", "make me choose" |

Switch on request, mid-walkthrough, either direction. In interviewer register, do **not** hand
the user a shortlist of candidates or a leading question that names the answer — same rule as
`problem-solving-gates`. Ask "what are you considering, and why?" and coach from there.

## The loop, per decision

### 1. Frame it

One sentence: what is being decided, and what forces it *now*. "We need a datastore before the
data-access layer, and the money + reporting requirements make this load-bearing." If nothing
forces it yet, defer the decision — don't walk it early.

### 2. Get the user's starting position

Ask for their lean and the constraints they already hold:

- **Team** — what the people building and maintaining this already know well.
- **Existing systems** — what it has to run next to, talk to, or match.
- **Ops capacity** — who operates it, and how much operational surface they can carry.
- **Deadline** — is there a date that rules out a learning curve.
- **Cost ceiling** — a stated budget, or a per-unit third-party charge in the path.
- **Compliance / policy** — data residency, retention, an approved-tech list.

"No lean" is a valid answer; note it and continue. A lean with a reason is the rep in
interviewer register — get the reason.

**Register changes the timing.** In **interviewer** register, stop here and wait — the user's
lean and reasoning come before any candidates are shown. In **collaborative** register, ask for
the lean in the *same* turn as the candidate set (steps 3–6); don't block the whole loop waiting
for it. The user asked for the decision walked — walk it, with the lean question up front.

### 3. Candidate set

2–4 options that are *realistic for this build*. Not every option in the category — the ones a
competent engineer would actually shortlist given Step 2. One line each:

```
<name> — <what it is in a clause>. Shines: <where it's clearly best>. Hurts: <where it costs>.
```

If the user named a candidate that shouldn't be on the list, say why once and drop it — don't
score a strawman through the whole table.

**If the user flags unfamiliarity** with a candidate, a concept, or the whole domain ("not
familiar with X", "explain this one", "no idea what that means"), expand that item to
teach-it depth *before* scoring or asking for a decision — how it works, why it exists, a
concrete example, what real systems do. Don't stay at one-line-each depth and don't make them
choose blind. This is `learning-gate` S0 inside the loop; it holds for the rest of the
walkthrough once they've said it, not just that one turn.

### 4. Deciding axes

The 2–4 dimensions that actually discriminate *here*. Name them before scoring so the reasoning
is visible, not smuggled into a verdict. Pull from the libraries below; cut any axis on which
all candidates score the same — it isn't deciding anything.

### 5. Score against the axes

A compact table or a short per-candidate read. Rules:

- Every candidate wins at least one axis or it shouldn't have been a candidate.
- The recommended option must **lose** at least one axis, stated plainly. A comparison where the
  winner sweeps is either a strawman field or a missing axis.
- Score for *this* build's constraints, not the general case ("Postgres' clustering story is
  weaker — irrelevant here, single node forever").

### 6. Recommendation + because

One option. The because cites a named axis and a Step 2 constraint: "Postgres — the reporting
queries are relational and multi-table (axis: query fit) and the team runs Postgres already
(constraint: ops). SQLite's single-writer limit isn't the blocker; the query fit is." No hedge,
no "you could go either way" unless it is genuinely a coin flip — and then say *that*, with the
tiebreaker.

### 7. User decides

They agree, override, or ask for another round. On override: record their stated reason in the
ADR as the decision rationale. Don't re-litigate a decided call; note a risk once if you see one
and move on.

### 8. Record it

ADR to `docs/architecture/decisions/NNN-<slug>.md`:

```
# ADR NNN — <decision title>

- Status: Accepted
- Date: <YYYY-MM-DD>
- Deciders: <who>

## Context
<what forced the decision; the constraints from Step 2>

## Decision
<the choice, one or two sentences>

## Alternatives considered
- <candidate> — <the axis it lost on>
- <candidate> — <the axis it lost on>

## Consequences
<what this makes easy, what it makes hard, what to revisit and when>
```

For a load-bearing decision, run the specialist skill (`database-architecture`,
`api-interface-style`, `microservices-decision`, `access-control-modeling`, …) first and fold its
recommendation block into Context + Decision. Hand the specialist the scope, the Step 2
constraints, and the user's lean so it *confirms* those inputs rather than re-running its own
front-door gate from zero — a second wall of questions on one decision is the stacking failure.

---

## When cost is a deciding axis

If a decision carries a real recurring price — compute, storage, database instances, a
managed-service premium, egress / CDN, per-request or per-token API charges, background-job
minutes, log / telemetry ingestion — give **two reads**, not one:

1. **The user's actual plan.** Size the cost for their stated scale and hosting (from the scope:
   users, RPS, GB, budget cap). Invoke `technical-cost-decision` for the Cost Surface when the
   arithmetic is non-trivial; name the dominant line. At hobby / single-user / self-hosted
   scale the honest answer is often "no meaningful difference between the candidates" — say that
   plainly; don't manufacture one.
2. **A realistic-scale example, for learning.** One short paragraph: pick a plausible production
   scale, state the cost driver explicitly ("50k MAU", "500 RPS peak", "2 TB egress/mo", "10M
   API calls/mo", "300M rows"), and give ballpark monthly figures for each candidate with the
   dominant line called out. A few lines — a teaching aid, not a second full Cost Surface.

This applies to every cost-bearing domain, not just infra: API request volume, web traffic and
CDN egress, LLM token spend, job minutes, telemetry ingestion.

If a decision genuinely has no cost dimension — a data-type choice, a code-structure choice,
two options that are the same byte on disk — say so and cut the axis. Don't invent numbers to
fill a table cell.

## Axes libraries

Starting axes for common build decisions. Not exhaustive; drop the ones that don't discriminate,
add build-specific ones.

### Language / runtime
Candidates usually among: Python, Node/TypeScript, Go, a JVM language, Ruby.
Axes: team familiarity · ecosystem fit for the domain (data/ML, CSV/finance, systems, web) ·
concurrency model needs · deployment footprint & cold-start · hiring / long-term maintenance.

### Web framework
Within a chosen language — e.g. Python: FastAPI, Django, Flask.
Axes: batteries-included vs. compose-it-yourself · built-in admin / ORM / auth vs. bring-your-own
· async support · API-first vs. server-rendered · community size & longevity.

### Datastore
Candidates: a relational DB (Postgres, MySQL), SQLite, a document store, a KV store, a
search/analytics engine — often more than one.
Axes: data shape (relational / document / key-value / time-series) · query patterns (joins,
aggregations, full-text, ad-hoc) · consistency & transaction needs · scale & write volume vs.
single-node-forever · ops burden & backup story · team familiarity.

### Data-access layer
Candidates: a full ORM (SQLAlchemy, Prisma, ActiveRecord), a query builder, raw SQL + a thin
mapper.
Axes: query complexity & need for hand-tuned SQL · migration tooling · type safety · how much the
team wants to think in objects vs. rows · lock-in.

### Frontend approach
Candidates: an SPA framework (React, Vue, Svelte), server-rendered + light JS (HTMX, Turbo),
a meta-framework (Next, Remix, SvelteKit), or none (API only).
Axes: interactivity level actually needed · SEO / first-paint · team skills · build & deploy
complexity · one client or many.

### API style
Defer to `api-interface-style` for anything non-trivial. Quick axes if handling inline: number of
distinct client query shapes · request/response vs. push vs. streaming · public vs. internal ·
latency sensitivity.

### Auth approach
Candidates: session cookies + a server store, stateless JWT, a hosted identity provider
(Auth0/Clerk/Cognito), framework-built-in auth, single-user-from-env.
Axes: number of users & self-serve signup vs. fixed set · who owns credential storage &
rotation · SSO / social login needs · session revocation needs · compliance. Load-bearing →
`access-control-modeling`.

### Background / async work
Candidates: a task queue (Celery, RQ, Sidekiq), a managed queue (SQS + workers), cron, in-process
background tasks, an event stream.
Axes: durability & retry needs · latency (seconds vs. minutes vs. batch) · volume · ops surface ·
does a job need to survive a deploy / crash.

### Packaging & dependency management
Candidates (Python): uv, Poetry, pip + requirements, pip-tools, Conda.
Axes: lockfile & reproducibility · speed · single-tool vs. several · ecosystem norms · CI
integration. Usually **structural or routine** — don't over-walk it.

### Deployment target
Defer to `deployment-strategy` / `serverless-execution-model` for anything non-trivial. Quick
axes: who operates it · scale-to-zero vs. always-on · container vs. function vs. VM vs. PaaS ·
cost model · existing infra.

---

## Anti-patterns

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| **Resume-driven** | The exciting option wins on axes nobody stated | Name the axes in Step 4 first; score against *this* build |
| **False binary** | "React or Django" when they're not even the same layer, or a 2-option field when a third is standard | Fix the candidate set in Step 3 |
| **Analysis paralysis** | Three rounds, no recommendation | Step 6 is mandatory — land one, note the risk, move on |
| **Because-free verdict** | "Go with Postgres." — no axis cited | Tie the recommendation to a named axis + a Step 2 constraint |
| **Flawless winner** | The recommended option loses no axis | Add the missing axis, or state the real cost you skipped |
| **Walking a routine call** | A full loop on the formatter | Step 3 depth control — name it, one line, batch it |
| **Interviewer register leak** | Claude hands the user a shortlist "to react to" while claiming to quiz them | Ask "what are you considering, and why?" — no leading list |
