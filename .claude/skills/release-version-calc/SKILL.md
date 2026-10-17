---
name: release-version-calc
description: Picks the next release version of an app or library from the diff since the last tag (not commit prefixes), classifies changes against a declared public surface, applies SemVer (0.x rule, pre-release stage, base from last GA), syncs manifests. Use for "what version is this", "bump the version", "cut a release". NOT one change's breakage (`change-surface-audit`), rollout (`deployment-strategy`), commits (`commit-and-push`).
---

# Release version calculation

The failure this prevents: a version number picked from the commit messages, from habit
("just bump the patch"), or from whatever the last person typed into a release form. Commit
messages say what the author meant, not what the diff does; a "fix" can drop a column, a
"bump node" can break every self-hoster, and a repo without Conventional Commits gives a
prefix-driven tool (semantic-release, release-please) nothing to read at all. The other
half: the arithmetic is easy to get wrong in ways nobody notices: a breaking change on 0.x
jumping to 1.0.0, a run of breaking pre-releases each bumping the base again, or stage
labels that sort backwards so `alpha.1` counts as *older* than `pre-alpha.3`.

This is a **procedure with one gate**. It withholds the number until the project has a
declared public surface (Step 1); after that it runs straight through and ends in one
version, the evidence for it, and the files to sync. It never pushes a tag or publishes.

## When to use

- "What version should this release be?" / "Is this a major or a minor?"
- "Bump the version" / "Cut a release" / "Tag the next release"
- "We're moving from beta to RC, what's the tag?"
- "package.json says 0.4.0 but the tag is 0.5.0-beta.2, which is right?"
- Before a release workflow that takes a version as input.

## Out of scope: hand these off

- **Whether one specific change is breaking** when the answer isn't obvious from the diff,
  e.g. an enum gaining a value or a default changing: `change-surface-audit`. This skill adds
  up a whole range and turns it into a number; it sends the one unclear change there and
  takes the verdict back.
- **How the new version reaches production** (blue-green, canary, rollback trigger):
  `deployment-strategy`. This skill decides what the version *is*, not how it ships. When
  both fire, settle the version first and pass Step 3's breaking data and config lines on as
  input to its schema-coupling question.
- **Running the retirement of something** with consumers (window, notices, brownouts):
  `deprecation-sunset`. This skill only notes that a deprecation landing is a minor bump and
  the eventual removal is a major one.
- **Committing the version bump, pushing the branch**: `commit-and-push`. **Merge vs squash
  of the release PR**: `history-integration-strategy`.
- **"What is semantic versioning?"** with nothing to version: answer directly, no procedure.

---

## Step 0: Read what's already there

Surface these from the repo. Don't ask the user for them.

- **Tags.** `git tag --merged HEAD`: the highest release tag and the highest **GA** tag
  (no pre-release suffix), and the prefix in use (`v1.2.3`, `web/v1.2.3`). No tags in a CI
  or fresh checkout? Run `git fetch --tags` (shallow clones often have none) before
  concluding there are none. Truly none means a first release: the base is `0.1.0`, and
  Step 3 still runs so the changelog has its first entry.
- **Scheme.** SemVer, CalVer (`2026.10.1`), or none. **CalVer: stop the SemVer path.** The
  next version is the date rule the project already uses; say so and only do Step 5.
