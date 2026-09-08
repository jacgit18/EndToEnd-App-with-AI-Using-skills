---
name: skill-usage-log
description: Reports on which skills have actually been invoked in this project, from the automatic skill-usage log. Every `Skill` tool call is captured by the PreToolUse hook in .claude/settings.json (scripts/hooks/log-skill.sh), which appends a timestamped line to .claude/_Prompts/logs/YYYY-MM-DD-skills.md. Use this skill when the user asks "which skills have I used", "skill usage log / report", "how often do I use <skill>", "what skills got used today / this week", "which skills have never fired", "is the skill logging working", or wants usage tallied over a date range or per session. NOT for logging or archiving prompts (that is `prompt-archive`, which owns the sibling YYYY-MM-DD.md prompt logs), NOT for checking the README/catalog is consistent with the skills tree (that is `sync-catalog` / `catalog-drift-audit`), NOT for testing whether a new skill collides with its siblings (that is `skill-interaction-testing`), and NOT for summarizing session state for a handoff (that is `session-handoff`).
---

# Skill Usage Log

Answers "what skills are getting used here, and how much" from a log that is written automatically. This skill only **reads and summarizes** — capture happens in the hook.

Paths are relative to the project root (the repo containing `.claude/`).

---

## The automatic capture

`.claude/settings.json` wires `scripts/hooks/log-skill.sh` as a `PreToolUse` hook with matcher `Skill`. On every skill invocation it appends one line to `.claude/_Prompts/logs/<date>-skills.md`:

```
# Skill usage log — 2026-09-08

- 14:22:07  `code-review`  (session a1b2c3d4)  args: high --fix
- 14:31:55  `dataviz`  (session a1b2c3d4)
```

One dated file per day, alongside the prompt logs (`<date>.md`) that `log-prompt.sh` writes. The hook is defensive: needs `jq`, prints nothing, always exits 0, never blocks the tool call. It only records skills invoked through the `Skill` tool in this project — not slash commands that don't resolve to a skill, and not skills used in other repos.

- To pause it: remove the `PreToolUse` block in `.claude/settings.json`.
- `logs/` can get large and may be gitignored locally — same tradeoff as the prompt logs. Mention it once; don't decide it for the user.

---

## Mode: check the logging is working

Use when the user asks whether skill tracking is active.

1. Confirm the wiring: `PreToolUse` block with matcher `Skill` in `.claude/settings.json`, and `scripts/hooks/log-skill.sh` exists and is executable.
2. Confirm `jq` is on `PATH` (the hook is a silent no-op without it).
3. Smoke-test without waiting for a real invocation:
   ```bash
   printf '%s' '{"session_id":"testtest","tool_name":"Skill","tool_input":{"skill":"demo","args":"x"}}' \
     | ./scripts/hooks/log-skill.sh && tail -n 2 ".claude/_Prompts/logs/$(date +%Y-%m-%d)-skills.md"
   ```
   Then delete the `demo` test line so it doesn't pollute the tally.
4. Report: wired / not wired, and the newest real entry's date so the user knows capture is live.

---

## Mode: usage report

Use for any "which / how often / when" question about skill usage.

1. **Scope it.** Default to all `*-skills.md` files. Honor an explicit window ("today", "this week", "since 2026-09-01") by selecting files by date in the filename.
2. **Read the logs.** `cat .claude/_Prompts/logs/*-skills.md` (or the date-filtered subset). If none exist, say so — either nothing has been invoked yet or the hook isn't wired (check with the mode above).
3. **Tally.** Parse the `` `skill-name` `` token from each `- ` line. See `report-recipes.md` for copy-paste shell one-liners. Produce whatever the question needs:
   - total invocations and distinct skills over the window
   - count per skill, descending — the ranked table is the usual answer
   - per-day or per-session breakdown when asked
   - first-seen / last-seen date per skill for a "when" question
4. **Never-used, when asked.** Cross-reference the tally against the skills tree: `find ".claude/skills" -mindepth 2 -maxdepth 2 -type d` gives every catalogued skill as `<Group>/<name>`; the log records bare `<name>`. List catalogued skills with zero recorded invocations. Caveat the result: the log only goes back to when the hook was added, so "never used" means "not since logging started".
5. **Report** as a short markdown table plus a one-line takeaway (most-used, and anything conspicuously unused). Don't paste raw log lines unless the user asks for the detail.
