# Merge-safe files (applies to every project)

The same few files cause most conflicts: the changelog, registry files with append-at-end lists, shared e2e specs and tracked generated files (screenshots).

- Changelog-style files: `merge=union` in `.gitattributes`, or one fragment file per PR combined at release.
- Registries (routes, feature flags, exports): one entry per line, sorted alphabetically, so different lines merge cleanly (see `parallel-agent-structure.md`).
- Generated files and images (README screenshots, build output, lockfiles) are not hand-merged: untrack generated binaries, and regenerate a lockfile from the resolved manifest.
- Each test gets its own spec file; do not append to one big shared spec.
- After a conflict, record the file as a hotspot in `ARCHITECTURE.md` and fix the seam if it repeats.

Enforcer: `.gitattributes` for `merge=union`; the rest is advisory until a project adds a lint.