- **Stray tags.** List every tag, not just the highest: a mistyped or old-scheme tag (`v1.5.5-alpha` beside `v5.0.0-alpha.10`) skews the base and the next number. Report any that do not fit the ladder and let the user decide; never delete or move a tag yourself.
- **Units.** One versioned unit, or several (a monorepo's web app, API and library). Ask
  whether they version **independently** (separate prefixes, run this per unit with
  `--path` / `--tag-prefix`) or **in lockstep** (one number, highest bump across all).
- **Stage ladder.** The pre-release labels the project uses (from tags, release workflow,
  CONTRIBUTING). Check they **sort in order under SemVer precedence**:
  `next-version.sh check-ladder <labels>`. Labels compare as ASCII, so `pre-alpha` sorts
  after `alpha` and `poc` after `mvp`. A misordered ladder is reported as a finding with a fix
  (rename so labels sort, e.g. write pre-alpha as `alpha.0.N`, since the numeric `0` sorts below
  `alpha.1`; or give pre-alpha its own lower base such as `0.0.N`).
- **Every place the version is written**: manifests, `VERSION`, Helm `Chart.yaml`, a
  health endpoint, an about screen, the changelog. `version-schemes.md` lists where each
  ecosystem keeps it.

## Step 1: The gate: a declared public surface

SemVer means nothing until someone says what counts as the public API. Look for a
declaration (a `## Versioning` section in README / CONTRIBUTING / RELEASING, or the repo's
docs folder). If there is none, **stop and write one with the user**: draft it from what Step
0 and the code show, one line per surface, and ask them to confirm or cut. Don't compute a
version against an undeclared surface. If the user declines to write one, use the table
below as an **assumed** surface and mark the output `Public surface: assumed (not declared)`,
so the number is visibly provisional rather than silently confident. Hurry or "don't
overthink it" counts as declining: use the assumed table and lead with the one change that
moves the number ("removed env var X → breaking → v2.0.0, not v1.6.1"). If the user still
wants their number, give the tag command for it and record the override in the changelog.
Sync the manifests only after they answer, so the files aren't edited twice. A row
the user cuts stays cut; flag it once only if the diff touches it.

| Surface | Breaking looks like |
|---|---|
| HTTP / RPC API, webhooks, events | field removed or renamed, new required input, status or error shape changed |
| Data and migrations | a migration that drops or renames, or that a rollback to the previous version cannot survive |
| Files users import or export | column or field renamed or removed, format changed |
| Config and environment | new required variable, one removed or renamed, changed default with visible effect |
| Runtime and deploy contract | runtime major, container user or ports, OS or arch support dropped |
| CLI | flag or command removed, output that scripts parse changed |
| Library exports (libraries only) | exported symbol removed, signature changed, re-exported dependency's major |
| User-visible features | a feature removed or a workflow forced to change |

**Who consumes it decides how strict to be.** A library with downstream users and an app
with self-hosters treat every row as binding. A single-operator app with one deployment
mostly cares about data and config (can I roll back? do I need to change my env?). Write
that down with the surface, so the next release reads the same rules.

## Step 2: Gather evidence for the range

Range: last release tag `..HEAD` (or `--since` if the user names another point), limited to
the unit's path. Run `scripts/release/next-version.sh --path <unit>` if the repo has it. It
lists migrations with destructive-looking lines, API contract files, deleted source files,
env template keys added and removed, runtime pins, dependency manifests, commit-message
hints and every manifest's version string. Without the script, collect the same with
`git diff --name-status <tag> HEAD -- <path>` plus a read of each group.

Then **read the diff** for each product file the script can't classify by name (route
handlers, serializers, exported modules). Commit messages are hints only; Conventional
Commit prefixes, where they exist, are a cross-check, never the source.

## Step 3: Classify each change

One line per change: surface, `breaking | additive | fix | none`, evidence (file or commit).

- **none**: refactors, tests, CI, docs, dev dependencies, lockfile-only bumps.
- **fix**: behaviour corrected to match what was documented or intended; a dependency bump
  that fixes a shipped vulnerability.
- **additive**: new endpoint, field, flag, optional env var, feature; a deprecation
  *announced* (the thing still works); a forward-only migration that only adds.
- **breaking**: anything in the Step 1 table's right column; removal of something
  deprecated earlier; a "fix" that changes behaviour consumers demonstrably rely on.

A change you can't place from the diff goes to `change-surface-audit`. Name it, hand it off,
and use its compatible/breaking verdict here. Don't guess the hard one to keep moving.
When the user asks whether a named change is breaking, run `change-surface-audit` on it
first even if the table already places it, and give that verdict before or alongside the
Step 1 gate, since it doesn't depend on the declared surface: its compatibility-phase call (keep the old field
alongside the new) can change what ships, and so the number. A removal of something
deprecated: if a deprecation record exists, say whether its exit criteria are met
(`deprecation-sunset`) before numbering it.

## Step 4: Compute the number

1. **Highest wins.** One breaking change makes the release breaking, however many fixes
   ride along. No product change at all means **no release**: say so.
2. **The 0.x rule.** While major is 0: breaking → **minor**, additive or fix → **patch**.
   1.0.0 is never reached by arithmetic. It's the owner's declaration that the public
   surface is stable. Ask before proposing it; don't infer it from "it's in production".
   A version the user names ("this is 2.0") is a floor: take the higher of named and
   computed, and say so when the diff alone wouldn't justify it.
3. **Base from the last GA, not the last pre-release.** If `2.0.0-beta.1` is open and
   another breaking change lands, the next is `2.0.0-beta.2`, not `3.0.0-beta.1`. The base
   moves only when the bump from the last GA exceeds the open pre-release's base.
4. **Stage is the user's call.** Whether this is still beta or ready for RC is a judgment
   about maturity the diff can't show. Ask; never promote a stage on your own. With no
   pre-release open and no stage named, default to GA and say so rather than asking. Same stage:
   iteration + 1. New stage: iteration resets to 1. GA: drop the suffix.
5. **Check it sorts higher** than the last tag under SemVer precedence. If it doesn't, the
   ladder is misordered (Step 0). Stop and report; don't ship a version that sorts lower.

`next-version.sh bump --level <highest> --stage <stage>` does 2–5 and exits non-zero on a
version that doesn't sort higher. Use it when present; check its output against these rules.

