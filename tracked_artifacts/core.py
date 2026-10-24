"""Classify files from `git ls-files` (or a plain list) as artifacts. Read-only, offline."""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path

# (glob, category). Matched against the full path and against the basename.
RULES: list[tuple[str, str]] = [
    (".env", "secret-file"),
    (".env.*", "secret-file"),
    ("*.pem", "secret-file"),
    ("*.key", "secret-file"),
    ("id_rsa", "secret-file"),
    ("*.p12", "secret-file"),
    ("node_modules/*", "dependency-dir"),
    (".venv/*", "dependency-dir"),
    ("venv/*", "dependency-dir"),
    ("__pycache__/*", "build-output"),
    ("*.pyc", "build-output"),
    ("dist/*", "build-output"),
    ("build/*", "build-output"),
    ("*.egg-info/*", "build-output"),
    (".DS_Store", "os-junk"),
    ("Thumbs.db", "os-junk"),
    ("*.log", "log-file"),
    ("*.zip", "archive"),
    ("*.tar.gz", "archive"),
    ("*.exe", "binary"),
    ("*.dll", "binary"),
]
EXAMPLE_ENV_SUFFIXES = (".example", ".sample", ".template")
DEFAULT_LARGE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class Finding:
    path: str
    category: str
    size: int | None
    reason: str


def _matches(path: str, pattern: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    # fnmatch.fnmatch follows host OS case rules. Casefolded fnmatchcase keeps
    # scans and allow globs consistent across Windows and POSIX.
    normalized_pattern = pattern.casefold()
    return fnmatch.fnmatchcase(path.casefold(), normalized_pattern) or fnmatch.fnmatchcase(
        name.casefold(), normalized_pattern
    )


def classify(path: str, size: int | None = None, large_bytes: int = DEFAULT_LARGE_BYTES) -> Finding | None:
    name = path.rsplit("/", 1)[-1]
    if name.casefold().endswith(EXAMPLE_ENV_SUFFIXES):
        return None
    for pattern, category in RULES:
        if _matches(path, pattern):
            return Finding(path, category, size, f"matches {pattern}")
    if size is not None and size >= large_bytes:
        return Finding(path, "large-file", size, f"{size // (1024 * 1024)} MiB or more")
    return None


def tracked_files(root: str | Path) -> list[tuple[str, int | None]]:
    base = Path(root)
    out = subprocess.run(["git", "-C", str(base), "ls-files", "--stage", "-z"], capture_output=True, check=True)
    indexed: dict[str, tuple[bytes, bytes]] = {}
    for raw in out.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode, object_id, stage = metadata.split()
        path = raw_path.decode("utf-8", errors="replace")
        # Prefer stage 0 for resolved files. For an unmerged path, retain the
        # first index stage rather than duplicating the path in the report.
        if path not in indexed or stage == b"0":
            indexed[path] = (mode, object_id)

    paths = list(indexed)
    blob_ids = [indexed[path][1] for path in paths if indexed[path][0] != b"160000"]
    sizes: dict[bytes, int | None] = {}
    if blob_ids:
        size_out = subprocess.run(
            ["git", "-C", str(base), "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
            input=b"\n".join(blob_ids) + b"\n",
            capture_output=True,
            check=True,
        )
        for line in size_out.stdout.splitlines():
            object_id, object_type, raw_size = line.split()
            sizes[object_id] = int(raw_size) if object_type == b"blob" else None

    return [
        (path, None if indexed[path][0] == b"160000" else sizes.get(indexed[path][1]))
        for path in paths
    ]


def scan(
    files: list[tuple[str, int | None]],
    large_bytes: int = DEFAULT_LARGE_BYTES,
    allow: tuple[str, ...] = (),
) -> list[Finding]:
    """Return artifact findings, dropping any path matched by an --allow glob."""
    findings = [classify(path, size, large_bytes) for path, size in files]
    kept = [f for f in findings if f is not None]
    return [f for f in kept if not any(_matches(f.path, glob) for glob in allow)]
