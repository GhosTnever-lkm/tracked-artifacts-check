"""tracked-artifacts-check [PATH] [--large-mb N] [--json]"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .core import DEFAULT_LARGE_BYTES, scan, tracked_files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tracked-artifacts-check", description="Find artifacts, secrets files and large binaries tracked by git.")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--large-mb", type=float, default=DEFAULT_LARGE_BYTES / (1024 * 1024), help="size threshold in MiB (default 5)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    if not Path(args.path).is_dir():
        print(f"tracked-artifacts-check: not a directory: {args.path}", file=sys.stderr)
        return 2
    try:
        files = tracked_files(args.path)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"tracked-artifacts-check: cannot list git files in {args.path}: {exc}", file=sys.stderr)
        return 2
    findings = scan(files, large_bytes=int(args.large_mb * 1024 * 1024))
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False))
    elif not findings:
        print(f"OK: {len(files)} tracked files, no artifacts found")
    else:
        for f in findings:
            print(f"[ERROR] {f.category}: {f.path} ({f.reason})")
        print(f"{len(findings)} tracked artifact(s) found in {len(files)} files")
    return 1 if findings else 0
