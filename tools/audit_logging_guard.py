#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit logging and exception-handling fallback patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


Pattern = tuple[str, re.Pattern[str], str]


PATTERNS: list[Pattern] = [
    (
        "traceback_print_exc",
        re.compile(r"traceback\.print_exc\s*\("),
        "traceback.print_exc() found; prefer logger.exception(...)",
    ),
    (
        "bare_except_pass",
        re.compile(r"except\s*:\s*\n\s*pass\b", re.MULTILINE),
        "except: pass found; do not silently swallow errors",
    ),
    (
        "except_exception_pass",
        re.compile(r"except\s+Exception\s*:\s*\n\s*pass\b", re.MULTILINE),
        "except Exception: pass found; at least log a warning",
    ),
    (
        "logger_fstring",
        re.compile(
            r"(?:^|[^A-Za-z0-9_])(?:logger|self\.logger)\."
            r"(?:debug|info|warning|error|exception|critical)\s*\(\s*f[\"']"
        ),
        "logger f-string found; prefer parameterized logging placeholders",
    ),
]


DEFAULT_EXCLUDES = {
    ".git",
    ".history",
    "__pycache__",
    ".cursor",
    ".trae",
    ".venv",
    "venv",
    "mcps",
    "dist",
    "build",
    "tools_legacy",
}


def iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in DEFAULT_EXCLUDES for part in path.parts):
            continue
        yield path


def line_no_from_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _is_i18n_t_fallback(content: str, offset: int) -> bool:
    """Allow the intentionally silent translation fallback in _t()."""
    window_start = max(0, offset - 400)
    context = content[window_start:offset]
    return (
        "def _t(" in context
        and "tr_fn = getattr" in context
        and "return tr_fn(" in context
    )


def scan_file(path: Path) -> list[tuple[str, int, str]]:
    issues: list[tuple[str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")

    for name, pattern, message in PATTERNS:
        for match in pattern.finditer(text):
            if name in {"bare_except_pass", "except_exception_pass"} and _is_i18n_t_fallback(
                text, match.start()
            ):
                continue
            line_no = line_no_from_offset(text, match.start())
            issues.append((message, line_no, match.group(0).strip()))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit logging and exception fallback patterns")
    parser.add_argument(
        "--root",
        default="FrameCore",
        help="scan root (default: FrameCore)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[audit] root does not exist: {root}")
        return 2

    all_issues: list[tuple[Path, str, int, str]] = []
    for py_file in iter_py_files(root):
        for msg, line_no, snippet in scan_file(py_file):
            all_issues.append((py_file, msg, line_no, snippet))

    if not all_issues:
        print("[audit] OK: no logging/exception fallback patterns found")
        return 0

    print(f"[audit] found {len(all_issues)} issue(s)")
    cwd = Path.cwd()
    for file_path, msg, line_no, snippet in all_issues:
        rel = file_path.relative_to(cwd) if file_path.is_relative_to(cwd) else file_path
        print(f"- {rel}:{line_no} | {msg}")
        print(f"  -> {snippet}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
