# Cloud setup kit

Owner-run scripts that create the cloud side of a new project on one stack: **Google Cloud (Cloud Run, Artifact Registry, Secret Manager) and Neon Postgres**. They turn the Fin-Dash first-run walk into one install and a few commands. A project on another stack does not use this kit.

An agent never runs these scripts or any cloud command: the owner runs them in their own terminal. Run every script with `--dry-run` first (it prints the steps and makes no `gcloud`, `neon` or `docker` call).

## Contents

- [Install](#install)
- [Order of use](#order-of-use)
- [What each script does](#what-each-script-does)
- [Names it creates](#names-it-creates)
- [Where the kit stops](#where-the-kit-stops)
- [Safety rules](#safety-rules)
- [Tests](#tests)
- [Evidence: what was run](#evidence-what-was-run)

## Install

```bash
.claude/skills/cloud-setup/cloud-kit/install.sh <project-dir>        # keeps existing files
.claude/skills/cloud-setup/cloud-kit/install.sh <project-dir> --force  # refresh from the kit
```

It copies `scripts/cloud-*.sh`, `scripts/cloud-kit.conf` and `scripts/cloud-kit-test/`, appends `.env.deploy` and `.neon` to `.gitignore` and one rule line to `CLAUDE.md`, and prints what to edit. **The kit repo is the source of truth**: fix the kit first, then refresh a project with `--force` (and re-apply the project's `cloud-kit.conf` values from git). `deploy.sh` is not part of the kit: it carries each project's release logic and reads the same names (below).

Edit `scripts/cloud-kit.conf` (committed, no secrets): `APP_SLUG`, `REPO_NAME`, `DB_ROLE`, `MARK_KEY`, `LOG_NAME`, `REGION`, `NEON_REGION`, `PG_VERSION`, `BUDGET_USD`, `DISPLAY_NAME`, then `KIT_CONFIGURED=yes`. Every value is pattern-checked before use (they end up in SQL and resource names); the shipped template is refused until edited.

## Order of use

1. Manual sign-ins: `gcloud auth login`, `neon auth`, `gh auth login`.
2. `scripts/cloud-new-project.sh --dry-run`, then for real.
3. `scripts/cloud-new-database.sh qa --dry-run`, then for real (repeat with `prod` later).
4. `scripts/cloud-bootstrap.sh qa --dry-run`, then for real (paste from the clipboard into the hidden prompt).
5. `scripts/cloud-verify.sh qa` (the other scripts also run it at their end).
6. `npm ci --ignore-scripts`, then the project's own deploy.

## What each script does

| Script | Does |
|---|---|
| `cloud-new-project.sh` | Creates and activates the `gcloud` configuration `<APP_SLUG>` (stops with `gcloud auth login` if nobody is signed in); creates the project (plain id, else id plus four digits, at most 3 retries); links the **open** billing account (one: use; several: ask; none: stop; never a placeholder); reads back project and billing; only then sets the configuration's project and region and writes `.env.deploy`; asks once before enabling the Budget API, creates the monthly budget (50, 90, 100 percent, one project) and reads it back. Re-run safe: resumes from `.env.deploy`. |
| `cloud-new-database.sh <qa\|prod>` | Creates Neon project `<slug>-<env>` from a temporary folder outside the repo (neon writes `.neon` into its working folder), records `NEON_PROJECT_ID_<ENV>` in `.env.deploy`, checks the direct connection string (postgres prefix, no `-pooler`, length) and puts it on the clipboard through a pipe. No clipboard tool (or `CLOUD_KIT_CLIPBOARD=none`): you paste by hand. |
| `cloud-bootstrap.sh <qa\|prod>` | Eight sections: APIs, image repository, runtime service account, docker registry access, owner URL secret, least-privilege database role and pooled app URL secret, environment mark, per-secret read grant. Then empties the clipboard and runs `cloud-verify.sh`. |
| `cloud-verify.sh <qa\|prod\|project>` | Read-only. `ok` or `FAILED` per line, exits 1 on any failure: project listed, billing enabled, budget scoped to the project, configuration active, four APIs, exactly two secrets per environment, policy on the app-URL secret is exactly the runtime account, runtime account absent from the owner-URL policy, Neon project listed, no `.neon` and no untracked file. |

With Fin-Dash's config, `cloud-bootstrap.sh qa|prod --dry-run` prints byte-for-byte what Fin-Dash's own bootstrap prints (tested against a stored copy of that output).

## Names it creates

Shared with the project's deploy script: service and prefix `<slug>-<env>`, service account `<prefix>-run`, registry `<region>-docker.pkg.dev/<project>/<REPO_NAME>/<slug>`, secrets `<prefix>-owner-database-url` and `<prefix>-app-database-url`, database mark `<MARK_KEY>:<qa|production>`, log name `LOG_NAME`.

## Where the kit stops

Manual, because they are sign-ins, consent or money: `gcloud auth login`, `neon auth`, `gh auth login`; the Neon permission page (choose the project-limited option, not "all projects"); Neon two-factor (the CLI cannot check it; the kit prints a reminder); creating a billing account or accepting billing terms; anything that spends money or widens access (paid plan, organization policy, domain, Google OAuth client). A budget is an alert, not a cap.

## Safety rules

- `--dry-run` on every script; real runs refuse when the active `gcloud` project differs from `.env.deploy` (new-project checks the named configuration instead).
- No secret in argv, output, a file or shell history: hidden prompt, stdin, pipes and environment variables only. The tests plant a sentinel secret and fail if it appears anywhere, and a mutation check proves the test catches a script that echoes it.
- Per-secret grants only; never project-wide.
- Preflight before a real run: tools on `PATH`, Docker server running, a note to run `npm ci --ignore-scripts`, and that the first run pulls `postgres:<PG_VERSION>-alpine` from Docker Hub.

## Tests

```bash
scripts/cloud-kit-test/run.sh
```

`bash -n` on every script, every `--dry-run` with zero fake calls, the Fin-Dash golden diff, config rejection, the active-project guard, each script's failure cases, the sentinel and its mutation, verify's FAILED cases, and `install.sh` twice. Fake `gcloud`, `neon`, `docker`, `xclip` and `gh` log their argv and print canned output; no real cloud, no package. ShellCheck is not used (not installed; installing it needs the owner's yes).

## Evidence: what was run

Labels: `verified` (output seen), `read-only` (read, not run), `not run`.

- Test suite, dry-run golden diff against Fin-Dash's script, installer twice: `verified` (this build).
- Flags taken from the tools' own `--help` text, read at build time (no cloud call): `gcloud billing budgets create` (`--billing-account`, `--display-name`, `--budget-amount`, `--filter-projects`, `--threshold-rule`), `billing projects link|describe`, `billing accounts list --filter=open=true`, `config configurations create|activate`, `billing budgets list`, `secrets get-iam-policy`, and `neon projects create|list`, `neon connection-string`, global `-o json`. The flags are `read-only` evidence only; the commands were never run for real.
- `not run` until the owner starts the next project: a real run of `cloud-new-project.sh` and `cloud-new-database.sh` and a real `cloud-verify.sh`; the exact `gcloud` output shapes the scripts parse (`--format=value(...)` fields such as `budgetFilter.projects`, `billingAccountName`, `properties.core.project`); `neon projects list -o json` shape (the script accepts a bare array or `{projects: [...]}`); `neon projects create` prompts (organization, default) behave as in the first walk.
- Neon two-factor and the Neon permission-page choice: `not run` (manual).
