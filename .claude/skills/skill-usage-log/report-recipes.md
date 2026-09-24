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

### Fires followed by an override phrase (feedback signal)

For each skill fire, take the user's next prompt in the same session (joined on the 8-char
session id in `<date>-skills.md` and `<date>.md`) and test it against override phrases. Run from
the project root. A skill fire with no later prompt in its session is omitted.

```bash
OVR='just tell me|just do it|skip (the|this)|no,? i meant|ignore (the|that)|don.t (ask|gate)|stop asking|not what i (asked|meant)|why (are|did) you (ask|use)|wrong skill'
for sf in .claude/_Prompts/logs/*-skills.md; do
  d=$(basename "$sf" -skills.md); pf=".claude/_Prompts/logs/$d.md"
  [ -f "$pf" ] || continue
  awk -v D="$d" -v OVR="$OVR" '
    FNR==NR { if ($0 ~ /^## [0-9:]+  ·  session /) { t=$2; s=$NF; n++; T[n]=t; S[n]=s; B[n]="" } else if (n) B[n]=B[n] " " $0; next }
    /^- [0-9:]+  `/ { t=$2; sk=$3; gsub(/`/,"",sk); s=$4 " " $5; gsub(/[()]/,"",s); sub(/^session /,"",s)
      for (i=1;i<=n;i++) if (S[i]==s && T[i]>t) { fire[sk]++; if (tolower(B[i]) ~ OVR) { ovr[sk]++; ex[sk]=substr(B[i],1,90) } ; break } }
    END { for (k in fire) printf "%s  %-28s follow-ups=%d overrides=%d  %s\n", D, k, fire[k], ovr[k]+0, ex[k] }
  ' "$pf" "$sf"
done | sort
```

Read it as a signal, not a verdict: two skills firing before one follow-up both get the credit
or blame, and the phrase list is a heuristic — tune `OVR` as real overrides turn up. It needs
the prompt log for the same date, so a day with a skills log but no `<date>.md` (hook not
running) yields nothing for that day.
