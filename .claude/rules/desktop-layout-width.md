# Desktop layout width: fit the common 1080p screen (applies to every web project, 2026-11-01)

Found on iron-log: the page container stopped at 1500 px. On a 1920x1080 screen, the most common desktop resolution, that left about 210 px of empty margin per side (measured at a 2200 px window: 1500 px of app, 343 px per side), and on a 2560 px monitor about 530 px per side. The 1500 px figure had been chosen for laptops and nobody had checked it against the common desktop. The owner moved the cap to 1920 px.

## The rules

1. **One page container, capped at 1920 px, centered.** `max-width: 1920px; margin: 0 auto;` on the outermost page wrapper, with the side padding the project already uses (iron-log: 16 px). 1920 px is the common desktop width, so a 1080p screen fills edge to edge, and larger monitors stay capped and centered instead of stretching. Define the value once (a token such as `--page-max`, or one rule) and never repeat it.
2. **Same container width on every screen and tab.** Do not give one tab a wider or narrower container: the header and tab bar would jump sideways when a person switches tabs.
3. **Readable limits go inside the content, not on the container.** Running text stays at about 60 to 70 characters, forms and editors at a fixed width (iron-log: 760 px), and a single-column list whose rows sprawl gets its own cap in that component's own stylesheet. Board, table, dashboard and chart screens use the full width.
4. **A cap below 1920 px needs a reason written next to it** (for example, a text-only site where line length matters more than fill). Never pick the cap from your own laptop.
5. **Test the desktop at 1920x1080 and 2560x1440, plus 1280, 768 and 375 px.** Emulate the viewport; do not dock DevTools to the side of the window, because a side-docked panel shrinks the page (iron-log 2026-11-01: a 1920 px screen reported a 1334 px viewport). The container should equal the viewport minus the side padding and about 15 px for a scrollbar.
6. **Measure, do not eyeball.** One console line gives the facts: `({ viewport: innerWidth, screen: screen.width, scale: devicePixelRatio, wrap: Math.round(document.querySelector('.wrap').getBoundingClientRect().width) })`. A scale other than 1 or a viewport narrower than the screen explains most "it does not fill my screen" reports.
7. **A width change is a layout change for the widest screens only.** Below the old cap nothing moves, so the proof is a before and after at the widths on either side of it (iron-log: 1500 and 1920 px), plus the project's own hands-off areas compared with computed styles.

## Where it applies

- New project, Stage 0 (`new-project-order.md`): the page container with the 1920 px cap and the side padding, as one rule.
- Definition of done, UI row (`definition-of-done.md`): "seen in a browser at phone and desktop width" means a 1920x1080 viewport, not a laptop window.
- Existing project: measure its container at 1920 and 2560 px (rule 6); if the cap is under 1920 px with no reason beside it, raise it as one small PR with the proof in rule 7.

## Enforcer

Advisory. Add a layout spec that asserts the container width at 1920 and 2560 px viewports when the cap is missed twice (`rule-enforcers.md`). iron-log's example change: the container cap in `src/styles.css`, `e2e/layout.spec.js` for the Board.

Related: `web-accessibility-and-lighthouse.md`, `new-project-order.md`, `definition-of-done.md`.
