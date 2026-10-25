# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.5] - 2026-10-25

### Fixed

- Detect common OpenSSH private-key filenames, including Ed25519, ECDSA, DSA, and security-key variants, without flagging public `.pub` files.

## [0.1.4] - 2026-10-25

### Fixed

- Measure tracked files from Git index blobs so staged content is checked even when the working copy has changed.

## [0.1.3] - 2026-10-25

### Fixed
- Make rule and allow-glob matching case-insensitive and consistent across operating systems.
- Reject size thresholds that overflow when converted to bytes, and round positive sub-byte thresholds up to one byte.

### Added
- Regression tests for portable matching and numeric boundaries.

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

[Unreleased]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/releases/tag/v0.1.2
[0.1.0]: https://github.com/GhosTnever-lkm/tracked-artifacts-check/releases/tag/v0.1.0
