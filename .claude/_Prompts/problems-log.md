# Problem Journal

## 2026-09-27 — Nav/header tab row overflows on narrow viewports

**Problem:** Nav/header tab row overflowed past its container's background on narrow
viewports — the container box didn't grow with unwrapped flex children, so overflowing items
rendered on whatever was behind the header instead of on it (hard to spot in desktop dev
tools, only showed up at real mobile widths). Root causes: no flex-wrap/overflow constraint on
the nav list, and a stale CSS selector (e.g. `nav a`) left over after nav items became
`<button>`s. Fixed with a hamburger menu that expands a full vertical list on narrow
viewports — most discoverable of the three candidates (vs. wrap-to-multi-row, which pushes
content below the fold, and horizontal scroll, which is undiscoverable without a visible
affordance).
**Recurrence:** First occurrence — single-corpus check (no `Finance/Error Log/` in this repo,
and its fallback `.claude/_Prompts/problem-journal/` doesn't exist yet). Grepped
`.claude/_Prompts/logs/*.md` for "flex-wrap", "nav overflow", "header overflow", "hamburger",
"responsive nav" — the only hit was this session's own prompt.
**Classification:** one-off · fundamental concept (CSS box-model + flex-wrap behavior at real
viewport widths, not an environmental fluke)
**Worth learning:** no — first occurrence, no established pattern yet. Worth re-checking if a
second, unrelated responsive-overflow bug shows up: the recurring gap would likely be "verify
computed layout at real mobile widths, not a resized desktop browser," not this specific nav.
**Next step:** none
**Error Log file:** none captured
