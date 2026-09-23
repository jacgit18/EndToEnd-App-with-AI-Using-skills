# Walk a feature through the stack, layer by layer

A recall card for interviews and live conversations. Skim it, don't read it out.

## The one question

> **At each layer, what is the decision, and would it be expensive to change later?**

Use the same test as in [delegation-decision-density.md](delegation-decision-density.md): a column name is cheap to change, a relationship other tables depend on is not. Say which is which as you go.

## The walk (in order)

| # | Layer | Say out loud |
|---|---|---|
| 1 | **Data** | Tables and columns to add. Relationships (foreign keys, many-to-many). What's nullable vs. required. Which choices are cheap to reverse and which are load-bearing. Indexing and migration only if they probe on scale. |
| 2 | **Business logic** | The functional flow: classes, functions, where data is derived from existing objects. Where the result lives (database or cache) and why: read frequency, how stale it can be, cost of recomputing. |
| 3 | **API** | The contract. What the endpoint accepts, what it returns, how errors are shaped, what's validated at the boundary. |
| 4 | **UI** | What state it tracks, how loading and error show up, what triggers a re-fetch or re-render. |

**Caching gets its own sentence**, not just a mention under storage: what's cached, how it's invalidated, and the TTL reasoning. Cache invalidation is a common probe.

## Cross-cutting (say it once, apply it at every layer)

Don't force these into the sequence. Name them as "here's how I'd handle this at every layer."

- **Auth.** Who may do this, where it's enforced (the API boundary is standard), what happens on failure. Expect this question for anything that touches user data.
- **Errors and edge cases.** What if the DB write fails, the cache is stale, the request is malformed?
- **Testing.** Unit tests on the logic, integration tests on the API contract, and what you'd trust instead of test.
- **Observability.** Logs and metrics, and how you'd know it's working or breaking in production. Often skipped, and often the difference between a junior and a senior answer.
- **Scale.** What changes as data or request volume grows. This is where the caching answer gets revisited.

Naming the split between the walk and the cross-cutting layers out loud is itself a sign of structured thinking.

## Questions to say out loud

1. What would it cost to undo this in six months?
2. Where does this data live, and what happens when that copy is stale?
3. Who is allowed to do this, and at which layer do I enforce it?
4. What happens at this layer when the layer below fails?
5. How would I know in production that this feature is broken?
6. What changes at 10x the data or traffic?

## 20-second interview version

"I walk it in order: data, logic, API, UI, saying at each layer which choices are cheap to change and which are load-bearing. Caching gets its own mention, with what's cached, how it's invalidated and why. Then I name the cross-cutting parts once, auth, error handling, testing, observability and scale, and say how each shows up at every layer."
