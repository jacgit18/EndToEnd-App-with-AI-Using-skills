# Report recipes

Shell one-liners for summarizing `.claude/_Prompts/logs/*-skills.md`. Each log line looks like:

```
- 14:22:07  `code-review`  (session a1b2c3d4)  args: high --fix
```

The skill name is the first backtick-quoted token. `LOGS` below is the file set to analyze —
`.claude/_Prompts/logs/*-skills.md` for everything, or a narrower glob for a window
(e.g. `.claude/_Prompts/logs/2026-09-*-skills.md`).

### Extract just the skill names

The hook strips backticks from `args`, so the first (and only) backtick-quoted token on a
`- ` line is always the skill name.

```bash
LOGS=".claude/_Prompts/logs/*-skills.md"
grep -hE '^- ' $LOGS | sed -E 's/^- [^`]*`([^`]+)`.*/\1/'
```

### Count per skill, most-used first

```bash
grep -hoE '`[^`]+`' $LOGS | tr -d '`' | sort | uniq -c | sort -rn
```

### Totals

```bash
# total invocations
grep -hcE '^- .*`[^`]+`' $LOGS | paste -sd+ | bc
# distinct skills
grep -hoE '`[^`]+`' $LOGS | tr -d '`' | sort -u | wc -l
```

### Per-day breakdown

```bash
for f in $LOGS; do
  d=$(basename "$f" -skills.md)
  n=$(grep -cE '^- ' "$f")
  echo "$d  $n"
done
```

### Per-session breakdown

```bash
grep -hoE '\(session [0-9a-z?]+\)' $LOGS | sort | uniq -c | sort -rn
```

### First-seen / last-seen date per skill

```bash
for f in $(ls .claude/_Prompts/logs/*-skills.md | sort); do
  d=$(basename "$f" -skills.md)
  grep -oE '`[^`]+`' "$f" | tr -d '`' | sort -u | sed "s/^/$d /"
done | awk '{ if(!f[$2]) f[$2]=$1; l[$2]=$1 } END { for(s in f) printf "%-32s %s .. %s\n", s, f[s], l[s] }' | sort
```

### Catalogued skills with zero recorded invocations

```bash
comm -23 \
  <(find ".claude/skills" -mindepth 2 -maxdepth 2 -type d -exec basename {} \; | sort -u) \
  <(grep -hoE '`[^`]+`' .claude/_Prompts/logs/*-skills.md | tr -d '`' | sort -u)
```

Caveat every "never used" result: the log only starts when the `PreToolUse` hook was added,
so it means "not invoked since logging began," not "never."
