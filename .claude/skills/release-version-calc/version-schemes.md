# Version schemes by ecosystem

Where each ecosystem keeps the version, and how a SemVer pre-release is written there.
`release-version-calc` Step 0 uses the first column to find every place to sync; Step 5 uses
the last to translate. The tag carries the canonical SemVer string; manifests carry the
ecosystem's form of the same version.

| Ecosystem | Where the version lives | `2.0.0-beta.2` written as | Notes |
|---|---|---|---|
| npm / Node | `package.json` `"version"` (and `package-lock.json` top-level, rewritten by `npm version --no-git-tag-version`) | `2.0.0-beta.2` | Full SemVer. `^0.4.0` only accepts 0.4.x, which is why the 0.x rule maps breaking to minor. |
| Python | `pyproject.toml` `[project] version` (or `[tool.poetry] version`, or a dynamic `__version__`) | `2.0.0b2` | PEP 440 only knows `a`, `b`, `rc`, `.dev`, `.post`. Custom stages (`pre-alpha`, `mvp`) have no form: use `.devN` for anything before alpha, or keep the manifest at the last base and let the tag carry the stage. |
| Rust | `Cargo.toml` `[package] version` | `2.0.0-beta.2` | Cargo treats 0.y as the breaking digit, same as the 0.x rule. |
| Go modules | the tag only (`v2.0.0-beta.2`) | `v2.0.0-beta.2` | No manifest version. A major ≥ 2 also changes the module path (`/v2`) in `go.mod` and every import: a breaking bump is a code change here. |
| Java / Maven | `pom.xml` `<version>` | `2.0.0-beta.2` (or `2.0.0-SNAPSHOT` between releases) | Maven's own ordering knows `alpha`, `beta`, `milestone`, `rc`, `snapshot`; arbitrary labels sort as strings. |
| Gradle | `build.gradle(.kts)` `version =` or `gradle.properties` | `2.0.0-beta.2` | Same ordering caveat as Maven. |
| .NET / NuGet | `.csproj` `<Version>` (or `Directory.Build.props`) | `2.0.0-beta.2` | NuGet follows SemVer 2.0 ordering. |
| Ruby | `lib/<gem>/version.rb` `VERSION` | `2.0.0.beta.2` | RubyGems treats any letter segment as pre-release; uses dots, not a hyphen. |
| PHP / Composer | tag only (a `version` field in `composer.json` is discouraged) | `2.0.0-beta2` | Composer stability flags: `dev`, `alpha`, `beta`, `RC`, `stable`. |
| Dart / Flutter | `pubspec.yaml` `version` | `2.0.0-beta.2+<build>` | `+N` is the store build number; it must rise on every store upload even when the version doesn't. |
| Helm | `Chart.yaml` `version` (chart) and `appVersion` (the app) | `2.0.0-beta.2` | Two numbers: bump `version` whenever the chart changes; `appVersion` follows the app. |
| Container images | image tag | `2.0.0-beta.2` | Also move floating tags (`2`, `2.0`, `latest`) only on GA. Never move `latest` to a pre-release. |
| iOS / Android | `CFBundleShortVersionString` + `CFBundleVersion`; `versionName` + `versionCode` | `2.0.0` + build `N` | Stores reject SemVer pre-release strings in the user-facing field; the stage lives in the track (TestFlight, beta channel), not the number. |
| Plain file | `VERSION` | `2.0.0-beta.2` | Whatever reads it decides the format. |

## Also check

- **Runtime-reported version**: a `/health` or `/version` endpoint, an about screen, a
  `--version` flag. If it reads the manifest at build time, nothing to do; if it's a
  hard-coded string, it's one more sync target.
- **Changelog**: Keep a Changelog style (`## [2.0.0-beta.2] - 2026-10-13`, then Breaking /
  Added / Fixed). Only the evidence from Step 3, not the commit list.
- **CalVer projects** (`YYYY.MM.N`, `YY.MINOR`): no bump levels. The next version is the
  date rule plus a counter; breaking changes are announced in the changelog instead.
