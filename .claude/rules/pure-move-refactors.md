# Pure-move refactors (applies to every project)

Splitting a large file (a store, a global stylesheet) went well as a series of pure moves.

- One slice per PR, branched off fresh `main`; no stacked PRs.
- A pure move changes no logic: the moved code is byte-for-byte the same, only imports and exports change. Say it in the PR and show the check (diff of the moved block, or computed styles before and after).
- Name the protected paths (for example board reorder and log write paths) and move them last, with their tests untouched and green.
- Add a guard that keeps the result from drifting back (a lint rule rejecting raw values, a size or line-count check, a test).
- Update the structure map in `ARCHITECTURE.md` in the same PR.

Enforcer: the guard each refactor adds (lint rule, size check or test); the rest is advisory.
