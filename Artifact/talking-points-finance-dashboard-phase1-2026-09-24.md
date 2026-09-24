# Talking points — finance dashboard, Phase 1 (auth + free deploy) and the skill work around it

_Built from the repo and this session's history. Drafts only: nothing here has been posted. Every claim below traces to the Evidence Block._

## Evidence Block

| What was built | When it shipped | Mechanism (technical) | What it's worth (business) | Outcome | Source |
|---|---|---|---|---|---|
| Single-owner login for the dashboard: login, logout, session refresh, UI | 2026-09-22 to 2026-09-24 | Server-side session row plus a signed HttpOnly cookie; a CSRF token derived from the session id and sent as a header on writes; an in-memory sliding-window limiter on login (10 attempts / 15 min per IP); every login failure returns the same 401 | Only the owner can read or change the financial data, and a stolen page or a password-guessing script gets little | Number: 22 backend and 11 frontend tests passing (re-run 2026-09-24). Named risks addressed: cross-site request forgery, password guessing | PRs #57, #60, #61; commits 5e3867f, f3674d7, 5f6c3f0, a044973 |
| A $0 deployment path | 2026-09-24 | Docker Compose stack (Postgres, FastAPI, Caddy serving the built React app) exposed by a Cloudflare quick tunnel; nightly `pg_dump` script with rotation; a doc listing what was and wasn't verified | The app can be reached over HTTPS with no server bill, and the paid alternatives are written down for when it matters | Number: $0 recurring, against ~$5-7/mo plus ~$12/yr in the original decision record. Verified live: `/health` reported the database connected through a real tunnel | PR #63; `finance-dashboard/docs/deploy.md` |
| A bug found only by watching the logs | 2026-09-24 | `--forwarded-allow-ips='*'` written inside `sh -c "..."` kept its quotes as literal characters, so the server trusted no proxy and logged the proxy's address for every request. Fixed with the `FORWARDED_ALLOW_IPS` environment variable | Without the fix the rate limiter would have counted all visitors as one client | Named risk: a login limiter keyed on the wrong IP. Every request had returned 200 | PR #63; comment in `compose.prod.yaml` |
| Error tracking with privacy-tight defaults | 2026-09-24 | Sentry enabled only when a DSN is set; no request bodies, no personal data, no performance tracing, because bodies carry transaction descriptions and amounts | A production exception is no longer lost in logs, and the financial content stays on the machine | Design property, verified once: a test error I raised on purpose showed up in the Sentry dashboard. Not measured in real use | PR #64; `backend/app/main.py`; your confirmation in session |
| A cost ledger and a startup check | 2026-09-24 | `docs/paid-options.md` lists every place a cost could appear with the free choice and the paid one; startup now refuses to boot on a malformed password hash | Cost decisions are visible before they bite; a config typo fails at boot instead of on every login | Named risks: silent spend; a 500 on every login after a bad copy-paste | PR #64 |
| Three catalog skill updates | 2026-09-24 | Cost-cap check in the tech-decision skill (from a decision record that said "$0 cap" and picked a paid server); "verify by observed effect" in the build-pacing skill; a sensitive-data field in the observability skill | The mistakes above become checks the assistant runs, not things I remember | Number: 3 skills edited, 3 agent test runs of about 14 scenarios, all passed; one real rule conflict found in testing and fixed before merge. Design property, not yet measured in real use | PRs #65, #66 |
| **The set as a whole** | 2026-09-10 to 2026-09-24 | 15 decision records (2026-09-10), a walking skeleton (2026-09-13), then Phase 1 in ten pull requests (#57-#66) | A small app built slowly enough to explain every file, with the decisions and costs on paper | Number: 33 automated tests, 15 decision records, 62 skills in the catalog | git log; `docs/architecture/decisions/` |

**Not verified (say these before someone asks):** a browser sign-in through the public tunnel; the backup restore drill; any long-running behaviour; there is no CI. The skill tests were simulated scenarios, not live sessions. One repair from 2026-09-24 (a shared `.env` file let the prod password leak into the dev stack; now split into `.env.prod` plus a wrapper script) is in the working tree, not yet merged.

## Plain-language summary

I'm building a personal finance dashboard slowly, on purpose, so I can explain every file in it. This month I finished the login system and got it running on the internet for no monthly cost. Along the way I caught a mistake that every automated check had passed, by reading the server's own log. I turned that lesson, and two others, into checks my AI assistant now runs before it calls a step done.

## Conversation script

**Opener.** I'm building a finance app one small piece at a time so I understand all of it. This month I got the login secure and running online for free.

**Their question, your read.** "Do you work on the technical side or the business side of this?"

**If they go technical.** The interesting part was the rate limiter. It counts login attempts per client IP, which means the server has to trust the proxy's forwarded-IP header. I set the allow-list to a star inside a shell string, the quotes stayed literal, and the server trusted nothing. Every request returned 200. The only tell was the log showing the proxy's address for everyone, so all visitors shared one bucket. I moved it to an environment variable and made "state what you observed" a rule in my build skill.

**If they stay non-technical.** The app has a lock on the front door that slows down anyone guessing passwords. It looked fine on every check, but it was treating all visitors as one person. I only saw it by reading the server's own record of who was visiting.

**Follow-up line.** Wrote up the login bug I found last week: everything reported success while the rate limiter quietly counted every visitor as the same person. Happy to share the fix.

## LinkedIn draft

Every request returned 200. The login rate limiter was still broken.

I was deploying a small personal finance app behind a proxy. The limiter counts attempts per client IP, so the server has to trust the proxy's forwarded-IP header. I set the allow-list to a star inside a shell string. The quotes stayed as literal characters, the server trusted nothing, and it logged the proxy's address for every visitor. One bucket for everyone. Health checks, login and cookies all looked green.

I only caught it by reading which IP the server logged. The fix was an environment variable instead of a command-line flag.

That is now a rule in the build skill I use with Claude: every step ends with what I observed, not which status code came back.

Shipped in September 2026: session login, CSRF protection, rate limiting, 33 automated tests, and a $0 deploy on a Cloudflare tunnel.

Caveats: single-user app, no CI yet, no backup restore drill yet, and the skill change was tested on simulated scenarios, not live use.

## Other angles (each is backed by a row above)

- The cost-cap mismatch: a decision record said "$0 budget" and picked a paid server; a check now catches that. (Skill update row.)
- Sentry on a finance app: the default settings would have shipped transaction amounts off the machine. (Error tracking row.)
- Keeping a paid-options ledger: every free choice next to its paid alternative. (Cost ledger row.)
- The env-file collision: a file named `.env` is read by every Compose stack in the folder. (Not merged yet; post after it lands.)
