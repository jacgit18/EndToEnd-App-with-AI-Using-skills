# Case Categories

The checklist Claude probes from in Think-together mode, after the user has named their own cases. Probe one or two categories per turn, and only ones that could apply. Every category below is a question, not a quota.

## Unhappy-path and edge categories

| Category | Ask about |
|---|---|
| **Invalid / missing / malformed input** | Wrong type or shape, missing required field, extra fields, wrong encoding, injection-shaped strings, empty vs whitespace |
| **Boundaries** | Empty, one, max, one over max, off-by-one at limits, zero and negative where numbers are allowed |
| **Auth & permissions** | Unauthenticated, wrong role, expired credential, another tenant's resource, permission revoked mid-flow |
| **Dependency failure** | Dependency down, slow, times out, returns an error status, returns 200 with an error body; retry behavior and whether a retry is safe |
| **Partial failure & rollback** | Fails halfway through a multi-step operation; what is left behind; is the operation idempotent on retry |
| **Concurrency & ordering** | Two callers at once, duplicate submission, out-of-order events, race between read and write |
| **State** | Already exists, already deleted, stale version, called twice, called before its precondition |
| **Volume & performance** | Large payload, many items, slow query at scale, rate limits — only if a limit or budget was actually stated |
| **Config & environment** | Missing env var, different region/timezone/locale, feature flag on vs off, prod-vs-staging difference |

For infrastructure (Terraform module, pipeline, migration), read "input" as variables/parameters, "dependency" as the provider, cloud API, or upstream stage, and "state" as existing resources, drift, and lock state.

## Flagging hidden assumptions on happy paths

A happy path is not free of assumptions. Common ones to name:

- The dependency is available and fast.
- Input is already validated upstream.
- Only one writer touches this record.
- The clock, timezone, and locale are what the developer's machine has.
- The resource being created does not already exist.

If the user's happy path relies on one, either add it to the Setup column as `assumes: …` or turn it into an unhappy case.

## Sources of an expected result

| Source | Meaning | What to do |
|---|---|---|
| `spec` | A written requirement or ticket says so | Cite it |
| `user` | The user stated it in this conversation | Repeat it back once to confirm |
| `code (as written — confirm intended)` | Read from implementation | Ask whether the behavior is intended before it becomes an assertion |
| `open` | Nobody has said | Ask; do not fill in |

## Worked table — password reset endpoint

Subject: `POST /password-reset` takes an email, sends a single-use reset link valid for 30 minutes. Spec says: unknown emails get the same response as known ones; links are single-use; rate limit is 5 requests per hour per email.

| Case | Type | Setup | Action | Expected result | Source | Level (suggestion) | Priority |
|---|---|---|---|---|---|---|---|
| Known email gets link | happy | account exists | POST valid email | 202, email sent with link | spec | integration | high |
| Unknown email, same response | unhappy | no such account | POST unknown email | 202, identical body and timing class, no email | spec | integration | high |
| Link used twice | unhappy | link already consumed | open link again | rejected | spec | integration | high |
| Link at 30 min boundary | edge | link issued at t0 | open at t0+30:00 | **open — is 30:00 inclusive?** | open | unit | medium |
| Sixth request in an hour | unhappy | 5 requests done | POST again | rejected with rate-limit response | spec | integration | medium |
| Email provider times out | unhappy | provider stub delays | POST valid email | **open — does the user see success or an error, and is the token still valid?** | open | integration | high |
| Malformed email string | unhappy | none | POST `"not-an-email"` | 400 | user | unit | low |
| Two simultaneous requests same email | unhappy | account exists | two parallel POSTs | **open — one link or two? does the first stay valid?** | open | integration | medium |

Assumptions: the mail provider is reachable in the happy path; the clock is server time in UTC.
Open questions: the three `open` rows.
Left out: password-strength rules on the new password (belongs to a different endpoint's cases); load testing (no throughput target was stated).
