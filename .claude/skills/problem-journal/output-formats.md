# Problem Journal — Journal-mode output formats

The chat output block and the `problems-log.md` entry template used by Journal mode. `<journal>` (and so `<journal>/errors/`) below is resolved per the "Journal root" note in `SKILL.md`.

### Output block

```
Problem:              <symptom + root cause + fix, one or two sentences>
Source:               <this session | <journal>/errors/<file> | user-stated (old session)>
Recurrence check:     <N hits — split by corpus: <journal>/errors/ vs. prompt-archive logs>
                      — grepped for: <term(s) searched>
Classification:       <recurring pattern | one-off> · <fundamental concept | environmental
                      fluke> · <delegated fully | attempted first | unknown>
Worth learning?:       yes/no — <the one driving reason, tied to the count/classification>
Entry written:         <journal>/problems-log.md
Closing the loop:     <<journal>/errors/<file> Status updated to Resolved | no Capture file
                      existed for this one>
Next step:            <none | learning-gate (teach the minimum) | problem-solving-gates
                      Knowledge Checker (verify after self-study)>
```

### Writing the entry

Append to `<journal>/problems-log.md` (create it with a `# Problem Journal` heading
if absent):

```markdown
## 2026-09-05 — <short problem title>

**Problem:** <symptom + root cause + fix>
**Recurrence:** <N hits — corpus breakdown, or "first occurrence">
**Classification:** <recurring/one-off> · <fundamental/environmental>
**Worth learning:** <yes/no> — <reason>
**Next step:** <as in the output block, or "none">
**Error Log file:** <<journal>/errors/<file>, if one exists — or "none captured">
```
