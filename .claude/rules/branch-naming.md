# Branch naming (applies to every project)

A branch is named `<letter>-<slug>`. The letter is the PR's label, so the branch, the label and the changelog agree and `scripts/pr-body.mjs` can label the PR from the name.

| Letter | Label | Use for | Example |
|---|---|---|---|
| `f-` | `enhancement` | a feature or any user-visible change | `f-rest-day-timer` |
| `b-` | `bug` | a fix | `b-second-rest-day` |
| `d-` | `documentation` | docs only (README, ADRs, vault docs, comments) | `d-readme` |
| `c-` | `chore` | tests, scripts, CI, config, refactors: nothing a user sees | `c-ci-shard-e2e` |
| `p-` | `dependencies` | package bumps and advisories (a person's branch; Dependabot keeps `dependabot/...`) | `p-zod-advisory` |

Other labels (`accessibility`, `duplicate`, `question`, ...) are not branch types. An accessibility fix is `b-` or `f-`, with the label added to the PR.

## Slug

- Lowercase letters, digits and single hyphens; two to five words; under 40 characters in all.
- Say what the change is, not the date, a ticket number alone, or the tool (`f-card-menu`, not `f-claude-changes-3`).
- One branch, one PR, one letter. A change that mixes types takes the letter of the main one (`feature-delivery.md`).

## Exempt

- `main`, `master`, `release/*`, `dependabot/*`, and names the harness makes (`claude/*`, `worktree-*`). Rename a harness branch before its first push when you can (`git branch -m b-second-rest-day`).
- Branches that already exist: do not rename them. The rule starts with the next branch you create.

## How it applies

- Creating a branch: propose a name from the change in this form and say why.
- `git-routine` and the `commit-and-push` skill use it for the branch guard.
- `scripts/pr-body.mjs` reads the letter to pick the PR label (`--type` overrides it).
- Enforcer: `~/.claude/hooks/guard-pr-create.sh` blocks `gh pr create` from a branch outside this form (opt out for one command with `BRANCH_NAME_SKIP=1`).
