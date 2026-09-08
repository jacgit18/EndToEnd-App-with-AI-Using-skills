# Repo layout — tooling mechanics

Reference for the "if the layout is (or stays) one repo, make it not hurt" step in `SKILL.md`. This is the *how*; `SKILL.md` decides the *whether*.

## Affected-graph / path-scoped CI

The failure mode being fixed: a one-line change to one component runs the entire suite because CI has no notion of "what did this PR actually touch."

**Homogeneous JS/TS workspace** (the common case when frontend + backend share a language and lint/type/build tooling) — reach for a build-graph tool:

| Tool | What it gives you | Adoption cost |
|---|---|---|
| **Nx** | `nx affected` — only builds/tests/lints projects whose dependency graph changed; remote caching; code-gen and project-graph visualization | Low-medium — mostly config, works with existing package managers |
| **Turborepo** | `turbo run test --filter=...[HEAD^]` — same affected-only idea, lighter tool surface, remote caching | Low — minimal config, good default for a JS/TS-only workspace |
| Plain workspaces (`npm`/`pnpm`/`yarn` workspaces) + a script that diffs changed paths | No caching or dependency-graph awareness, just directory filtering | Lowest — no new tool, but doesn't catch "changed a shared package, need to test its consumers" |

Nx and Turborepo both understand the *dependency graph* (a shared package changed → rebuild everyone who imports it), not just "which directory changed." That distinction matters once packages are shared across the frontend/backend boundary; a pure path-filter can't see it.

**Polyglot** (JS + Python + anything else in the same repo) — neither Nx nor Turborepo drives non-JS toolchains natively. Two workable patterns, in order of adoption cost:

1. **Path-filtered CI workflows** — `dorny/paths-filter` (GitHub Actions) or the platform-native equivalent, gating each component's own job on whether its directory changed. No new build system, works with whatever each component already uses, but no cross-language dependency graph — a shared codegen step feeding two services won't trigger both unless you wire that path explicitly.
2. **Bazel** — one build graph across every language, real affected-detection for the whole polyglot tree, remote caching. Real power, real cost: a new build language (BUILD files) for every target, a steeper ramp for a small team, and existing tooling (IDE integration, package-manager-native workflows) often needs Bazel-specific plugins. Reach for this only once the path-filtered approach is demonstrably insufficient — e.g., cross-language dependencies that path filters keep missing — not as a default starting point.

## `CODEOWNERS`

A file (`CODEOWNERS`, at repo root or in `.github/`/`.gitlab/`) mapping paths to owners:

```
apps/frontend/     @frontend-team
apps/backend/      @backend-team
services/*-data/   @data-team
```

This is the mechanical answer to "who owns what" — it auto-requests the right reviewers and, combined with branch-protection rules, can require review from the owning team before a path merges. It only works if the directory layout matches the actual ownership boundaries (the service boundaries from the Readiness Block recommendation) — a `CODEOWNERS` file layered on a tangled directory structure just produces wrong or absent owners.

This is usually the highest-leverage, lowest-cost fix for an "unclear ownership" complaint specifically — often a same-day change, independent of anything else in this file.

## CI cost at scale

Path-scoped/affected CI reduces wasted compute but doesn't eliminate the fixed costs of a large repo: checkout time, artifact storage, remote-cache hosting (Nx Cloud, Turborepo remote cache, or self-hosted equivalents), and self-hosted-runner infrastructure if SaaS CI minutes become the dominant line item. Once that's a real dollar number rather than a guess, it's a `technical-cost-decision` question — this file only flags that it exists.

## Repo split or merge is a migration

Moving code between repos — extracting a service into its own repo, or merging repos back together — means preserving (or deliberately discarding) git history, cutting CI over without a gap, and redirecting every open PR and local clone. That sequencing, not the target-layout decision, is what `migration-cutover` covers. Don't improvise the cutover inline once the target layout is agreed.
