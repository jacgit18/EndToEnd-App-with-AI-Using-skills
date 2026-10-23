# Rules index

One line per rule file: what it decides and what enforces it. Read the file when you touch that area; the hard rules are in `CLAUDE.md`.

| Rule | Decides | Enforcer |
|---|---|---|
| `adding-a-skill.md` | steps to add or change a skill | `lint.sh --strict`, `/new-skill` |
| `agents.md` | which unattended agents exist | advisory |
| `commands.md` | git scripts, lint, smoke tests | the scripts |
| `conventions.md` | branches, commits, staging, docs location, prod deploys | `commit.sh`, permissions |
| `definition-of-done.md` | project DoD and per-feature Done when | PR template Done section |
| `dependency-security.md` | no install without approval; vetting; CI scans; repo prerequisites | `permissions.ask`, `dependency-scan.yml` |
| `dependency-selection.md` | library or build ladder | advisory (PR package delta) |
| `document-toc.md` | `## Contents` in long docs | `doc-toc.sh` hook, `doc-toc.mjs --check` |
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

Each rule is kept in two places: here and `~/.claude/rules/`. After editing one, run `diff -r .claude/rules ~/.claude/rules` and copy the change across.
