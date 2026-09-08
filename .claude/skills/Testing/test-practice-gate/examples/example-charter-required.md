# Example: charter required, then satisfied

**Context:** I'm working through a personal project to get sharper at testing. I have a `parseDuration("1h30m")` helper that returns milliseconds, and I want tests for it.

**Precondition check:** Have I stated what the tests are for? No — I just asked Claude to "write tests for parseDuration."

**Me:** "Write tests for this `parseDuration` function."

**Claude:** "Before I write these — four things, in your words:
1. What must `parseDuration` always guarantee? What does 'wrong' look like?
2. Where does it realistically break — units out of order, missing units, whitespace, huge values, a bare number, negative?
3. It doesn't touch anything external as far as I can see — agree there's no seam to decide?
4. What's the set of cases that would make you call this done?"

**Me:** "Okay:
1. A valid string always returns a non-negative integer of milliseconds; an invalid string throws a `RangeError`, never returns `NaN` or a partial value.
2. Break points I care about: `30m1h` (out of order), `1h30` (trailing number, no unit), `''`, `'1h 30m'` (internal space), `'0m'`, and something absurd like `'999999h'` for overflow.
3. No seam, agreed.
4. Done when each of those six break points has a test, plus `1h`, `1h30m`, and `45s` as happy cases, plus one asserting the `RangeError` type specifically."

**Claude:** "That's a complete charter. One gap-check: you've got `'1h30'` (trailing number) — do you also want `'h30m'` (leading unit with no number)? Same failure class, might be worth pinning. Otherwise I'll write exactly the nine you listed, named for the behavior each protects."

**Me:** "Add `'h30m'`, yes."

**Outcome:** Claude wrote ten tests — `throws RangeError on units out of order`, `throws RangeError on trailing number without unit`, `returns 0 for a zero-valued unit`, `throws RangeError on overflow`, etc. — each mapped to something I'd decided mattered. I made every call about what to assert; Claude turned my list into code and caught one sibling case by asking. The `'h30m'` test failed first run — the parser returned `1800000` instead of throwing. That was a real bug I owned finding, because I owned the charter.
