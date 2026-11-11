# UI preview mock-ups: show the change before building it (applies to every project, 2026-11-01)

The owner liked the Loadbearer wide-screen preview page (a private Artifact with Before and After per change, a width switch, option toggles and an "All combined" click-through) and wants it for UI work from now on. It caught a bad idea cheaply before any code (a tile for "Start from last month", a feature that does not exist) and let the owner pick between layouts instead of describing them. Mock-ups cost minutes; a built-and-reverted layout costs a branch, a review and a Lighthouse run.

## When to make one

- Any UI change that moves, adds, removes or restyles more than one element: a new screen or tab, a layout change, a redesigned panel, a new empty state, a design-language change, anything with more than one reasonable arrangement.
- Not for a one-file fix, a copy change, a colour-token fix or a bug with an obvious fix.
- When the owner says "let me see a preview", "what would it look like" or "propose options": always.

## What it is

One self-contained HTML page published with the Artifact tool (private by default; the link is the deliverable), built from the project's own colours, fonts, card style and spacing, so it reads as the real app. Contents:

1. **One tab per change**, numbered the same as in the chat or the plan, each with a short note: what changes, effort, files touched, risk, hands-off areas not touched.
2. **Before / After / Both** per change. Before is a real screenshot-faithful rendering of today, After is the proposal.
3. **A width switch** for the sizes that matter to the change (desktop 1920x1080 and 2560x1440, then 1280, 768, 375 as needed) and an "Actual size" toggle.
4. **Option toggles** where the owner has to choose (layout 1, 2 or 3; button placement A, B or C; panel style new or current), with one line saying what each option means and a recommendation in the chat.
5. **An "All combined" view**: a clickable mini-app (header tabs, section buttons) with every accepted change applied, so the whole effect is judged together, not one panel at a time.
6. **Example data, labelled** as example. Never present invented numbers as the user's.
7. A list of what is **not** mocked and why (needs real data, needs a device).

Make it theme-aware like any Artifact (the page chrome follows the viewer; the mock shows the app's own light theme like a screenshot unless the change is about themes, then add a theme switch).

## How, in order

1. **Look at the real thing first.** Screenshots of the affected screens at the target widths, in light and dark. A mock built from memory drifts: on 2026-11-01 the mock showed a dark header band floating at 2560, which is true only in the light theme (dark theme: transparent header), and the build session briefly concluded there was nothing to widen. State which theme and width the Before is.
2. **Check every action and label exists.** A tile, button or menu in the mock must trigger something that already exists, or be marked "new, needs building". Read the code; do not invent features in a mock.
3. **Respect hands-off lists** (project `CLAUDE.md`): draw those areas as unchanged placeholders and say so.
4. **Build, run once, publish.** Test the script against a stub DOM or one browser pass for errors, then publish; republish to the same URL as the owner's picks come in so the link stays.
5. **Owner picks in chat**; the choices go into the feature's brief (`feature-delivery.md`, decisions made, option marked) and the brief links the preview. The mock is not the spec: the brief and the Done when list are.
6. **Keep a copy** in the project docs (`Projects/<project>/ux/previews/<date>-<topic>.html`) and list it in `PriorityRead.md` if it is still the reference; archive it when the work ships.
7. **Keep the preview until the owner has seen it.** Never delete, unpublish or overwrite a preview page, a temporary preview route or its screenshots before the owner says in chat that they have looked at it; give the link first, then wait. Cleanup is its own step with the owner's yes (2026-11-11: a landing preview was removed unseen during the billing go-live and had to be rebuilt).

## Evidence

A mock is `read-only` evidence at best (nothing ran in the real app). After building, the real screenshots at the same widths replace it in the PR (`evidence-labels.md`, `definition-of-done.md` UI row).

## Enforcer

Advisory. The check is the brief's Ready gate: a UI change over one screen names its approved preview link or says `Preview: n/a: <why>`. Add a PR-template line if it is skipped twice (`rule-enforcers.md`).

Example: the Loadbearer wide-screen preview (copy in the project docs `ux/previews/2026-11-01-wide-previews.html`). Related: `feature-delivery.md`, `desktop-layout-width.md`, `web-accessibility-and-lighthouse.md`, `screen-addresses.md`.
