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
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(name, pattern)


def classify(path: str, size: int | None = None, large_bytes: int = DEFAULT_LARGE_BYTES) -> Finding | None:
    name = path.rsplit("/", 1)[-1]
    if name.endswith(EXAMPLE_ENV_SUFFIXES):
        return None
    for pattern, category in RULES:
        if _matches(path, pattern):
            return Finding(path, category, size, f"matches {pattern}")
    if size is not None and size >= large_bytes:
        return Finding(path, "large-file", size, f"{size // (1024 * 1024)} MiB or more")
    return None


def tracked_files(root: str | Path) -> list[tuple[str, int | None]]:
    base = Path(root)
    out = subprocess.run(["git", "-C", str(base), "ls-files", "-z"], capture_output=True, check=True)
    result = []
    for raw in out.stdout.decode("utf-8", errors="replace").split("\0"):
        if not raw:
            continue
        file = base / raw
        size = file.stat().st_size if file.is_file() else None
        result.append((raw, size))
    return result


def scan(files: list[tuple[str, int | None]], large_bytes: int = DEFAULT_LARGE_BYTES) -> list[Finding]:
    findings = [classify(path, size, large_bytes) for path, size in files]
    return [f for f in findings if f is not None]
