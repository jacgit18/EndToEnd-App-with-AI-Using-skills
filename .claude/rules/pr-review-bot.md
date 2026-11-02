# Automatic PR review, model by risk (applies to every project, 2026-10-28)

Every project that opens PRs gets an automatic Claude review when a PR is opened or marked ready, and the model is picked from what the PR changes. It arrives with the PR kit (`commit-and-push/pr-kit/install.sh`), which `guard-pr-create.sh` already requires before `gh pr create`, so a new project gets it without a separate step.

## Which model

`scripts/review-model.mjs` (PR kit) reads `git diff --numstat` against the base branch:

| Tier | When | Model | Turns |
|---|---|---|---|
| deep | any risky path (migrations, `.sql`, auth, session, crypto, secrets, billing, payments, webhooks, `.github/workflows/`, Dockerfile, dependency manifests and lock files, `.env*`), over 600 changed lines or over 25 files (lock files not counted) | Opus (`claude-opus-5-5`) | 40 |
| light | only docs, tests and images | Sonnet (`claude-sonnet-5-5`) | 15 |
| standard | everything else | Sonnet | 30 |

- Never Haiku: reviewing a diff for real problems needs Sonnet or Opus (`git-actions.md`).
- Labels override the pick: `review:deep`, `review:standard`. Adding one to an open PR re-runs the review.
- Per project, under `review` in `.github/pr-kit.json`: `highRisk` and `light` (extra regexes, added to the defaults), `deepLines`, `deepFiles`, `models`, `turns`. Name the project's own hot paths there (a store, a sync folder, a payments module).
- The summary comment starts with `Reviewed by <model> (<tier> review)` and the run summary says why.

## Setup per project

1. `install.sh <project-dir>` (writes `.github/workflows/claude-review.yml`, `scripts/review-model.mjs`, its test).
2. Add the `CLAUDE_CODE_OAUTH_TOKEN` repository secret: run `claude setup-token` in your own terminal (never inside a chat, the token would land in the transcript), then `gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner/repo>` and paste at the hidden prompt. It bills the Claude subscription (Max), not API credits, so it needs no API key; delete any old `ANTHROPIC_API_KEY` secret. Without the token every PR gets a "did not run" comment, which is deliberate: a missing review must not look like a passing one. The token lasts a year; revoke it under claude.ai Settings, Claude Code, Authorization tokens (the row with only the `user:inference` scope).
3. Add the project's risky paths to `review` in `.github/pr-kit.json`.
4. Not a required check (a skipped or failed review would block merges: `test-run-protocol.md` rule 8). Budget the job in `CI-BUDGET.md`; it has `timeout-minutes` with a `timeout-ok` reason (`ci-budget.md`).

## Limits, stated plainly

- Reviews draw from the same subscription usage limits as interactive sessions, and Opus uses them faster (expectation, not measured). Watch the first runs and adjust `deepLines`, `deepFiles` and `highRisk` if too many PRs go deep. On iron-log's last 60 merged PRs the defaults gave 24 deep, 28 standard, 8 light (`verified`, picker run over merge history).
- The review sees the diff, `CLAUDE.md` and the repo. It does not see the project docs vault (ADRs, briefs), so a settled decision can be flagged again. A chat review with `/code-review` before opening the PR remains the first review.
- The model IDs are in `review-model.mjs` `DEFAULTS`; update them there when a new model is released.

## Enforcers

- `reviewModel.test.js` (picker rules, including "never Haiku"); the installer's smoke run executes it.
- `ci-timeouts.mjs` covers the workflow's timeout.
- That a project has the workflow at all follows from the PR kit (`guard-pr-create.sh`); the secret and `review` settings are advisory.

Related: `ci-budget.md`, `dependency-security.md` (the action is pinned to a commit SHA), `feature-delivery.md` (one `/code-review` before the PR).
