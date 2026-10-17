# Every rule needs an enforcer (applies to every project)

Rules written only as prose get missed (the PR Audience box, Lighthouse before/after, ux docs). Rules with a mechanical check held (a PR-create hook, a `check` reminder, a measured target-size spec, a token lint rule).

- Each rule in a project's `CLAUDE.md` names its enforcer: a hook, lint rule, test or spec, CI check, or script. If there is none, mark it `advisory`.
- Prefer, in order: a test or lint that fails, a hook that blocks, a script that prints a reminder, prose.
- When a rule is missed twice, add the enforcer instead of rewording the rule.
- A new enforcer ships with a changelog line and lists the rule it guards.
- Keep a short "rule, enforcer" table in `CLAUDE.md` or the project's `ARCHITECTURE.md`.
