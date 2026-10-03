# TODO

Carried over from `.claude/handoffs/handoff-skill-catalog-wrapup-2026-10-03.md`. Update this file as items close.

## Finance dashboard

- [ ] **Public URL: https://findash.us.ci (named tunnel), 4 of 5 done.** Replaced the quick tunnel that died ("Tunnel not found").
  - [x] Domain `findash.us.ci` (free, DNSHE) on Cloudflare, nameservers Active.
  - [x] Tunnel `findash` with a published route to `http://localhost:8080`, run by the host's systemd `cloudflared` service (PRs #136 merged; #135 closed as superseded).
  - [x] Verified over HTTPS: `/health` ok, gzip + immutable cache, `/api` 401 without a session, owner signed in (2026-10-03).
  - [x] Old quick-tunnel container removed (`up -d --remove-orphans`).
  - [ ] **Reboot check:** after the next reboot, confirm `systemctl is-active cloudflared` is `active`, `docker ps` shows the three `finance-prod-*` containers, and https://findash.us.ci/health answers. Settings are right (cloudflared and docker enabled, containers `unless-stopped`); a real reboot is untested.
  - [ ] Check how the DNSHE domain renews and note the expiry date in `finance-dashboard/docs/paid-options.md`.
- [ ] **Phase 7 close-out, owner steps (3 of 7 done).** Code and docs merged in PR #132 (see `finance-dashboard/ACCESSIBILITY.md`). What is left:
  - [ ] Fill in the per-figure table in `finance-dashboard/docs/phase7-verification.md` from one real month (needs the real login).
  - [x] Deploy the `Caddyfile.prod` fixes (compression, asset caching). Deployed 2026-10-03 (backup `finance-20261003-143923.sql.gz` first). Checked on the local prod stack at 127.0.0.1:8080: `/health` ok, gzip + immutable cache on the bundle, `robots.txt` and meta description served, `/api/budgets` 401 without a session. Public HTTPS URL checked later the same day (see the Public URL item). `app.reconcile` run by the owner 2026-10-03.
  - [x] Audit the other routes with Lighthouse and axe. Done 2026-10-03; results in `ACCESSIBILITY.md`.
  - [x] **Fix what the route audit found.** Done on branch `finance/a11y-route-fixes` (see `ACCESSIBILITY.md`, "Other routes"): all 7 routes 100/100/100/100, axe 0 violations at 1280 and 320px, all controls at least 44px, 98 frontend tests.
  - [ ] **Deploy the route fixes** (frontend rebuild only, no migration). Needs a fresh "deploy to prod": back up with `scripts/backup-db.sh`, then the owner runs `scripts/prod.sh up -d --build`. Then re-run the checks against https://findash.us.ci.
  - [ ] Audit the edit states (account/category edit rows), Import after choosing a file, and error messages with axe.
  - [ ] Work through the "Manual review still required" list in `ACCESSIBILITY.md` (screen readers, zoom, forced colors, target size, reading level), then retest on the deployed HTTPS site.
- [ ] **Phase 8 (CI/CD hardening): ON HOLD until the owner says go.** Spec `finance-dashboard/docs/phase8-spec.md`, ADR-0019 to 0022. Slice 1 is the CI workflow. Build with `incremental-build-pacing`. Free-first; note paid options in `finance-dashboard/docs/paid-options.md`. A prod deploy needs an explicit fresh "deploy to prod".

## Skill candidates (held until Phase 8 is further along)

- [ ] Restore-drill procedure skill.
- [ ] Env-isolation lens on `config-and-secrets-management`.
- [ ] Extend the `deployment-strategy` release checklist.

## Follow-ups

- [ ] **About 2026-10-17:** run `skill-usage-log` and `grep '\[project: '` in the logs to see which global skills are used in other projects. Organically unused so far: `browser-test-tooling`, `deprecation-sunset`, `idea-to-first-test`, `repo-reality-audit`, `web-vitals-audit`. `context-promotion` and `diagnostic-injection` fired only in tests. Exclude test-agent fires (annotated with `# NOTE` in the day's log).
- [ ] Optional: test the rewritten `context-promotion` description properly with non-isolated read-only agents (worktree agents see `main` only), or leave the skill as is. The rewrite is untested and was not shipped.
- [ ] Lighthouse's "Agentic Browsing" category did not appear in Lighthouse 12.8.2 output. Re-check the policy's fractional-pass rule when it does.
