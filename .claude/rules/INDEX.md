# Rules index

One line per rule file: what it decides and what enforces it. Read the file when you touch that area; the hard rules are in `CLAUDE.md`.

| Rule | Decides | Enforcer |
|---|---|---|
| `adding-a-skill.md` | steps to add or change a skill | `lint.sh --strict`, `/new-skill` |
| `agents.md` | which unattended agents exist | advisory |
| `ci-budget.md` | CI job timeouts, per-project CI budget, no silent pipeline growth, test pruning by proposal | `scripts/ci-timeouts.mjs` (PR kit), PR template line |
| `new-project-claude-md-template.md` | lean CLAUDE.md template for a new project | advisory |
| `new-project-order.md` | Day-1 checklist for a new project, guardrails added at triggers, features stop when a trigger fires; lean CLAUDE.md template | advisory (stage table) |
| `pr-review-bot.md` | Automatic PR review on open; model picked by risk (Opus for risky paths or big diffs, Sonnet otherwise, never Haiku) | `reviewModel.test.js`, `claude-review.yml` (PR kit); secret and `review` settings advisory |
| `branch-naming.md` | branch is `<letter>-<slug>`, letter = PR label | `guard-pr-create.sh` hook |
| `commands.md` | git scripts, lint, smoke tests | the scripts |
| `conventions.md` | branches, commits, staging, docs location, prod deploys | `commit.sh`, permissions |
| `desktop-layout-width.md` | page container capped at 1920 px, desktop checked at 1920 and 2560 | advisory |
| `definition-of-done.md` | project DoD and per-feature Done when | PR template Done section |
| `dependency-security.md` | no install without approval; vetting; CI scans; repo prerequisites | `permissions.ask`, `dependency-scan.yml` |
| `dependency-selection.md` | library or build ladder | advisory (PR package delta) |
| `document-toc.md` | `## Contents` in long docs | `doc-toc.sh` hook, `doc-toc.mjs --check` |
| `ui-preview-mockups.md` | publish a private Artifact preview before a multi-element UI change | advisory (brief Ready gate) |
| `vault-properties.md` | vault docs start with an intact properties block (line 1 `---`, required keys, YAML-safe values) | `doc-toc.sh` hook runs `fm-check.mjs` (exit 2) |
| `screen-addresses.md` | every screen has an address; Back and reload work; the address is not security | route test and navigation spec (iron-log), else advisory |
| `endpoint-guards.md` | every route declares its guard; default-deny gate; route module per feature; route-inventory test | route-inventory test (iron-log), else advisory |
| `evidence-labels.md` | verified, read-only, agent-reported, not run | advisory |
| `feature-delivery.md` | one brief, one branch, one PR | advisory (PR template lines) |
| `feature-planning.md` | plan once; cost, debt, tiers | advisory |
| `git-actions.md` | which model for which git work | `permissions.ask` |
| `merge-safe-files.md` | conflict-prone files | `.gitattributes` |
| `parallel-agent-structure.md` | structure for parallel agents; serial or parallel by file overlap | advisory |
| `production-access.md` | read-only production, owner runs commands | advisory |
| `pure-move-refactors.md` | file splits as pure moves | the guard each refactor adds |
| `repo-map.md` | what is tracked in this checkout | advisory |
| `rule-enforcers.md` | every rule names an enforcer; new guards tested for false positives | advisory |
| `session-git-hygiene.md` | one worktree per session; no stray commits | `permissions.ask` |
| `skill-architecture.md` | skill file shape, slash-only skills | `lint.sh` |
| `test-run-protocol.md` | reading test failures under load | advisory |
| `web-accessibility-and-lighthouse.md` | WCAG target, Lighthouse floors | `scripts/lighthouse.mjs --check` |

Each rule is kept in two places: here and `~/.claude/rules/`. After editing one, copy it across and run `scripts/rules/sync-check.sh` (exits 1 on a differing copy or a rule with no row here; covered by `scripts/tests/test_rules.sh`).
