# Endpoint guards: every route declares who may call it (applies to every project, 2026-10-31)

Found on iron-log (route review 2026-10-31): the server was guarded well, but only because of middleware order in one file. Nothing
failed if a route was added above the sign-in line, nothing listed which route needs which role, and feature commands were flat lines
in one `app.ts`. Guards that live only in reading order get lost. This rule makes them declared, listed and tested.

## The rules

1. **Default deny.** One sign-in gate sits before every route; a route is public only by a named allowlist entry with a reason
   (health probe, webhook with its own signature check, error reports). Register public routes first, the gate next, everything else after.
2. **Every endpoint has a row** in the project's guard matrix (`ARCHITECTURE.md`): method and path, guard (`public`, `session`, `admin`,
   `paid`, `token`), rate limit and key (IP or user), body limit, cache header, and the feature that owns it. A new endpoint is not done without its row.
3. **One feature, one route module, one prefix.** A feature mounts its routes at its own `/api/<feature>` prefix from its own folder, and
   declares its guard once at the mount (`app.use('/api/issues', requireAdmin, limit, issuesRoutes)`), not per handler. The main app file
   is a registry: mounts only, no logic. Commands of one feature share one router (and a prefix when their guard differs from the rest). Split the code, keep the URLs: phones hold writes queued for the old paths, so a URL changes only when the feature needs a different guard, and the old path keeps working for a window. Move existing flat routes as a pure move
   (`pure-move-refactors.md`), one feature per PR.
4. **Roles are checked on the server, twice where it matters.** The UI hides a feature; the route guard (`requireAdmin`, `requirePaid`)
   refuses it; for admin and money data the database checks again (row-level security, a function that re-reads `is_admin`). A hidden
   screen or a typed address is never the control (`screen-addresses.md`).
5. **Authenticated answers are `Cache-Control: private, no-store`** by default (set before the sign-in gate so a 401 is not cached
   either); a route that is safe to cache for a short time sets its own `private` header after it.
6. **Limits before cost.** Per-address limit before sign-in, per-user limit after; body size judged before parsing, small by default and larger only on the one route that needs it, after sign-in.
7. **Machine callers** (webhooks, schedulers) are public routes with their own proof (signature, signed token), their own rate limit, and no session. Never an admin route in disguise.
8. **Unknown paths** under `/api` answer a JSON 404 and need a session first, so the API's shape cannot be probed.
9. **Cross-site writes** are refused (origin check plus SameSite cookies) before any body is read.

## Enforcer: the route-inventory test

A test (iron-log: `server/routeGuards.test.ts`) that:
- lists every route the app registers and fails unless it is on the `PUBLIC` allowlist (with a reason) or answers 401 with no session;
- fails on a stale `PUBLIC` entry;
- probes every mounted prefix and an unknown `/api` path for 401 with each method;
- checks one account without the role gets 403 (admin) or 402 (paid) on each guarded prefix;
- checks the no-store header.

A mounted router cannot be listed from the app, so the prefix list in the test is kept by hand; a new feature adds its prefix there
(advisory until a prefix is missed twice, then derive it from the feature registry).

## Where it applies

- New project: Stage 0 of `new-project-order.md` includes the default-deny gate and this test from the first endpoint.
- New endpoint or feature: the brief's Done when has a line for guard, limits and matrix row (`feature-delivery.md` question bank).
- Existing project without it: run the route review (iron-log's is the model: list every route, its guard, where the gate sits), then one brief.
- Audits: `audit-codebase` and `security-audit` report routes missing from the matrix or the test.

Related: `definition-of-done.md` (API route row), `screen-addresses.md`, `dependency-security.md`, skill `access-control-modeling`.
