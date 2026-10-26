# Feature brief: question bank

Ask only what the project docs and code do not answer. Group by theme, batch up to 4 per call, recommended default first. Skip a theme that does not apply (no data change: skip Data).

A question added after a miss carries an *(added date, PR: why)* note. Add one whenever you add a question, so a later cleanup can tell a needed question from a stale one, and a run of late additions in one theme shows the bank was missing that area.

## Job and user
- Who uses this, and what do they do today instead?
- In one sentence, what can they do afterward that they cannot now?
- What must not change (existing behavior, hands-off areas)?

## Scope
- Smallest version worth shipping? What is explicitly out?
- What does the next version add (so this one leaves room, not code)?

## Audience and tier
- Everyone, admin only, or paid? (Project default applies unless told otherwise.)
- If paid or capped: the limit, and what a user sees when they hit it.
- Behind a flag, or released straight?

## States and edge decisions
- Empty, first run, loading, error, offline, over the limit, many items, long text, undo or cancel.
- Existing data created before this feature: what shows?
- Two devices, same data: which wins?

## Mechanism limits (read the code first, ask only what it leaves open)
*(added 2026-10-21, #229: a brief assumed limits and screens the mechanism and app did not have.)*
- Does the delivery mechanism (queue, push, job runner, sync, API) allow what the feature needs: how many pending items per user or key, how far ahead, how often, retries and duplicates?
- Photo or camera input: settle `media-capture-pipeline` first (capture, extraction, retention, cap, accuracy) and link its ADR in the brief.
- What runs the code path: a signed-in user, or a background job with no user context (row-level security, a security-definer function, a migration)?
- Does every screen, tab, route or flag the answers name exist as written?
- What stops it if it loops or the user never opens the app again?

## Data
- New tables, columns or stored fields? Who owns them? Export, import and delete-my-data behavior.
- Money, dates, units: format, rounding, time zone.

## UI
- Which screen and component; reuse or new?
- Phone and desktop, light and dark; copy text in the owner's words.
- Accessible name for each control; tap target size.
- Any Board or day-tab area touched (hands off unless told).

## Cost and risk
- Per-use cost and the cap; new dependency, service or vendor (`dependency-selection.md`); each new package needs the owner's yes and a `dep-vet` result (`dependency-security.md`), so ask it here, not mid-build. *(added 2026-10-21, #226: an agent would otherwise add a package mid-build without the owner's yes.)*
- What could go wrong, how it is switched off, the measurement that says remove it.

## Verification
- Which behaviors need a test; which need a real device; what will the owner try by hand?
- Lighthouse floors affected?

## Docs
- Which docs change: feature map, `ux/`, `data/`, ADR, changelog.

## Closing
- Anything the build would otherwise stop to ask? (Last question of the last round.)
