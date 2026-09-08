# Coverage Metrics

What each metric measures, what it misses, and the reference points behind a target number. Use this in steps 2–3 and 5 of `policy-framework.md` and in "Challenge the framing" in `SKILL.md`.

---

## The four metrics

### Statement coverage
Percentage of executable statements run at least once by the suite.

- **Measures:** which lines the tests reached.
- **Misses:** whether the line did the right thing (no assertion required to count it), and whether *both* sides of a condition ran. `if (x) doA(); else doB();` on one line can show as covered with only `x` true.
- **Use as:** the baseline metric for ordinary code. Cheap, universal, every tool reports it.

### Branch coverage
Percentage of decision outcomes (the true *and* the false of each `if`, each `case`, each `&&`/`||` short-circuit, each `catch`) that executed.

- **Measures:** whether every path through the control flow was taken.
- **Misses:** still no assertion requirement; still blind to combinations of conditions (condition/decision coverage goes further, rarely worth it).
- **Use as:** the metric for decision-heavy, business-critical logic. This is what forces the `else`, the error handler, and the edge-case branch to be exercised — the exact gap `Test Branch Coverage.md` is about. A segment can sit at 100% statement and 60% branch; the missing 40% is untested behavior.

### Function coverage
Percentage of functions/methods invoked at least once.

- **Measures:** whether whole units of code have *any* test touching them.
- **Misses:** almost everything about quality — one call with no assertions counts the function as covered.
- **Use as:** a coarse secondary signal to flag entirely untested modules. Weak alone.

### Line coverage
Like statement coverage but counted per source line; may not distinguish multiple statements on one line.

- **Use as:** interchangeable with statement coverage for policy purposes; report whichever the tool makes primary.

---

## The reference band

From `Code Coverage Best Practices.md`, citing Google's internal guideline — a **starting reference, not a mandate**:

| Coverage | Label |
|---|---|
| 60% | acceptable |
| 75% | commendable |
| 90% | exemplary |

Caveats that travel with the band:

- **No universal ideal.** The right number for a segment is a function of business impact, change frequency, complexity, and lifespan. A product owner with domain knowledge sets it, not a company-wide edict.
- **The gradient matters more than the level.** 30%→70% on an untested area is where the value is. 90%→95% is not — stop optimizing there.
- **Prioritize new code.** Coverage of newly written and frequently-changed code is worth more than the aggregate.
- **High coverage ≠ quality.** 100% is often misleading and wasteful; it breeds a false sense of security and assertion-free tests. Mutation testing is the tool for "are these tests actually any good."
- **Low coverage is a reliable warning.** It *guarantees* large untested areas. The main product of a coverage report is the list of what's **not** covered — feed that into code review and decide, line by line, whether the risk is acceptable.
- **Combine sources.** Unit coverage is one input; integration and system tests cover code too (sometimes incidentally). Merge the data for a real picture.

---

## The three gate bases

When CI enforces coverage, it can gate on:

| Basis | What it enforces | Best for | Failure mode |
|---|---|---|---|
| **Overall** | total repo/module coverage stays above a floor | a mature codebase already above target | a big generated file lifts the average and hides an untested change; punishes whoever inherits a low-coverage module |
| **New-code** | lines added/modified in the PR meet a target | stopping fresh untested code from landing | ignores the existing untested body; needs accurate diff attribution |
| **Delta** | coverage doesn't drop more than a tolerance vs the base branch | catching any regression, incremental ratchet | noisy when the changed line count is tiny; can fire for legitimate reasons (removing a well-tested module) |

Common good policy: **new-code target + a small delta tolerance**, with an overall gate added only once the codebase is comfortably above its target. A flat overall gate on a below-target codebase is the configuration most likely to be gamed.

---

## Guard against the checklist trap

`Code Coverage Best Practices.md` is explicit: gates can degenerate into checklist exercises with "unintended outcomes" — tests written only to move the number, with weak or no assertions. Signs it's happening:

- Coverage rises but defect rate doesn't.
- Tests with many lines exercised and one trivial assertion (`expect(result).toBeDefined()`).
- New tests that never fail.

The countermeasures are cultural and structural, not a higher number: put the *uncovered lines* in front of reviewers, keep the target realistic per segment, and use mutation testing where test quality genuinely matters.
