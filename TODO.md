# TODO

Carried over from `.claude/handoffs/handoff-skill-catalog-wrapup-2026-10-03.md`. Update this file as items close.

## Finance dashboard

- [ ] **Phase 7 close-out, owner steps.** Code and docs are done on branch `finance/phase7-closeout` (see `finance-dashboard/ACCESSIBILITY.md`). What is left:
  - [ ] Fill in the per-figure table in `finance-dashboard/docs/phase7-verification.md` from one real month (needs the real login).
  - [ ] Deploy the `Caddyfile.prod` fixes (compression, asset caching). Needs a fresh "deploy to prod" in the session.
  - [ ] Audit the other routes (`/`, `/accounts`, `/categories`, `/budgets`, `/import`) with Lighthouse and axe.
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
