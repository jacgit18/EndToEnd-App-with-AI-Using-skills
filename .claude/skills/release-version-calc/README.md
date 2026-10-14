# release-version-calc skill

A procedure for one decision: **the next release version** of an app, service or library.
It reads the diff since the last release tag rather than trusting commit prefixes,
classifies each change against a public surface the project has declared, and applies
SemVer with the parts that usually go wrong written out: the 0.x rule, pre-release
iteration and stage promotion, the base computed from the last GA rather than the last
pre-release, and a check that stage labels actually sort in order. It ends with one number,
the evidence, and every file to sync. The user pushes the tag.

One gate: it won't compute a version until the public surface is declared (Step 1).

## Where it sits

```
change-surface-audit       →  is ONE change compatible or breaking?            (feeds Step 3 for unclear changes)
release-version-calc       →  what is the next version for this RANGE?         (this skill; chat block + version bump on a branch)
commit-and-push            →  commits the bump this skill writes
deployment-strategy        →  how that version rolls out to production
deprecation-sunset         →  runs a removal's window; its announcement is a minor, its removal a major here
scripts/release/next-version.sh  →  evidence + arithmetic (read-only); notes.sh renders release notes
```

The boundary that most needs stating: **`change-surface-audit` vs this skill.** That one
walks six blast-radius surfaces for a single proposed change. This one adds up a range of
already-made changes and maps the worst of them to a number. It calls the other for the one
change it can't classify from the diff, and never re-runs the six-surface walk itself.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point: read tags/scheme/units/ladder, the public-surface gate, evidence, classification, the arithmetic rules, sync-then-stop, output block. |
| `version-schemes.md` | Where each ecosystem stores the version and how a SemVer pre-release is spelled there (PEP 440, RubyGems, Go `/v2`, mobile build numbers, Helm's two numbers). |
| `scripts/release/next-version.sh` (repo) | `evidence` (default), `bump`, `check-ladder`. Read-only; any tag prefix. Tests in `scripts/tests/test_release.sh`. |

## What it produces

A chat block (unit, range, surface, per-change classification, highest bump, stage, next
version, sync list, the command the user runs), plus, on a branch, the version strings
updated and a changelog entry. No tag, no push, no publish.

## Packaging

General, not tied to one project. Ships in the personal-core symlink set (`plugins/README.md`), so it's available in every project; `scripts/release/next-version.sh` is copied into a repo that wants the script.
