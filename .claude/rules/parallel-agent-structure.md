# Structure for parallel agents (applies to every project)

Goal: a typical change touches a small, predictable set of files, and two unrelated changes never touch the same file. Then several agents (or branches) can work at once without conflicts, and each agent reads less to do its job. Apply this when designing a new project and when adding to an existing one.

## Design rules

1. **Organize by feature, not by file type.** One folder per feature holds its component, hook, styles, types and tests (`features/timer/`), not one `components/`, `hooks/`, `types/` folder each with a piece of every feature.
2. **Name the shared files up front and keep the list short.** These are the collision points: router, root store, global stylesheet, shared types, config, the main entry. List them in the project's `ARCHITECTURE.md`. Everything else should be owned by one feature.
3. **Shared files are registries, not logic.** A feature adds one line to register itself (a route, a slice, an export); the logic lives in the feature folder.
4. **Make shared files append-safe.** One item per line, sorted alphabetically (imports, exports, CSS properties, registry entries, config keys), so two branches editing different lines merge cleanly. New styles go in the feature's own file, not the global one.
5. **Define seams.** Features talk through a small typed interface (an exported function, a store slice, an event), never by reaching into another feature's internals. An agent can then change a feature's insides without knowing who else exists.
6. **Share only what is truly the same concept.** A little duplication across features is cheaper than a shared helper that couples them all. Extract to shared code when a second feature needs the same thing, not before.
7. **Keep files readable whole.** Over about 500 lines usually means two jobs in one file; split it.
8. **Tests live with the feature.** Each feature gets its own unit and e2e spec file. Do not append to one big shared test file.
9. **Lazy-load features** so each is its own chunk; this also keeps the first screen small.
10. **Do not over-build.** Start with feature folders and the rules above; add layers or interfaces only when a real second consumer appears.

## Running agents in parallel

- Give each agent one feature folder (or one task) and say which shared files it may touch.
- Two tasks that both need the same shared file run one after the other, or split that shared file first.
- Use one branch or worktree per agent. Before starting, check open PRs and their changed files (`gh pr list`, `gh pr diff <n> --name-only`); wait for a PR to merge only if it touches a file you also need to change (see "Serial or parallel" below).
- Small commits and PRs off `main`; no stacked PRs.
- Put the structure map (feature folder to purpose, shared file list, import rules) where agents read it first: the project's `ARCHITECTURE.md` and a line in its `CLAUDE.md`.

## Serial or parallel: decide by file overlap

Before you put work in a queue ("wait for that PR", "one at a time"), list the files each task will touch and compare them with the other open PRs and with the other tasks in this request (`gh pr list`, `gh pr diff <n> --name-only`, or the plan).
- **No file in common:** do them in parallel (one branch or worktree each, separate PRs). Do not serialize work only because it is in the same area or the same kind of change.
- **A file in common:** run those tasks one after the other (or split the shared file first), and say which file forced it. A shared registry line or a different, far-apart hunk of the same file still counts as overlap unless the owner says otherwise.
- Say the result in one line before starting: "A touches X, B touches Y: no overlap, doing both" or "A and B both change styles.css: B waits".

## Check it

- Before the first feature: write the feature list, the shared-file list and the import rules into `ARCHITECTURE.md`.
- After a few PRs: run `git log --stat -20`. If most commits touch many files across the tree, or the same shared file keeps showing up, the structure is leaking: fix the seam, not just the change.
- In review: a PR that edits a shared file with logic (not a registry line) needs a reason.

## Worked example

iron-log's `CLAUDE.md` Conventions: per-component CSS files, import placement and alphabetical names, one open PR per store slice or component, a spec file per feature, `feature-map.md`. Its known weak spot is the shared store (`AppState`, slices), the first place parallel work collides.

## Related

Plan the features (and their cost, debt and free/paid tier) before building: see `feature-planning.md` in this folder. Its "shared files touched" field feeds the parallel-work decision above.
