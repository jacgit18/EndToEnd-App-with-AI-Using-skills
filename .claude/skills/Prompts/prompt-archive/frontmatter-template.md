# Prompt file frontmatter

The convention used by files already in `.claude/_Prompts/` (e.g. `Linux Terminal.md`,
`Database/DataBase Prompts.md`). Match it when archiving a new prompt.

```markdown
---
tags:
  - prompt
  - AI
author:
  - jacgit18
Comments:
Purpose:
Status:
Started:
EditDate:
Relates:
dg-publish: false
---
<prompt body, verbatim>
```

## Field notes

| Field | Value |
|---|---|
| `tags` | Always `prompt` and `AI`. Add topic tags when obvious (`databases`, `query`, `ChatGpt`, `writing`, `finance`). |
| `author` | `jacgit18`. Add `chatgpt` or `claude` as a second list item only if a model authored the prompt. |
| `Comments` | Free-text note about the doc. Leave blank if nothing to say. |
| `Purpose` | One sentence: what the prompt is for. Required. |
| `Status` | `Draft` (just captured), `Refinement` (being worked on), `Final` / `Done` (settled). Default `Draft`. |
| `Started` | Usually left blank. |
| `EditDate` | Today, `YYYY-MM-DD`. |
| `Relates` | Link to a related note if there is one, else blank. |
| `dg-publish` | `false`. |

Do not invent values for blank fields — leave them empty.
