# skill-static-audit

A read-only, single-skill audit. Given one skill, it walks frontmatter → body structure →
workflow → bundled resources → examples, and returns findings that each cite a line or gap, rated
blocker / should-fix / nit, with a verdict and a fix order. Origin: a user-supplied audit
checklist, adapted to this catalog's conventions (carve-outs, reciprocal pointers, `README.md`
row, `learning-gate` Step 3 row, gate-vs-procedure honesty).

It is a **procedure, not a gate** — it withholds nothing. `learning-gate` can only lower it to a
hint pass when the user is explicitly learning to write skills.

## Where it sits

| Boundary | Skill | Split |
|---|---|---|
| Does a new/changed skill collide with its neighbors? | `skill-interaction-testing` | That one *runs* realistic prompts (stacking, contradiction, silent override, chaining). This one only *reads*. Natural order: audit the text, fix it, then interaction-test. A description edit that widens or narrows scope hands back to interaction testing. |
| Whole-catalog rot (stale markers, missing README rows, dead pointers) | `catalog-drift-audit` | Periodic, mechanical, no target skill. This is on demand, one skill, deep on content. Its "Catalog wiring" step is a per-skill slice of the same ideas; it never writes the audit log. |
| Creating a skill, measuring triggering, description optimization | `anthropic-skills:skill-creator` | It builds and runs evals. This gives a reading-based critique and measures nothing. |
| Applying the fixes | `/new-skill` step 4 | This skill reports; reciprocal sibling edits are applied there or by hand. |
| Which skills actually got invoked / "why doesn't it fire" from usage data | `skill-usage-log` | That reads the invocation log. This reads one skill's text and can flag trigger *risk* only. |
| Learning to write skills (coaching level) | `learning-gate` | Has a Step 3 row pointing here; on explicit learning intent this skill's escape hatch allows a hint pass instead of the full report. |
| Review request that looks like a debug/design gate | `problem-solving-gates` | Its description carves out skill-file review; this is a critique, not a gate. |
| Prompts, not skills | `prompt-authoring`, `prompt-tester` | Different artifact. Both descriptions carry the reverse pointer. |
| Is the skill's *subject matter* correct | (none — domain expert) | Out of scope by design. |

## Files

| File | Role |
|---|---|
| `SKILL.md` | Target-resolution table, six audit sections, calibration + output format, Never list, escape hatch, examples. |

## Design choices

- **Every finding cites text.** The pasted checklist's strongest rule; kept as the deletion test
  for any finding, with "fine" as a valid result.
- **Conditional checks.** Bundled-resource and catalog-wiring checks say "skip and record why"
  when the precondition is absent — this repo's skills mostly have no scripts, and this checkout
  has no README catalog table, so an unconditional check would produce false failures.
- **Reciprocity is checked by reading the sibling**, not assumed — one-directional pointers are
  the most common defect in this catalog.
- **Severity scale** (blocker / should-fix / nit) replaces "priority order" so the verdict is not
  subjective; description/trigger defects rank first.
- **Honest scope line.** "Not checked" is a required part of the report.

## To try it

- "Audit `Skill Development/entry-point-first`" → full section-by-section report.
- "Is this description any good? [paste]" → Step 2 on the paste, limits stated.
- "Does my new skill collide with anything?" → not this; `skill-interaction-testing`.
- "Audit all my skills" → asks which one / offers `catalog-drift-audit`.
