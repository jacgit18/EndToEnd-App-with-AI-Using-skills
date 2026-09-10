# ADR 0011 — Python packaging / dependency management

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 9 (routine tier)

## Context

Python backend (ADR-0002). Need a reproducible dependency install for dev, CI, and the
container image. Solo maintainer.

## Decision

**`uv`.** One tool for the virtualenv, dependency resolution + install, the lockfile
(`uv.lock`), and the Python version. `pyproject.toml` holds `[project].dependencies` and a
`[dependency-groups] dev`; `uv sync` builds the environment; the Dockerfile runs `uv sync
--no-dev` (or `--frozen`) for the runtime image.

## Alternatives considered

- **Poetry** — mature and popular, but heavier and slower, with its own resolver and lockfile
  format. Lost on *speed* and *single-tool scope* (uv also manages the Python version).
- **pip + `requirements.txt` (+ `pip-tools`)** — closest to vanilla; lost on *workflow* (no
  single-tool venv+lock+install) and needs `pip-tools` bolted on for a real lockfile.

## Consequences

- Newer than Poetry, but well past "risky" and now a de facto modern default.
- Fast CI installs; a single tool for contributors to learn.
- Lockfile committed — reproducible builds across dev / CI / image.
- Reversible with low cost if `uv` ever regresses — the `pyproject.toml` is standard PEP 621
  and portable to Poetry or pip-tools.
