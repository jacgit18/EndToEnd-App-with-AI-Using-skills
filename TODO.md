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
- [ ] **Phase 7 close-out, owner steps (5 of 8 done).** Code and docs merged in PR #132 (see `.claude/records/finance-dashboard-accessibility.md`). What is left:
  - [ ] Fill in the per-figure table in `finance-dashboard/docs/phase7-verification.md` from one real month (needs the real login).
  - [x] Deploy the `Caddyfile.prod` fixes (compression, asset caching). Deployed 2026-10-03 (backup `finance-20261003-143923.sql.gz` first). Checked on the local prod stack at 127.0.0.1:8080: `/health` ok, gzip + immutable cache on the bundle, `robots.txt` and meta description served, `/api/budgets` 401 without a session. Public HTTPS URL checked later the same day (see the Public URL item). `app.reconcile` run by the owner 2026-10-03.
  - [x] Audit the other routes with Lighthouse and axe. Done 2026-10-03; results in the accessibility record.
  - [x] **Fix what the route audit found.** Done on branch `finance/a11y-route-fixes` (see the accessibility record, "Other routes"): all 7 routes 100/100/100/100, axe 0 violations at 1280 and 320px, all controls at least 44px, 98 frontend tests.
  - [x] Deploy the route fixes (2026-10-03, backup `finance-20261003-173630.sql.gz` first; verified live on https://findash.us.ci).
  - [ ] **Deploy the second pass** (keyboard focus ring and chart colours, both in `index.html`; no migration). Needs a fresh "deploy to prod": backup with `scripts/backup-db.sh`, then the owner runs `scripts/prod.sh up -d --build`. Then re-run the scripted checks against https://findash.us.ci.
  - [x] Audit the edit states, Import after choosing a file, and error messages with axe. Done: 0 violations in every state. It also turned up two real defects, fixed in the same pass: chart text invisible on dark/forced colors, and no keyboard focus ring on date/month inputs (see the record).
  - [ ] **Manual review, what only a person can do** (the record has the full list; zoom, 44px, reduced motion, third-party, 200% text and forced-colors emulation are done by script): a screen reader pass (NVDA/Firefox, VoiceOver/Safari), real Windows High Contrast, a by-hand keyboard pass, and a decision on plain-language supplements for "Void", "Net", "Kind", "Archive" and similar. Then retest on the deployed HTTPS site.
- [ ] **Phase 8 (CI/CD hardening): ON HOLD until the owner says go.** Spec `finance-dashboard/docs/phase8-spec.md`, ADR-0019 to 0022. Slice 1 is the CI workflow. Build with `incremental-build-pacing`. Free-first; note paid options in `finance-dashboard/docs/paid-options.md`. A prod deploy needs an explicit fresh "deploy to prod".

- [x] Web-accessibility lessons from Phase 7 folded into `web-vitals-audit` (`measurement.md`, last section) and a "Build to these from the first commit" list in `.claude/rules/web-accessibility-and-lighthouse.md`. Read-based and lint only; no isolation or interaction test run.

## Skill candidates (held until Phase 8 is further along)

- [ ] Restore-drill procedure skill.
- [ ] Env-isolation lens on `config-and-secrets-management`.
- [ ] Extend the `deployment-strategy` release checklist.

## Follow-ups

- [ ] **About 2026-10-17:** run `skill-usage-log` and `grep '\[project: '` in the logs to see which global skills are used in other projects. Organically unused so far: `browser-test-tooling`, `deprecation-sunset`, `idea-to-first-test`, `repo-reality-audit`, `web-vitals-audit`. `context-promotion` and `diagnostic-injection` fired only in tests. Exclude test-agent fires (annotated with `# NOTE` in the day's log).
- [ ] Optional: test the rewritten `context-promotion` description properly with non-isolated read-only agents (worktree agents see `main` only), or leave the skill as is. The rewrite is untested and was not shipped.
- [ ] Lighthouse's "Agentic Browsing" category did not appear in Lighthouse 12.8.2 output. Re-check the policy's fractional-pass rule when it does.
