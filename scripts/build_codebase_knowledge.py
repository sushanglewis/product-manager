#!/usr/bin/env python3
"""Scan a codebase and emit a machine-readable feature map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_DIRS = ("src", "lib", "app", "packages", "server", "client")
IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".go", ".rs"}


def find_source_root(root: Path) -> Path | None:
    for candidate in DEFAULT_SOURCE_DIRS:
        path = root / candidate
        if path.is_dir():
            return path
    if any(
        p.suffix in SOURCE_EXTENSIONS for p in root.iterdir() if p.is_file()
    ):
        return root
    return None


def scan_features(root: Path, max_features: int = 10) -> dict[str, Any]:
    root = root.resolve()
    source_root = find_source_root(root)
    features: list[dict[str, Any]] = []

    if source_root:
        for child in sorted(source_root.iterdir()):
            if not child.is_dir() or child.name in IGNORE_DIRS:
                continue
            entry_points = sorted(
                p.relative_to(root)
                for p in child.rglob("*")
                if p.is_file() and p.suffix in SOURCE_EXTENSIONS
            )[:5]
            features.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(root)),
                    "entry_points": [str(ep) for ep in entry_points],
                    "has_tests": (root / "tests" / child.name).exists(),
                }
            )
            if len(features) >= max_features:
                break

    return {
        "root": str(root),
        "source_root": str(source_root) if source_root else None,
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a feature map from an existing codebase.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--max-features", type=int, default=10, help="Maximum features to emit")
    args = parser.parse_args()
    result = scan_features(Path(args.root), max_features=args.max_features)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
