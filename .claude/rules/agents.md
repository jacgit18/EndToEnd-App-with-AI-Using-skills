# Agents

Skills are procedures inside one foreground conversation. Actual unattended-agent infra:

- **`spec-executor`** (`.claude/agents/spec-executor.md`) — subagent that executes exactly
  one slice of an already-approved `spec-drift-gate` spec in an isolated worktree. It does
  not decide scope, does not merge or push; it reports what it did and flags anything that
  fell outside the spec, for a human to run through `spec-drift-gate` Step 4. Only dispatch
  it when a written spec already exists and the slice is big enough to background.
- **Weekly Catalog Drift Audit** — a scheduled cloud routine (not in this repo; lives at
  claude.ai/code/routines). Runs `catalog-drift-audit` against `main`, fixes mechanical
  drift on a branch, opens a PR. Never pushes to `main`. Its audit trail is
  `.claude/_Prompts/catalog-audit-log.md`.

To author a new agent, copy `template/spec-system/agent-spec-template.md` to
`.claude/agents/<name>.md` and fill it in (the template starts with a worthiness test —
fixed-sequence or high-stakes tasks should stay scripts, not agents).
