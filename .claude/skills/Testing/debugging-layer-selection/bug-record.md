# Bug record (Step 0 template)

Fill this in before triage picks a layer. Anyone with zero prior context should be able to
reproduce the bug from it, or see exactly why they can't. Over-capture: if unsure whether a
detail matters, record it — a detail that turns out irrelevant costs nothing, a lost one can
cost the diagnosis.

- **Repro steps** — minimal, ordered actions/inputs that trigger it. If not consistently
  reproducible, say so and record what differed between the times it did and didn't happen.
- **Expected** — what should have happened, concretely.
- **Actual** — what happened instead, concretely. "It's wrong" is not a statement.
- **Verbatim error output** — full message, stack trace, status code, or log line, pasted
  exactly. Never paraphrase or trim a stack trace: the exception type and line numbers
  often carry the diagnosis.
- **Environment / context** — language, framework, dependency versions, config, data
  state, and where it ran (local / staging / prod).
- **Timing and frequency** — when it started, how often it recurs, any tie to a trigger
  (load, a particular input, a recent deploy or change).
- **Already ruled out** — hypotheses tested and eliminated, so diagnosis doesn't re-tread
  them. Record only what was actually tested, not hunches.

## Not reliably reproducible

This is the case the record matters most for. Record every occurrence you have (time,
input, environment, outcome) and diff the failing runs against the passing ones. State the
observed rate ("3 of ~20 runs"). If you can't reproduce it at all, the record's job is to
say precisely what was tried, so the next person knows what has been ruled out. Don't guess
a trigger to fill the gap.

## Done test

Hand the record to someone who has never seen the bug. If they'd need a follow-up question
to reproduce it, it isn't done.
