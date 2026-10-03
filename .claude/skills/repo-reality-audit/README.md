# repo-reality-audit skill

A read-only procedure (not a gate) that runs two checks against a whole codebase, once, as it
stands right now: do the repo's own docs and ADRs still match its code, and does the build/test
suite actually run clean when executed. It never fixes anything and never judges design
quality — it only checks whether the repo's *current claims about itself* are true.

## Why this exists, not a broader "codebase audit" skill

Built after a manual six-dimension audit of a real full-stack repo (structure, dependency/config
hygiene, test posture, error handling, security surface, operability). Most findings mapped
cleanly onto existing specialists once pointed at the right file — `security-review`,
`observability-strategy`, `test-strategy`, `code-review` would each catch their own dimension
just as well. A broad catch-all audit skill would mostly re-derive that work, which the
catalog already avoids (see the "prefer a lens over a catch-all skill" convention).

Two findings from that audit needed something no existing skill does: an ADR committing to a
CI pipeline and linter that don't exist anywhere in the repo, and a test suite that hangs
ambiguously instead of failing fast when its precondition (a dev database) isn't met — both
required actually reading a decision doc *and* executing commands against the current tree,
not reasoning about a diff or a design. This skill is scoped to exactly that narrow slice.

## Where it sits

```
repo-reality-audit          →  do the repo's docs/ADRs/CI claims still hold, does it build/
                                test/run clean right now                    (this skill)
code-review                 →  correctness/quality review of one diff
change-surface-audit        →  blast-radius audit of one proposed change, before it happens
spec-drift-gate             →  checkpoints one tracked, spec-gated build against its own spec
sync-catalog                →  this skill catalog's own consistency only
repo-scanner                →  maps a repo's structure; doesn't execute or judge
security-review             →  security-specific findings this skill hands off to, never redoes
observability-strategy      →  logging/alerting/SLO findings this skill hands off to
test-strategy                →  test-level mix decision; this skill only executes what exists
```

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Step 1 scopes the target, Step 2 runs the doc/ADR-vs-reality drift check, Step 3 runs the actually-build/test/run check, Step 4 reports cited, rated findings with an owning skill named per finding. |
| `claim-patterns.md` | Lookup table of recurring claim shapes (CI/pipeline, named tool, superseded mechanism, test-run, file/path) and the exact command that checks each — kept out of `SKILL.md` so the entry point stays a short procedure. |

## What it produces

A cited, rated findings list (blocker/should-fix/nit) plus a one-line verdict on whether the
repo's story about itself currently holds up. Each finding names the specialist skill that
owns a fix, or says "no owner — drift only, needs a doc update." It never edits anything.

## Deliberately out of scope

- **A broad security/error-handling/structure/observability health check** — those stay with
  `security-review`, `code-review`, `observability-strategy`. This skill only checks claims
  vs. reality and whether the build/test actually runs; it is not a general codebase quality
  audit, on purpose (see "Why this exists" above).
- **One diff's correctness** → `code-review`.
- **One proposed change's blast radius, before it happens** → `change-surface-audit`.
- **Mid-build spec-drift checkpoints for one tracked, already-spec'd build** →
  `spec-drift-gate`.
- **This skill catalog's own README/backlog consistency** → `sync-catalog`.
- **Mapping a repo's structure without judging it** → `repo-scanner`.
- **Which test levels should exist and how much effort each gets** → `test-strategy`. This
  skill only reports how the *existing* suite behaves when run.

## Dependencies

Needs no repo setup; the docs and test-command assumptions are in `SKILL.md` → Portability.
The siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Not yet packaged as a plugin; `plugins/README.md` describes
how catalog subsets are installed in other projects.

## Interaction with sibling skills

- **vs `ambiguity-gate`** — a bare "audit my codebase" goes there first.
- **vs `code-review` / `change-surface-audit`** — one diff, or one proposed change, is there;
  the whole tree as it stands is here.
- **vs `spec-drift-gate`** — one tracked build against its own spec is there.
- **vs `catalog-drift-audit`** — a skill catalog's own consistency is there.
- **vs `test-strategy`** — whether the suite runs is here; what the suite should contain is there.

Re-check overlap after any trigger-description change here.
