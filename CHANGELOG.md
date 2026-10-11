# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `--allow GLOB` (repeatable) to ignore findings for intentionally committed fixtures.

## [0.1.0] - 2026-10-11

### Added

- Detect tracked secret files (`.env`, keys), dependency and build directories, OS junk, logs, archives and binaries.
- Flag files above a configurable size threshold (`--large-mb`, default 5 MiB).
- `.env.example`-style templates are allowed; `--json` output; exit code 2 when git is unavailable.

[Unreleased]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/releases/tag/v0.1.0
