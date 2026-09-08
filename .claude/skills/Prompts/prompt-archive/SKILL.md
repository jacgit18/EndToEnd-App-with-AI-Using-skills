---
name: prompt-archive
description: Saves prompts to this vault — either archiving a keeper prompt into the .claude/_Prompts/ library as a properly formatted markdown file, or logging the prompts from the current session to a dated log. Use when the user says "save this prompt", "archive this prompt", "add this to my prompt library", "keep this prompt", "that prompt was good, store it", or wants the session's prompts written to a log / "dump my prompts" / "log the prompts from this chat". Every submitted prompt is ALSO captured automatically by the UserPromptSubmit hook in .claude/settings.json (scripts/hooks/log-prompt.sh) — this skill is the on-demand and curated path on top of that. NOT for evaluating whether a prompt works well (that is prompt-tester), NOT for writing a new prompt from scratch (that is `prompt-authoring`), and NOT for recording a resolved coding bug/problem for a learning-worthiness verdict (that is `problem-journal`, which reads these dated logs as a recurrence-search corpus but writes its own separate file).
---

# Prompt Archive

Two jobs, picked by what the user asked for:

| Ask | Mode |
|---|---|
| "save / archive / keep this prompt", "add to my prompt library" | **Archive** — one curated file in `.claude/_Prompts/` |
| "log / dump the prompts from this session", "write my prompts to a file" | **Log** — append to `.claude/_Prompts/logs/YYYY-MM-DD.md` |

If the ask is ambiguous, ask which one in a single line. Don't do both unless asked.

Paths are relative to the project root (the repo containing `.claude/`).

---

## Mode: Archive a keeper prompt

Use when the user wants a specific prompt kept for reuse.

### 1. Get the prompt text

Use the exact prompt the user points to — a block they pasted, a prompt from earlier in the conversation, or one they name. Do not paraphrase, "improve", or reformat the body. If it's unclear which text they mean, quote back the candidate and confirm.

### 2. Decide category and filename

- **Category** = a subfolder of `.claude/_Prompts/`. Reuse an existing one (`ls .claude/_Prompts/`) when it fits — e.g. `Database/`. Create a new subfolder only for a clearly distinct topic. If nothing fits and the topic is broad, place the file directly in `.claude/_Prompts/`.
- **Filename** = a short Title Case name describing what the prompt does, `.md` extension (e.g. `Schema From Process Flow.md`). Match the spaced-name style already used in the folder.
- Before writing, check whether a file with that name already exists. If it does, ask whether to append a variant under a new `##` heading in that file or create a distinct file.

### 3. Write the file

Frontmatter follows the vault convention (see `frontmatter-template.md`). Fill what you can infer, leave the rest blank — don't invent values:

```markdown
---
tags:
  - prompt
  - AI
author:
  - jacgit18
Comments:
Purpose: <one sentence: what this prompt is for>
Status: Draft
Started:
EditDate: <today's date, YYYY-MM-DD>
Relates:
dg-publish: false
---
<prompt body, verbatim>
```

- `EditDate` — today's date.
- `Status` — `Draft` for a newly captured prompt unless the user says it's finished (`Final` / `Done`).
- `tags` — always include `prompt` and `AI`; add topic tags (e.g. `databases`, `query`) when obvious.
- `author` — `jacgit18`; add `chatgpt` / `claude` as a second author only if the user says a model wrote it.

### 4. Index it

Append a row to `.claude/_Prompts/INDEX.md` (create the file with an `# Prompt Index` heading and a table header if it doesn't exist):

```markdown
| Date | Prompt | Category | Purpose |
|---|---|---|---|
| 2026-09-02 | [Schema From Process Flow](Database/Schema%20From%20Process%20Flow.md) | Database | Turn a described process flow into a DB schema |
```

### 5. Report

One line: the path written and that it was indexed. Don't dump the file contents back.

---

## Mode: Log session prompts

Use when the user wants a record of what they asked during this session (beyond the automatic per-prompt hook — e.g. they want it consolidated, annotated, or the hook wasn't active).

1. Collect the user's prompts from this conversation, in order, verbatim. Skip tool noise and your own messages.
2. Append to `.claude/_Prompts/logs/<today>.md` (same file the hook uses). Create it with a `# Prompt log — <date>` heading if absent. Don't rewrite entries the hook already logged today unless the user asks for a clean consolidated version — in that case write a new file `.claude/_Prompts/logs/<today>-session.md` instead of clobbering.
3. Format each entry:
   ```markdown
   ## <HH:MM or sequence #>

   <prompt text>
   ```
4. Report the path and how many prompts were written.

---

## The automatic hook

`.claude/settings.json` wires `scripts/hooks/log-prompt.sh` to `UserPromptSubmit`, so every prompt submitted in this project is appended to `.claude/_Prompts/logs/YYYY-MM-DD.md` with a timestamp and short session id. The script prints nothing and always exits 0, so it never blocks a prompt or adds context.

- To pause it: remove or comment the `UserPromptSubmit` block in `.claude/settings.json`.
- The `logs/` folder can get large. If the user doesn't want logs in git, add `/.claude/_Prompts/logs/` to `.gitignore` — mention this once, don't decide it for them.
