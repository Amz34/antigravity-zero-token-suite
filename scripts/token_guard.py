#!/usr/bin/env python3
"""Local workspace token estimator and context-budget guardrail."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_EXTENSIONS = (".py", ".md", ".json", ".js", ".ts", ".html", ".css", ".yml", ".yaml", ".sh")
EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def estimate_file_metrics(filepath: str | Path, chars_per_token: int = 4) -> dict[str, int]:
    """Return line count, character count, and heuristic token count for a text file."""
    if chars_per_token < 1:
        raise ValueError("chars_per_token must be >= 1")
    path = Path(filepath)
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    char_count = len(content)
    est_tokens = char_count // chars_per_token
    return {
        "lines": len(lines),
        "chars": char_count,
        "est_tokens": est_tokens,
    }


def scan_workspace_tokens(
    root_dir: str | Path = ".",
    max_lines: int = 150,
    chars_per_token: int = 4,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
) -> dict[str, Any]:
    """Scan a workspace directory and identify files exceeding the line-count budget."""
    root = Path(root_dir).resolve()
    total_files = 0
    total_lines = 0
    total_est_tokens = 0
    heavy_files: list[dict[str, Any]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for filename in sorted(filenames):
            if not filename.endswith(extensions):
                continue
            filepath = Path(dirpath) / filename
            try:
                metrics = estimate_file_metrics(filepath, chars_per_token=chars_per_token)
            except OSError:
                continue

            total_files += 1
            total_lines += metrics["lines"]
            total_est_tokens += metrics["est_tokens"]

            if metrics["lines"] > max_lines:
                rel_path = os.path.relpath(filepath, root)
                heavy_files.append(
                    {
                        "path": rel_path,
                        "lines": metrics["lines"],
                        "chars": metrics["chars"],
                        "est_tokens": metrics["est_tokens"],
                    }
                )

    heavy_files.sort(key=lambda item: (-item["est_tokens"], item["path"]))
    return {
        "root": str(root),
        "max_lines": max_lines,
        "chars_per_token": chars_per_token,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_est_tokens": total_est_tokens,
        "heavy_files": heavy_files,
    }


def format_report(summary: dict[str, Any]) -> str:
    """Format a human-readable guardrail report."""
    lines = [
        "=== Antigravity Zero-Token Workspace Scanner ===",
        f"Scanned Root:              {summary['root']}",
        f"Total Eligible Files:      {summary['total_files']}",
        f"Total Lines of Code/Text:  {summary['total_lines']}",
        f"Estimated Full-Read Cost:  ~{summary['total_est_tokens']} tokens",
        "",
    ]
    heavy = summary["heavy_files"]
    if heavy:
        lines.append(
            f"[ALERT] Files exceeding {summary['max_lines']} lines (use targeted line ranges instead of full reads):"
        )
        for item in heavy:
            lines.append(
                f"  - {item['path']}: {item['lines']} lines (~{item['est_tokens']} tokens)"
            )
    else:
        lines.append(
            f"[OK] All scanned files are within the {summary['max_lines']}-line single-read budget."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan a workspace and flag files that exceed single-turn LLM context budgets."
    )
    parser.add_argument("root", nargs="?", default=".", help="Workspace root directory (default: .)")
    parser.add_argument(
        "--max-lines",
        type=int,
        default=150,
        help="Maximum line count allowed for an un-sliced file read (default: 150)",
    )
    parser.add_argument(
        "--chars-per-token",
        type=int,
        default=4,
        help="Character-to-token heuristic divisor (default: 4)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary on stdout",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when one or more files exceed --max-lines",
    )
    args = parser.parse_args(argv)

    summary = scan_workspace_tokens(
        root_dir=args.root,
        max_lines=args.max_lines,
        chars_per_token=args.chars_per_token,
    )
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(format_report(summary))

    if args.strict and summary["heavy_files"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
