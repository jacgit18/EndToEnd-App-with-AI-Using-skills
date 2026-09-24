# Problem Journal — Journal-mode output formats

The chat output block and the `problems-log.md` entry template used by Journal mode. `Finance/Error Log/` below means that folder or its fallback, per the "Error-log directory" note in `SKILL.md`.

### Output block

```
Problem:              <symptom + root cause + fix, one or two sentences>
Source:               <this session | Finance/Error Log/<file> | user-stated (old session)>
Recurrence check:     <N hits — split by corpus: Finance/Error Log/ vs. prompt-archive logs>
                      — grepped for: <term(s) searched>
Classification:       <recurring pattern | one-off> · <fundamental concept | environmental
                      fluke> · <delegated fully | attempted first | unknown>
Worth learning?:       yes/no — <the one driving reason, tied to the count/classification>
Entry written:         .claude/_Prompts/problems-log.md
Closing the loop:     <Finance/Error Log/<file> Status updated to Resolved | no Capture file
                      existed for this one>
Next step:            <none | learning-gate (teach the minimum) | problem-solving-gates
                      Knowledge Checker (verify after self-study)>
```

### Writing the entry

Append to `.claude/_Prompts/problems-log.md` (create it with a `# Problem Journal` heading
if absent):

```markdown
## 2026-09-05 — <short problem title>

**Problem:** <symptom + root cause + fix>
**Recurrence:** <N hits — corpus breakdown, or "first occurrence">
**Classification:** <recurring/one-off> · <fundamental/environmental>
**Worth learning:** <yes/no> — <reason>
**Next step:** <as in the output block, or "none">
**Error Log file:** <Finance/Error Log/<file>, if one exists — or "none captured">
```
