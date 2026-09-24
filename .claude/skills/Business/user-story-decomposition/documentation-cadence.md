# User Story Decomposition — documentation cadence

Read when the stories will be documented as they ship. Contains the split lens (from "Writing the stories") and the Documentation-candidate flag (an optional pass after Definition of Ready).

### Splitting for a documentation cadence (optional lens)

When the epic's stories are going to be documented and shared as they ship — a build log, a
LinkedIn series, months of dated posts instead of one dump — apply one more test on top of the
checks above: **does this story stand alone as one tellable unit** (a stated problem, what got
built, a real before/after), or is it really a sub-step of a bigger reveal that won't make sense
told by itself?

A story can pass the sprint-sized checks above and still fail this one. "Build the CSV import
pipeline" might be a single valid sprint-sized story and still the wrong unit to document — split
it at the seams a reader would actually care about (upload + column mapping · dedupe logic ·
categorization) so each piece ships, closes, and earns its own dated writeup, instead of one
feature landing as a single post that reads like a status update.

This is a tiebreaker, not a new scope-in rule. A story still has to pass the drop/defer checks
above and the **Cohesive** quality-bar row below — don't carve a cohesive story into artificially
small pieces just to manufacture more posts.

---

## Marking a story documentable (optional pass)

Not every story is worth a public writeup, and settling that for good belongs to whoever closes
the story, not to this skill at authoring time — the honest signal (was there a real
before/after, did anything notable happen building it) only exists once the work is actually
done. What this skill can do now is flag the candidates, so "was this worth posting" doesn't
have to be reconstructed from memory three sprints later:

- **Likely worth it**: a load-bearing decision got made, a real before/after exists (a number, a
  broken thing now working, a manual process now automated), or the story stands alone as one
  tellable unit (the documentation-cadence lens above).
- **Probably not**: pure plumbing, a one-line config change, a story whose only content is "did
  what the ticket said" with nothing a reader outside the team would want to read.

Record it as one line: `Documentation candidate: y/n — <reason>`. That is a prediction, not a
commitment — re-confirm it when the story closes.

**Do not hand off to `explaining-my-work` from here.** That skill's whole basis is that every
claim traces to something that already happened; a story still in the backlog has nothing to
trace yet. The hand-off happens later, when the story is actually closed, and whoever closes it
should record the real completion date at that point — a post is only honestly dated if
something wrote down when the work actually finished, not when someone got around to drafting
about it.