## Step 5: Sync, then stop

Update every location from Step 0 to the new number **on a branch**, translated per
ecosystem (Python's PEP 440 has no `-beta.2`; it's `b2`: see `version-schemes.md`), plus
a changelog entry grouped Breaking / Added / Fixed with the Step 3 evidence. Commit through
`commit-and-push`.

**Where the tag goes.** Sync on the release branch before it merges; the tag goes on the
commit that lands on the default branch (the merge, squash or rebased commit), never the release
branch's tip. After a squash the tip isn't on main, so `git tag --merged HEAD` won't find
that tag next time and the next release computes from a stale base.

**Pushing the tag and publishing the release stay with the user.** A tag on a shared remote
triggers release workflows, package publishes and notifications, and can't be cleanly taken
back. Give the exact command with its target commit (`git tag -a v2.0.0-beta.2 <sha on main> -m "…"
&& git push origin v2.0.0-beta.2`, run after the merge), or the workflow's manual inputs, and
stop. If the user said "tag it", say in one line that the tag is theirs to push.

## Output

```
Unit:          <name/path> · scheme SemVer · tag prefix <v> · ladder <labels> <ok | MISORDERED: …>
Range:         <last tag>..HEAD  (<n> commits) · last GA <tag | none>
Public surface: <where declared> · consumers <who>
Changes:       <surface> — <change> — breaking|additive|fix|none — <file/commit>
               …
Handed off:    change-surface-audit <change → verdict> | none
Highest bump:  <major|minor|patch|none> → after 0.x rule: <…>
Stage:         <ga | label> (user's call: <confirmed | asked>)
Next version:  <prefix><X.Y.Z[-stage.n]>   (sorts above <last tag>: yes)
Sync:          <file — old → new, ecosystem form>  …  · CHANGELOG
You run:       <tag + push command, or release-workflow inputs>
```

## Example invocations

> "We're about to release, what version is this?" (repo tagged `v0.3.0`, a migration drops a column)

Applies. Step 0 finds `v0.3.0`, no GA beyond it, SemVer. Step 1 finds a `## Versioning`
section. Step 3 marks the drop-column migration breaking. Step 4: breaking on 0.x → minor →
`v0.4.0`. Sync `package.json` and `pyproject.toml`, write the changelog, hand the user the tag
command.

> "Beta's done, cut the RC." (last tag `v2.0.0-beta.3`, last GA `v1.6.0`, two fixes since)

Applies. Highest bump is patch, which doesn't move the base past `2.0.0`. The user named the
stage, so `v2.0.0-rc.1`, and Step 4.5 confirms `rc` sorts above `beta`.

> "Is renaming this response field a breaking change?"

Does not apply. One change's compatibility → `change-surface-audit`. This skill uses that
verdict when the field's release is being numbered.

> "How do we roll out 2.0 without downtime?"

Does not apply. Rollout → `deployment-strategy`.

## Portability

Needs git with tags. Optionally uses `scripts/release/next-version.sh` (bash + git, read-only;
copy `scripts/release/` into the repo, works with any tag prefix). Writes only the version
bump and changelog entry, on a branch; reads `version-schemes.md` for ecosystem formats.

Depends on: `change-surface-audit`, `commit-and-push`, `deployment-strategy`,
`deprecation-sunset`. If a named sibling isn't installed, say so and give the one-line
answer inline instead of dropping the hand-off; when it is installed under a plugin
namespace, hand off by that name. The load-bearing ones: no `change-surface-audit` → for the
one unclear change, ask "what did a consumer see before, what do they see now, and does any
consumer depend on the old shape?" and classify from the answer, marking it *unaudited* in
the output; no `next-version.sh` → do Step 2 with `git diff --name-status` and Step 4 by hand,
writing out each rule's result on its own line so the arithmetic is checkable; no
`commit-and-push` → stage the synced files by explicit path and commit with a message
listing old → new versions.

## Routing boundaries (full)

- Fires on "what version is this", "what should the next version be", "bump the version",
  "cut a release", "tag a release", "is this a major or minor", "semver for this release",
  "next release number", "move from beta to rc", "version mismatch between package.json and
  the tag".
- NOT `change-surface-audit`: "is this change breaking" or "what could this break" about one
  change. This skill uses its verdicts across a range.
- NOT `deployment-strategy`: how a version rolls out, rollback triggers, release cadence.
- NOT `deprecation-sunset`: running a removal's window and consumer migration.
- NOT `commit-and-push`: committing and pushing; it commits the bump this skill writes.
- NOT `history-integration-strategy`: how the release branch or PR is merged.
- NOT `api-interface-style`: how an API's own versions are exposed (`/v2/` paths, headers, version negotiation). This skill numbers releases, not API version schemes.
