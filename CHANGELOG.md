# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.2] - 2026-10-12

### Added

- `--allow GLOB` (repeatable) to ignore findings for intentionally committed fixtures.
- Document installation from the versioned v0.1.2 source.
- Publish wheel and source distributions with SHA-256 checksums from the release workflow.
- Verify the release tag matches package metadata before publication.

### Fixed

- Reject zero, negative, and non-finite `--large-mb` values with a concise CLI error instead of scanning every file or raising an uncaught exception.

## [0.1.1] - 2026-10-11

### Added

- CI now also runs the test suite on Windows (windows-latest), not only Ubuntu.


## [0.1.0] - 2026-10-11

### Added

- Detect tracked secret files (`.env`, keys), dependency and build directories, OS junk, logs, archives and binaries.
- Flag files above a configurable size threshold (`--large-mb`, default 5 MiB).
- `.env.example`-style templates are allowed; `--json` output; exit code 2 when git is unavailable.

[Unreleased]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/releases/tag/v0.1.2
[0.1.0]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/releases/tag/v0.1.0
